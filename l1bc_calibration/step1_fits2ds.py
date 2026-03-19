#%%
import argparse
from dataclasses import dataclass
import re
from turtle import pos

from astropy import conf
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
from astropy.io import fits as fits
from pathlib import Path
#%% FUNCTIONS
def convert_fits2ds_exp_y_x(filelist:list[str]|list[Path], slitsize:float,sourcename:str, attrsnote:str= '') -> xr.Dataset:
    """Converts raw Fits files into xr.Dataset with shape (exp,y,x)
    Args:
        filelist (list[str] | list[Path]): File paths to raw fits files
        slitsize (float): Size of the slit in micrometers, to be added as an attribute to the Dataset.
        sourcename (str): Name of the source used for calibration.
        attrsnote (str, optional): Note to add as an attribute to the Dataset. Defaults to ''.

    Returns:
        xr.Dataset: Dataset with shape (exp,y,x)
    """
    if isinstance(filelist[0], str):filelist = [Path(f) for f in filelist]
    exps = np.sort(np.unique([get_exp_from_fn_ASIIMG(f) for f in filelist]))
    exposures = [] # in seconds for ds
    imgs = []
    for e in exps:
        fns = [f for f in filelist if f'_{e}s' in str(f.stem)] #get files with exposure e, #type: ignore
        if len(fns)>0:
            im = []
            for fidx,f in enumerate(fns):
                with fits.open(f) as hdul:
                    hidx = int(len(hdul)-1)
                    data = hdul[hidx].data #type: ignore
                    if fidx==0:
                        exposures.append(hdul[hidx].header['EXPOSURE']) #type: ignore
                    im.append(data)
            imgs.append(np.nanmean(np.array(im), axis=0)) #average all images for same exposure
    
    ds = xr.Dataset(
        data_vars={
            'counts': (('exp','y','x'), np.array(imgs),
                        {'units':'ADU','description':'Image counts'}),
        },    coords={ 
            'exp': (('exp',), np.array(exposures), {'units':'s','description':'Exposure time for images'}),
            'y': (('y',), np.arange(np.shape(imgs)[1]), {'units':'pixels','description':'y pixel index'}), #type: ignore
            'x': (('x',), np.arange(np.shape(imgs)[2]), {'units':'pixels','description':'x pixel index'}), #type: ignore
        },    attrs={
            'description':'HiT&MIS claibration images taken with various exposure times',
            'source': sourcename,
            'slit_size_um': f'{slitsize:.2f}',
            'date_created': np.datetime_as_string(np.datetime64('now'), unit='s', timezone='UTC'),
            'Note': attrsnote}
        ) # type: ignore
    return ds

def fit_linear_counts_vs_exp(ds: xr.Dataset) -> xr.Dataset:
    """Fits a 1st order polynomial to Counts vs Exposure (y = mx + b)
       Where m = countrate (ADU/s) 
             b = bias (ADU)

    Args:
        ds (xr.Dataset): Dataset with 'counts' variable and 'exp' coordinate. 'counts' variable can have any number of additional dimensions (e.g. pos,y,x, etc). 'exp' must be one of the dimensions of 'counts'.

    Returns:
        xr.Dataset: Input Dataset with added variables:
            - countrate (ADU/s): slope of linear fit to counts vs exp for each pixel
            - countrate_err (ADU/s): standard error in countrate from fit
            - bias (ADU): intercept of linear fit to counts vs exp for each pixel
            - bias_err (ADU): standard error in bias from fit  
    """  
    weight = np.full_like(ds.exp.data, 6) # read noise of 6 counts for full exposure  
    fit = ds.counts.polyfit(dim= 'exp', deg = 1, skipna= True, w = 1/weight, cov =True)
    fit.polyfit_coefficients.data = fit.polyfit_coefficients.clip(min=0)
    # assign to ds
    ds = ds.assign(countrate = fit.polyfit_coefficients.sel(degree = 1))
    ds.countrate.attrs['units'] = 'ADU/s'
    ds.countrate.attrs['description'] = 'Count rate per pixel from linear fit to counts vs exposure time for each pixel'
    ds = ds.assign(countrate_err =np.sqrt(fit.polyfit_covariance.sel(cov_i=0, cov_j=0)))
    ds.countrate_err.attrs['units'] = 'ADU/s'
    ds.countrate_err.attrs['description'] = 'Standard Error in count rate per pixel from linear fit to counts vs exposure time for each pixel'
    ds = ds.assign(bias = fit.polyfit_coefficients.sel(degree = 0))
    ds.bias.attrs['units'] = 'ADU'
    ds.bias.attrs['description'] = 'Bias (intercept) per pixel from linear fit to counts vs exposure time for each pixel'
    ds = ds.assign(bias_err = np.sqrt(fit.polyfit_covariance.sel(cov_i=1, cov_j=1)))
    ds.bias_err.attrs['units'] = 'ADU'
    ds.bias_err.attrs['description'] = 'Standard Error in bias (intercept) per pixel from linear fit to counts vs exposure time for each pixel'
    ds = ds.drop_vars(['degree'])
    return ds

def get_exp_from_fn_comic(fn:str|Path)->str: #the file naming convention from COMIC software
    if isinstance(fn, str):
        fn = Path(fn)
    return fn.stem.split('_')[-2].strip('s')

def get_exp_from_fn_ASIIMG(fn:str|Path)->str: # The file naming convention for ASIIMG software
    if isinstance(fn, str):
        fn = Path(fn)
    return fn.stem.split('_')[2].strip('sec')
#%% 
@dataclass
class Fits2DsConfig:
    rootdir: str|Path #path to raw data directory containing all calibration subdirs
    destdir: str|Path #path to save processed datasets
    slitsize: float
    sourcename: str 
    overwrite: bool = False
    pos_identifier: str = 'pos'
    attrsnote: str = ''

def main(config : Fits2DsConfig):
    """
    Process FITS files into xarray Datasets and save as NetCDF files.
    This function orchestrates the conversion of FITS image files into xarray Datasets,
    applies linear fitting to exposure vs. counts data, and saves the processed data
    as NetCDF files. It handles dark frames, flat frames, background frames, and 
    calibration lamp position data.
    Parameters
    ----------
    config : Fits2DsConfig
        Configuration object containing:
        - rootdir (str or Path): Root directory containing subdirectories with FITS files
        - destdir (str or Path): Destination directory for output NetCDF files
        - overwrite (bool): Whether to overwrite existing NetCDF files
        - slitsize (float): Slit size in micrometers
        - sourcename (str): Name of the light source
        - attrsnote (str): Additional notes for dataset attributes
        - pos_identifier (str): String identifier for lamp position directories
    Returns
    -------
    None
        Results are saved as NetCDF files to the destination directory.
    Notes
    -----
    - Dark and flat frames are processed with linear fitting and saved to NetCDF
    - Background frames are processed with linear fitting but used only for background
      subtraction of lamp images
    - Lamp position data is concatenated across positions and saved with position
      as a dimension
    - Background subtraction is applied to lamp datasets if background data exists
    - Output files follow naming convention: {rootdir_stem}_{id}_l0.nc or
      {rootdir_stem}_slit_{slit_id}_l0.nc
    """


    if isinstance(config.rootdir, str):
        config.rootdir = Path(config.rootdir).expanduser()


    if isinstance(config.destdir, str):
        config.destdir = Path(config.destdir).expanduser()

    DIRNAME = 'l0'
    if  config.destdir.stem != DIRNAME:
        config.destdir = config.destdir.joinpath(DIRNAME)
    config.destdir.mkdir(parents=True, exist_ok=True)

    SKIP, LINFIT, SAVEDS = False, False, False
    lampdirs = []
    bgds = None
    dirs = list(config.rootdir.iterdir())
    
    # PROCESS DARK, FLAT, AND BACKGROUND FRAMES
    # first to create datasets and get background dataset for later background subtraction of lamp images
    for d in dirs:
        id = d.stem
        spath = config.destdir.joinpath(f'{config.rootdir.stem}_{id}_l0.nc')
        #save path
        if spath.exists() and not config.overwrite:
            print(f"{id} dataset already exists at {spath}, skipping processing...")
            continue
        elif spath.exists() and config.overwrite:
            print(f"deleting {spath} to overwrite...")
            spath.unlink() #delete existing file to be overwritten
            pass

        if 'dark' in id.lower():
            #fits -> ds, save to netcdf
            attrsnote= f'{id} dark frames taken at various exposure times'
            LINFIT = True
            SAVEDS = True
        if 'flat' in id.lower():
            #fits -> ds, linear fit, save to netcdf
            attrsnote = f'The {id} are to be used for creating calibration maps for HiT&MIS images.'
            LINFIT = True
            SAVEDS = True
        if 'background' in id.lower():
            #fits -> ds, linear fit, save to netcdf
            attrsnote = f'The {id} is to be used only ask a dark+background correction for the calibration lamp images'
            LINFIT = True
            SAVEDS = False
        if config.pos_identifier in id.lower():
            #fits -> ds, linear fit, save to netcdf
            lampdirs.append(d)
        if SAVEDS and spath.exists() and not config.overwrite:
            print(f"{id} dataset already exists at {spath}, skipping processing...")
            SKIP = True
    
        if not SKIP:
            if 'dark' in id.lower() or 'flat' in id.lower() or 'background' in id.lower():
                print(f'Processing {id} data...') #fits -> ds
                all_fns = list(d.glob('*.fit*')) #try getting files in current dir
                if len(all_fns)>0: # found files in current dir
                    pass #go onto the next step
                else: 
                    all_fns = list(d.glob('*/*.fit*')) #try getting files in subdirs
                if len(all_fns)<1: #if no files found in dir and subdirs, skip this id
                    print(f'No fits files found in {d}, skipping...')
                    SKIP = True
            
                if not SKIP:
                    ds = convert_fits2ds_exp_y_x(all_fns, slitsize=config.slitsize, sourcename=config.sourcename, attrsnote= config.attrsnote)
                    if LINFIT:
                        ds = fit_linear_counts_vs_exp(ds)
                    if SAVEDS:
                        encoding = {var: {'zlib': True} for var in (*ds.data_vars.keys(), *ds.coords.keys())}
                        spath = config.destdir.joinpath(f'{config.rootdir.stem}_{id}_l0.nc')#save path
                        ds.to_netcdf(spath, encoding= encoding)
                        print(f"{id} dataset saved to netcdf with shape: {dict(ds.sizes)}")
                    else:
                        bgds = ds
                    del ds
            else: ''
    # PROCESS LAMP POSITION DATA 
    if len(lampdirs)>0:
        LINFIT = True
        SAVEDS = True
        SKIP = False
        print(f'Processing lamp position data...') #fits-> ds, linear fit, save to netcdf
        slits = np.sort(np.unique([d.stem.split('_')[-2] for d in lampdirs]))
        
        for s in slits:
            dslist = []
            pos = []
            pdirs = list(config.rootdir.glob(f'*{s}_*'))
            for pd in pdirs:
                id = pd.stem
                pos.append(id.split('_')[-1].strip('in'))
                all_fns = list(pd.glob('*.fit*')) #try getting files in current dir
                if len(all_fns)>0: # found files in current dir
                    pass #go onto the next step
                else: 
                    all_fns = list(pd.glob('*/*.fit*')) #try getting files in subdirs
            
                if len(all_fns)<1: #if no files found in dir and subdirs, skip this id
                    print(f'No fits files found in {pd}, skipping...')
                    SKIP = True
                bgsub_note = ''
                if not SKIP:
                    ds = convert_fits2ds_exp_y_x(all_fns, slitsize=config.slitsize, sourcename=config.sourcename, attrsnote= config.attrsnote)
                    if bgds is not None:
                        ds = ds - bgds
                        bgsub_note = ' Background subtracted before linear fitting.'
                    else: 
                        bgsub_note = 'No background corrections applied.'
                    dslist.append(ds)
                
                if len(dslist)>0:
                    fullds = xr.concat(dslist, dim= xr.DataArray(np.array(pos, dtype= float), dims= 'pos', 
                    attrs={'units':'inches','description':'distance between foreoptic and lamp'}))
                    fullds.attrs['description'] = f'Calibration lamp images taken at various exposures times using Hit&MIS.'
                    fullds.attrs['slit_size_um'] = f'{config.slitsize:.2f}'
                    fullds.attrs['date_created'] = np.datetime_as_string(np.datetime64('now'), unit='s',timezone='UTC')
                    fullds.attrs['source'] = config.sourcename
                    fullds.counts.attrs['units'] = 'ADU'
                    fullds.counts.attrs['description'] = 'Image counts'
                    fullds.attrs['Note'] = bgsub_note
                    print(f"Lamp dataset with {s} slit created with shape: {dict(fullds.sizes)}")
                    if LINFIT:
                        fullds = fit_linear_counts_vs_exp(fullds)
                    if SAVEDS:
                        encoding = {var: {'zlib': True} for var in (*fullds.data_vars.keys(), *fullds.coords.keys())}
                        spath = config.destdir.joinpath(f'{config.rootdir.stem}_{config.pos_identifier}_slit_{s}_l0.nc')#save path
                        fullds.to_netcdf(spath, encoding= encoding)
                        print(f"{id} dataset saved to netcdf with shape: {dict(fullds.sizes)}")
                    del fullds
    else: print('No lamp position directories found, skipping lamp data processing.')


        
#%%\


if __name__ == '__main__':
    # rootdir  = Path('~/locsststor/raw/hmsao-v1_calibration_slit_100um_20251023').expanduser()
    # destdir = Path('~/locsststor/proc/hmsao-v1_calibration_slit_100um_20251023/l0').expanduser()
    # slitsize = 100
    # sourcename = 'Gamma Scientific RS-12D Series Calibration Light Source'
    # OVERWRITE = False
    # pos_identifier = f'pos'

    parser = argparse.ArgumentParser(description='Process raw fits files into xarray Datasets and save as netcdf for HiT&MIS calibration data.')
    parser.add_argument('--rootdir',
                        type=str, 
                        required=True, 
                        help='Path to raw data directory containing all calibration subdirs')
    parser.add_argument('--destdir',
                         type=str, 
                         required=True, 
                         help='Path to save processed datasets')
    parser.add_argument('--slitsize',
                         type=float, 
                         required=True, 
                         help='Size of the slit in micrometers, to be added as an attribute to the Dataset')
    parser.add_argument('--sourcename',
                         type=str, 
                         required=True, 
                         help='Name of the calibration light source')
    parser.add_argument('--overwrite',
                         type =bool,
                         default=False,
                         help='Whether to overwrite existing datasets at the destination path. Default is False.')
    parser.add_argument('--pos_identifier',
                         type=str,
                         default='pos',
                         help='String identifier to look for in directory names to identify lamp position data. Default is "pos".')
    args = parser.parse_args()
 
    config = Fits2DsConfig(
        rootdir= args.rootdir, 
        destdir= args.destdir, 
        slitsize= args.slitsize, 
        sourcename= args.sourcename,
          overwrite= args.overwrite, 
          pos_identifier= args.pos_identifier)
    
    main(config=config)