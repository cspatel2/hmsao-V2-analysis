#%%
import matplotlib.pyplot as plt
import numpy as np
from wcwidth import width
import xarray as xr
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
from datetime import datetime, timezone
#%%

def get_datafiles(path, win, version,date=''):
    p = Path(path).expanduser()
    fns = list(p.glob(f'*{version}/l1b/*/*{date}*{win}*.nc'))
    fns.sort()
    return fns

def load_ref_spectra( kind,path:str| Path ="~/locsststor/proc/ref_spectra" ):
    if kind not in ['solar', 'night']:
        raise ValueError(f"kind must be either 'solar' or 'night', got {kind}")
    if isinstance(path, str):
        path = Path(path).expanduser()
    fns = list(path.glob(f'*{kind}*.nc')) 
    ds = xr.open_dataset(fns[0])
    return ds

def Normalize(da, dim=None,sigma=0, invert_signal=False):
    """
    Normalize the data array `da` along the specified dimension `dim`.
    If `dim` is None, normalize the entire array globally.
    If `invert_signal` is True, invert the normalized signal (1 - normalized value).
    """
    if dim is None:
        # normalize the entire array globally
        vmin = np.nanmin(da.values) 
        vmax = np.nanmax(da.values)
        da = da - vmin
        da = da / (vmax - vmin)
        if sigma > 0:
            da.values = gaussian_filter1d(da.values, sigma=sigma)
    else:
        # normalize each slice along `dim` independently
        vmin = da.min(dim=dim, skipna=True)
        vmax = da.max(dim=dim, skipna=True)
        da = da - vmin
        da = da / (vmax - vmin)
        if sigma > 0:
            da = gaussian_filter1d(da, sigma=sigma, axis=da.get_axis_num(dim))
    if invert_signal:
        da = 1 - da
    return da

def load_data_set(path):
    ds = xr.open_dataset(path)
    ds = ds.assign_coords({'time':('tstamp',[datetime.fromtimestamp(t, tz=timezone.utc) for t in ds['tstamp'].values])})
    if 'param' in list(ds.variables):
        print('param found')
        ds = ds.drop_vars('param')
    return ds
#%%

win = '7774'
version = 'v2'
date = '20251116'
p = Path("~/local_data")
fns = get_datafiles(p, win, version, date)    
print(len(fns))
# %%
ds = load_data_set(fns[-1])
ds
#%%
da = ds.countrate.sum('za')
vmin = np.nanpercentile(da.values, 1)
vmax = np.nanpercentile(da.values, 99)
#%%
da.plot(vmin=vmin, vmax=vmax)
#%%
# tidx = 0
tidx = datetime(2025, 11, 16, 22,57, 0, tzinfo=timezone.utc)
if isinstance(tidx, int):
    ids = ds.countrate.isel(tstamp = tidx)
elif isinstance(tidx, datetime):
    ids = ds.countrate.sel(time = tidx, method='nearest')
else:
    raise ValueError(f"tidx must be either an integer or a datetime object, got {type(tidx)}")
vmin = np.nanpercentile(ids.values, 1)
vmax = np.nanpercentile(ids.values, 99)
ids.plot(y = 'za', vmin=vmin, vmax=vmax)
plt.title(f'{ids.time.values}')
# %%
zaslice = slice(-4,0)
line = ids.sel(za=zaslice)
line.plot()
#%%
l = line.copy()
l = l.sum('za')
l = Normalize(l, invert_signal=False, sigma=2)
#%%
plt.figure(figsize=(12, 4)) 
l.plot()

# %%
