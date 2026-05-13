#%%
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime, timezone, timedelta
from scipy.ndimage import gaussian_filter1d
# %%
p = Path('~/local_data/hmsao-v2/l1a').expanduser()
#%%
list(p.glob('**/*'))
# %%
win = '7774'
date = '20251116'
fns = list(p.glob(f'**/*{date}*{win}*.nc'))
fns.sort()
# %%
fidx = -1
ds = xr.open_dataset(fns[fidx])
# %%
times = [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values]
ds = ds.assign_coords(time=('tstamp', times))

#%%
if fidx == -1: dt = datetime(2025,11,16,23,10, tzinfo=timezone.utc)
else:dt = times[50]
pda= ds.countrate.sel(tstamp = dt.timestamp(),method = 'nearest').sel( za = slice(-15,15), wavelength = slice(777, 786.5))
offset =   -0.05
pda['wavelength'] = pda.wavelength + offset
vmin = 0
vmax = pda.quantile(.999)
pda.plot(y = 'za', vmin = vmin, vmax = vmax)
#%%
fig,ax = plt.subplots(2,1,figsize=(6.4, 4.8), sharex=True)
pda.plot(ax = ax[0],y = 'za', vmin = vmin,vmax = vmax, cmap = 'plasma')
ax[0].set_title(f'{pda.time.values:%Y-%m-%d %H:%M} UTC')

# pda.plot(ax = ax[1],y = 'za', vmin = 0, vmax = 8, cmap = 'RdYlBu')
l = pda.sel(za = -15, method = 'nearest').clip(0, None)
l.values = gaussian_filter1d(l.values, sigma = 2)
l.plot(ax = ax[1], lw = 0.5)
solar_lines = [777.4, 778. , 778.8, 779.7, 780.1, 780.7, 781. , 783.2, 783.6, 784.9, 785.5] 
for wl in solar_lines:
    ax[1].axvline(wl, color='orange', linestyle='--', lw = .5)

oh_lines = [780.8,782.1, 784.1, 786.06]
for wl in oh_lines:
    ax[1].axvline(wl, color='green', linestyle='--', lw = .5)

n2_lines = [777.36, 782.8, 786.19, 787.96]
for wl in n2_lines:
    ax[1].axvline(wl, color='blue', linestyle='--', lw = .5)

ax[1].axvline(782.55, color='black', linestyle='--', lw = .5)

ax[1].set_title(f'')