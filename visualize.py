#%%
import matplotlib.pyplot as plt
from numpy import dsplit
import xarray as xr
from pathlib import Path
from datetime import datetime, timezone
import matplotlib as mpl
import numpy as np
usetex = False

if not usetex:
    # computer modern math text
    mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc('font', **{'family': 'serif',
       'serif': ['Times' if usetex else 'Times New Roman']})
# for Palatino and other serif fonts use:
# rc('font',**{'family':'serif','serif':['Palatino']})
mpl.rc('text', usetex=usetex)
mpl.rc('xtick', labelsize=10) 
mpl.rc('ytick', labelsize=10) 

# %%
path = Path('~/locsststor/proc/hmsao-v2/l2')
win = '5577'
fns = list(path.expanduser().glob(f'*/*{win}*.nc'))
fns.sort()
print(f'# of files: {len(fns)}')
# %%
ds = xr.open_dataset(fns[1])
time = [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values]
# ds = ds.clip(min = 0)
ds = ds.assign_coords({'time': ('tstamp',time)})

# %%
fig, ax = plt.subplots(1, 1, figsize=(6.4, 4.8), dpi=300, tight_layout=True, squeeze=True)
tstart = datetime(2025, 11, 17,0, tzinfo=timezone.utc)
tend = datetime(2025, 11, 17,4, tzinfo=timezone.utc)

da = ds[win].copy() * 4 * np.pi * 1e-9 #convert to KiloRayleighs
da = da.clip(min=0) #clip negative values to 0
da = da.sel(tstamp = slice(tstart.timestamp(), tend.timestamp()))
da.attrs['units'] = 'kR'

da.plot(x = 'time')


# %%
