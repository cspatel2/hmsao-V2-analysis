#%%
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pathlib import Path
# %%
def open_flatfield(fn, version:str|None = None, plot = False):
    ds = xr.open_dataset(fn)
    da = ds.countrate.sel(za = slice(-20,15))
    med = da.median(skipna=True)
    da = da/med
    if version is None:
        version = ''
    if plot:
        da.plot()
        plt.title(f"Normalized flatfield - {version}")
    return da

def find_flatfield_fns(path,win, version):
    p = Path(path).expanduser()
    fns = list(p.glob(f'**{version}*calib*/l1a/*flat*{win}*.nc'))
    fns.sort()
    return fns

def get_datafiles(path, win, version):
    p = Path(path).expanduser()
    fns = list(p.glob(f'*{version}/l1a/*/*{win}*.nc'))
    fns.sort()
    return fns


def apply_flatfield(da, flatda,version, plot:bool = False):
    if isinstance(da, xr.Dataset):
        da = da.countrate
    if isinstance(flatda, xr.Dataset):
        flatda = flatda.countrate
    
    da_flat = da/flatda
    if plot:
        tidx = 0
        fig,axs = plt.subplots(2,3, figsize = (15,10), )
        plt.subplots_adjust(wspace=.3, hspace=.2)
        plot_da =  da.isel(tstamp = tidx)
        vmin = np.nanpercentile(plot_da.values, 1)
        vmax = np.nanpercentile(plot_da.values, 99)
        plot_da.plot(ax = axs[0,0], vmin=vmin, vmax=vmax)
        axs[0,0].set_title("Data")

        vmin = np.nanpercentile(flatda.values, 1)
        vmax = np.nanpercentile(flatda.values, 99)
        flatda.plot(ax = axs[0,1], vmin=vmin, vmax=vmax)
        axs[0,1].set_title("Normalized Flatfield")

        plot_flat_da = da_flat.isel(tstamp = tidx)
        vmin = np.nanpercentile(plot_flat_da.values, 1)
        vmax = np.nanpercentile(plot_flat_da.values, 99)
        plot_flat_da.plot(ax = axs[0,2], vmin=vmin, vmax=vmax)
        axs[0,2].set_title("Data after flatfield correction")

        zaidx = 500
        wlidx = 300
        plot_flat_da.isel(za = zaidx).plot(ax = axs[1,0], x = 'wavelength')
        da.isel(tstamp = tidx, za = zaidx).plot(ax = axs[1,0], x = 'wavelength')
        plot_flat_da.isel(wavelength = wlidx).plot(ax = axs[1,1], y='za')
        da.isel(tstamp = tidx, wavelength = wlidx).plot(ax = axs[1,1], y='za')

        fig.suptitle(f"Flatfield correction - {version}")

    return da_flat
#%%

win = '5577'
version = 'v2'
p = Path("~/local_data").expanduser()
fns = find_flatfield_fns(p, win, version)
flat = open_flatfield(fns[-1], version, plot = False)
fns_data = get_datafiles(p, win, version)
ods  = xr.open_dataset(fns_data[2])
#%%
fixedda = apply_flatfield(ods, flat, version, plot = True)
# %%

version = 'v1'
p = Path("~/locsststor/proc").expanduser()
fns = find_flatfield_fns(p, win, version)
flat = open_flatfield(fns[-1], version, plot = True)


# %%
def find_raw_flatfield_fns(path,win, version):
    p = Path(path).expanduser()
    fns = list(p.glob(f'*{version}*calib*/l0/*flat*.nc'))
    fns.sort()
    return fns
# %%
win = '5577'
version = 'v2'
p = Path("~/local_data").expanduser()
fns = find_raw_flatfield_fns(p, win, version)
print(len(fns))
# %%
rds = xr.open_dataset(fns[-1])
rds = rds.sortby('exp')
# %%
rds.counts.isel(exp= 5).plot()
# %%
