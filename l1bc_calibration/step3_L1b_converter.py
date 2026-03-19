# perform secondary straightening on a l1a dataset based on a provided line profile
# NOTE: THIS IS A COPY OF THE SECONDARY_STRAIGHTENING SCRIPT, IN L1B CONVERTER . CAN USE THAT SCRIPT DIRECTLY INSTEAD.
#%%
import argparse
from dataclasses import dataclass
from datetime import datetime
from logging import config
import os
import sys
from astropy import conf
import numpy as np
from pyparsing import line
import xarray as xr
from skimage import transform
from pathlib import Path

from matplotlib import pyplot as plt
from tqdm import tqdm

LOCALPATH = os.path.dirname(os.path.realpath(__file__)).replace('l1bc_calibration', 'l1b_converter')

if LOCALPATH not in sys.path:
    sys.path.append(LOCALPATH)

from secondary_straightening import secondary_straightening
# %%

# %%

@dataclass
class CalibL1BConfig:
    """ Configuration for L1B conversion.
    Arguments:
        rootdir (str|Path): Root directory containing L1A files.
        destdir (str|Path): Destination directory for L1B files. If not provided, will create a 'l1b' directory parallel to the rootdir.
        windows (list[str]): List of windows to process. If not provided, will process all windows found in the line profile directory.
        lineprofile_dir (str|Path): Directory containing line_profile_*.nc files for secondary straightening calibration.
    """
    
    rootdir: str|Path
    destdir: str|Path
    windows: list[str]
    lineprofile_dir: str|Path
     

def main(config : CalibL1BConfig):
    """
    Process L1a data files to generate L1b secondary-straightened output files.
    This function performs the following operations:
        1. Validates configured spectral windows against available line profile data
        2. Prepares and validates destination directory for output files
        3. For each valid window, iterates through corresponding L1a input files
        4. Applies secondary straightening calibration using line profile data
        5. Harmonizes variable attributes and adds processing metadata
        6. Saves calibrated data to compressed NetCDF format in the L1b directory
    Args:
        config (CalibL1BConfig): Configuration object containing:
            - rootdir (str|Path): Root directory containing L1A files.
            - destdir (str|Path): Destination directory for L1B files. If not provided, will create a 'l1b' directory parallel to the rootdir.
            - windows (list[str]): List of windows to process. If not provided, will process all windows found in the line profile directory.
            - lineprofile_dir (str|Path): Directory containing line_profile_*.nc files for secondary straightening calibration.
    Returns:
        None
    Raises:
        FileNotFoundError: If line profile files or input data files not found
        KeyError: If required data variables not found in input datasets
    Notes:
        - Automatically creates destination directory if it doesn't exist
        - Handles both 'countrate' and 'intensity' data variables
        - Clips negative countrate values to zero
        - Adds processing metadata and preserves original variable attributes
    """

    #check for valid windows
    config.lineprofile_dir = Path(config.lineprofile_dir).expanduser()
    available_windows = [fn.stem.split('_')[-1] for fn in config.lineprofile_dir.glob('*profile_*.nc')]
    if config.windows == ['']:
        valid_windows = available_windows
    else:
        valid_windows = [w for w in config.windows if w in available_windows]
    
    print(f"Valid windows for processing: {valid_windows}")

    config.rootdir = Path(config.rootdir).expanduser()
    config.destdir = Path(config.destdir).expanduser()

    #check destination directory
    if config.destdir == Path('') or config.destdir.stem != 'l1b':
        config.destdir = Path(str(config.rootdir).replace('l1a','l1b'))
    config.destdir.mkdir(exist_ok=True)
    print(f"Destination directory: {config.destdir}")

    for win in valid_windows:
        print(f"Processing window: {win}")
        line_profile_path = config.lineprofile_dir.joinpath(f'line_profile_{win}.nc')

        fns = list(config.rootdir.glob(f'**/*{win}*.nc'))
        print(f"Found {len(fns)} files to process.")
        fns.sort()
    
        lprof = xr.open_dataset(line_profile_path)

        ds = xr.open_dataset(fns[0])
        id = None
        if 'countrate' in list(ds.data_vars): id = 'countrate'
        elif 'intensity' in list(ds.data_vars): id = 'intensity'
        else: print("no known data variable found")

        for fn in fns:
            print(f"Processing file: {fn.name}...")
            ds = xr.open_dataset(fn)
            if id == 'intensity':
                ds = ds.rename({'intensity':'countrate'})
            ss = secondary_straightening(ds, lprof)
            ss['countrate'] = ss['countrate'].clip(min=0) 
            all_vars = list(ds.coords) + list(ds.keys())
            for var in all_vars:
                ss[var].attrs = ds[var].attrs    
            ss.attrs['DataProcessingLevel'] = 'L1b - Secondary Straightened'
            ss.attrs['FileCreationDate'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S EDT")
            encoding = {var: {'zlib': True}for var in (*ds.data_vars.keys(), *ds.coords.keys())}
            print('...saving...')
            outfn = config.destdir.joinpath(fn.stem.replace('l1a','l1b') + fn.suffix)
            ss.to_netcdf(outfn, encoding=encoding)
            print('...Done.')
    #
#%%
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert L1A files to L1B by applying secondary straightening calibration.')
    parser.add_argument('--rootdir', type=str, required=True, help='Root directory containing L1A files to process.')
    parser.add_argument('--destdir', type=str, default='', help='Destination directory for L1B output files. If empty, will replace "l1a" with "l1b" in the rootdir path.')
    parser.add_argument('--windows', type=str, required=True, help='list of windows to process')
    parser.add_argument('--lineprofile_dir', type=str, required=True, help='Directory containing line_profile_*.nc files for secondary straightening calibration.')

    args = parser.parse_args()
    config = CalibL1BConfig(
        rootdir=args.rootdir,
        destdir=args.destdir,
        windows=args.windows.split(','),
        lineprofile_dir=args.lineprofile_dir
    )
    main(config)
    