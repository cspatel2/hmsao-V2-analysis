#%%
from calendar import c

from matplotlib.pylab import f
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from numpy import dsplit
import xarray as xr
import matplotlib.colors as mcolors
from pathlib import Path
from datetime import datetime, timezone,timedelta
import matplotlib as mpl
import numpy as np
import matplotlib.dates as mdates
usetex = False

if not usetex:
    # computer modern math text
    mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc('font', **{'family': 'serif',
       'serif': ['Times' if usetex else 'Times New Roman']})
# for Palatino and other serif fonts use:
# rc('font',**{'family':'serif','serif':['Palatino']})
mpl.rc('text', usetex=usetex)
mpl.rc('xtick', labelsize=9) 
mpl.rc('ytick', labelsize=9) 
plt.rc('axes', labelsize=9)
def degree_formatter(x, pos): return f"{x:.0f}°"

# %%
path = Path('~/locsststor/proc/hmsao-v2/l2')
windows = {
    '5577': 'Greens',
    '6300': 'Reds',
}
tcenter = datetime(2025, 11, 17,17,46, tzinfo=timezone.utc)
tstart = tcenter - timedelta(minutes=30)
tend = tcenter + timedelta(minutes=30)
fig, ax = plt.subplots(2, 1, figsize=(6.5, 2.5), dpi=300, tight_layout=True, squeeze=True, sharex=True, sharey=True, gridspec_kw={'wspace': 0.05})

to_rayleighs = 4 * np.pi * 1e-6

for i, (win, cmap) in enumerate(windows.items()):
    fns = list(path.expanduser().glob(f'*/*{win}*.nc'))
    fns.sort()
    print(f'# of files: {len(fns)}')
    
    ds = xr.open_dataset(fns[1])
    time = [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values]
    ds = ds.assign_coords({'time': ('tstamp',time)})
    ds.za.attrs = ds.za.attrs.copy()
    ds.za.attrs.pop('units', None)
    ds.za.attrs['long_name'] = 'Zenith Angle'
    ds.time.attrs = {
        'long_name': 'Time',
        'units': 'UTC',
    }
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax[i].xaxis.set_major_formatter(formatter)
    ax[i].yaxis.set_major_formatter(FuncFormatter(degree_formatter))


    da = ds[win].copy() * to_rayleighs  #convert to Rayleighs
    da = da.sel(tstamp = slice(tstart.timestamp(), tend.timestamp()))
    sza_cutoff = 90+12
    da = da.where(da.sza > sza_cutoff, 0) #drop negative values
    da.attrs['units'] = 'R' 

    
    vmin = np.nanpercentile(da.values, 1)
    vmax = np.nanpercentile(da.values, 99.65)
    da.plot(x = 'time', cmap=cmap, ax=ax[i], vmin = vmin, vmax = vmax)
    ax[i].axvline(tcenter, color='k', ls='--', lw=0.2)

ax[0].set_xlabel('')
plt.savefig(f'visplots/hmsao_{tcenter.strftime("%Y%m%d")}_{tcenter.strftime("%H%M%S")}.png',  dpi=600,
    bbox_inches='tight', pad_inches=0.1)

# %%
# tcenter = datetime(2025, 11, 17,17,46, tzinfo=timezone.utc)
# tstart = tcenter - timedelta(minutes=30)
# tend = tcenter + timedelta(minutes=30)
# tslice = slice(tstart.timestamp(), tend.timestamp())
# tslice = (None, None)
fig, ax = plt.subplots(2, 1, figsize=(6.5, 2.5), dpi=300, tight_layout=True, squeeze=True, sharex=True, sharey=True, gridspec_kw={'wspace': 0.05})

for i, (win, cmap) in enumerate(windows.items()):
    fns = list(path.expanduser().glob(f'*/*{win}*.nc'))
    fns.sort()
    print(f'# of files: {len(fns)}')
    
    ds = xr.open_dataset(fns[1])
    time = [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values]
    ds = ds.assign_coords({'time': ('tstamp',time)})
    ds.za.attrs = ds.za.attrs.copy()
    ds.za.attrs.pop('units', None)
    ds.za.attrs['long_name'] = 'Zenith Angle'
    ds.time.attrs = {
        'long_name': 'Time',
        'units': 'UTC',
    }
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax[i].xaxis.set_major_formatter(formatter)
    ax[i].yaxis.set_major_formatter(FuncFormatter(degree_formatter))


    da = ds[win].copy() * to_rayleighs #convert to Rayleighs
    da.attrs['units'] = 'R'
    da = da.where(da > 0 | da.isnull(), 0) #drop negative values
    sza_cutoff = 90+12
    da = da.where(da.sza > sza_cutoff,np.nan) #drop negative values
    
    vmin = np.nanpercentile(da.values, 1)
    vmax = np.nanpercentile(da.values, 99.65)
    da.plot(x = 'time', cmap=cmap, ax=ax[i], vmin = vmin, vmax = vmax)
    ax[i].axvline(tcenter, color='k', ls='--', lw=0.2)

ax[0].set_xlabel('')
plt.savefig(f'visplots/hmsao_{tcenter.strftime("%Y%m%d")}.png',  dpi=600,
    bbox_inches='tight', pad_inches=0.1)
# %%
tstart = tcenter - timedelta(minutes=30)
tend = tcenter + timedelta(minutes=30)
tslice = slice(tstart.timestamp(), tend.timestamp())
fig, ax = plt.subplots(1, 1, figsize=(6.5, 2.5), dpi=300, squeeze=True, sharex=True, sharey=True, gridspec_kw={'wspace': 0.05})

for i, (win, cmap) in enumerate(windows.items()):
    fns = list(path.expanduser().glob(f'*/*{win}*.nc'))
    fns.sort()
    print(f'# of files: {len(fns)}')
    
    ds = xr.open_dataset(fns[1])
    ds = ds.sel(tstamp = tslice)
    # ax.set_ylim(ds.tstamp[0].values, ds.tstamp[-1].values)
    time = [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values]
    ds = ds.assign_coords({'time': ('tstamp',time)})
    ds.za.attrs = ds.za.attrs.copy()
    ds.za.attrs.pop('units', None)
    ds.za.attrs['long_name'] = 'Zenith Angle'
    ds.time.attrs = {
        'long_name': 'Time',
        'units': 'UTC',
    }
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_formatter(formatter)

    da = ds[win].copy() * to_rayleighs #convert to Rayleighs
    da.attrs['units'] = 'R'
    da = da.where(da > 0 | da.isnull(), 0) #drop negative values
    sza_cutoff = 90+12
    da = da.where(da.sza > sza_cutoff,np.nan) #drop negative values
    
    vmin = np.nanpercentile(da.values, 1)
    vmax = np.nanpercentile(da.values, 99.65)
    da = da.sel(za = slice(-.1, .1)).mean('za') #select the closest to zenith
    da.plot(
                    x='time',                # Set time as x-axis
                    color=cmap[0].lower(),   # Set color from a colormap
                    ax=ax,                   # Use existing Matplotlib axes
                    ls='-',                  # Solid line style
                    marker='o',              # Circular markers
                    markersize=1,            # Size of markers
                    label=win,               # Legend label
                    lw=0.5
                    )# type: ignore
    line = ax.axvline(tcenter, color='k', ls='--', lw=0.2)
    val = da.interp(tstamp=tcenter.timestamp())
    # ax.scatter(tcenter, float(val.values), color='k',label = f'{val.values:.1f} R')  # Add a point at the intersection
    ax.annotate(f'{val.values:.1f} R', xy=(tcenter, float(val.values)), xytext=(1, .5), textcoords='offset points', fontsize=9.5, color=cmap[0].lower())  # Annotate the value
    

ax.legend(fontsize=6, title_fontsize=7, loc='upper right')
ax.set_xlabel('')
ax.set_title('Zenith Angle = 0.0°')
plt.savefig(f'visplots/hmsao_{tcenter.strftime("%Y%m%d_%H%M%S")}_za0.png',  dpi=600, bbox_inches='tight', pad_inches=0.1)

# %%
