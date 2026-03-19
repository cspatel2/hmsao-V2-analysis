# %%
from __future__ import annotations
from pickle import FALSE
from dateutil.parser import parse
from typing import SupportsFloat as Numeric
import subprocess
from typing import Iterable
from tqdm import tqdm
import xarray as xr
import numpy as np
from datetime import datetime,timezone,timedelta
import matplotlib.pyplot as plt
from pathlib import Path
import astropy.io.fits as fits
from datetime import timezone
from matplotlib.colors import LogNorm, PowerNorm
import matplotlib as mpl
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
mpl.rc('axes', titlesize=15)



# %% FUCTIONS
def get_time_from_fn(fn:Path) -> float:
    return float(fn.stem.split('_')[-1])

def get_tstamp_from_hdu(hdu) -> Numeric:
    if 'TIMESTAMP_S' in hdu.header:
        time_s = hdu.header['TIMESTAMP_S']
        if 'TIMESTAMP_NS' in hdu.header:
            time_ns = hdu.header['TIMESTAMP_NS']
        else:
            time_ns = 0
        time = time_s + 1e-9*time_ns
        return time
    else:
        raise ValueError('Invalid file')

def get_tstamp_from_fn(fn: str) -> Numeric:
    with fits.open(fn) as ffile:
        if len(ffile) > 1:
            hdu = ffile[1]
        else: hdu = ffile[0]
        if 'TIMESTAMP_S' in hdu.header:
            time_s = hdu.header['TIMESTAMP_S']
            if 'TIMESTAMP_NS' in hdu.header:
                time_ns = hdu.header['TIMESTAMP_NS']
            else:
                time_ns = 0
            time = time_s + 1e-9*time_ns
            return time
        else:
            raise ValueError('Invalid file')
        
def read_raw_img(fn:Path|str, pixdict:dict|None = None):
    if isinstance(fn, str):
        fn = Path(fn)
    #open fits file and read data
    with fits.open(fn) as hdul:
        if len(hdul) > 1: idx = 1
        else: idx = 0
        hdu = hdul[idx]
        data = hdu.data # type:ignore
        exp = hdu.header['EXPOSURE']
        tstamp = get_tstamp_from_hdu(hdu)

        data = np.clip(data, np.percentile(data,.5), np.percentile(data,99))

        #normalize by panel if pixdict is provided
        if pixdict is not None: 
            normdata = np.full(data.shape, np.nan)

            for key,lims in pixdict.items():
                x1, x2, y1, y2 = lims
                dat = data[x1:x2, y1:y2]
                dat -= np.nanmin(dat)
                dat /= (np.nanmax(dat)-np.nanmin(dat))
                normdata[x1:x2, y1:y2] = dat
            data = normdata
    return data, exp, tstamp
# %%
# 


print('collecting data and sorting...')
# get data and sort 
datdir = Path('~/locsststor/raw/hmsao-v2/20251116').expanduser()
fns = list(datdir.glob('*.fit*'))
fns.sort(key = get_time_from_fn)

times = [get_tstamp_from_fn(fn) for fn in fns]
times = np.asarray(times)

print('Getting data for Valid time window...')
# define relevant time window limits
window_start = datetime(2025, 11, 16, 20, 00, tzinfo=timezone.utc)
window_end = window_start + timedelta(hours = 4)
start = window_start - timedelta(minutes=10)
end = window_end + timedelta(minutes=10)
#pick out data from valid time window
valid = (times > start.timestamp()) & (times < end.timestamp())
fn = np.asarray(fns, dtype=object)
fn = fn[valid]
print(len(fn))
#%%
pixdict = {
    #win: [x1,x2,y1,y2]
    'ha': [0,1500,0,1500],
    'Hb': [0,1500,1501,-1],
    '7774': [1500,-1,0,1560],
    '6300': [1500,-1,1561,2060],
    '5577': [1500,-1,2060, 2580],
    '4278': [1500,-1,2580,-1],
} 

#%%
TEST = False
if TEST:
    data,exp,tstamp = read_raw_img(fns[0], pixdict)
    fig, ax = plt.subplots(1, 1, figsize=(6.4, 4.8), dpi=300, tight_layout=True, squeeze=True)
    img = ax.imshow(data, cmap = 'Greys')
    fig.colorbar(img, ax=ax)
    ax.axvline(1500, ymin=0.5, ymax=1, color='k', ls='--', lw=0.5)
    ax.axvline(1593, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)
    ax.axvline(2077, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)
    ax.axvline(2593, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)

    ax.axhline(1500,  xmin=0, xmax=1, color='k', ls='--', lw=0.5)

    ax.text(1550/2, 100, 'Hβ', fontsize=15, ha='center', va='center')
    ax.text(3*3008/4, 100, 'Hα', fontsize=15, ha='center', va='center')
    ax.text(900, 1600, '7774 + OH', fontsize=15, ha='center', va='center')
    ax.text(1800, 1600, '6300', fontsize=15, ha='center', va='center')
    ax.text(2300, 1600, '5577', fontsize=15, ha='center', va='center')
    ax.text(2800, 1600, '4278', fontsize=15, ha='center', va='center')

    ax.set_xticks([])
    ax.set_yticks([])

    dtime = datetime.fromtimestamp(tstamp).astimezone(timezone.utc)
    ax.set_title(f'{dtime:%Y-%m-%dZ%H:%M:%S}\nExposure: {exp:.2f} s', color='k', )


#%%
# %%

with open('filelist.txt', 'w') as ofile:
    for idx, fname in tqdm(enumerate(fn), total=len(fn), desc='Generating plots'):
        data,exp,tstamp = read_raw_img(fname, pixdict)
        fig, ax = plt.subplots(1, 1, figsize=(6.4, 4.8), dpi=300, tight_layout=True, squeeze=True)
        img = ax.imshow(data, cmap = 'Greys')
        fig.colorbar(img, ax=ax)
        ax.axvline(1500, ymin=0.5, ymax=1, color='k', ls='--', lw=0.5)
        ax.axvline(1593, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)
        ax.axvline(2077, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)
        ax.axvline(2593, ymin=0, ymax=0.5, color='k', ls='--', lw=0.5)

        ax.axhline(1500,  xmin=0, xmax=1, color='k', ls='--', lw=0.5)

        ax.text(1550/2, 100, 'Hβ', fontsize=15, ha='center', va='center')
        ax.text(3*3008/4, 100, 'Hα', fontsize=15, ha='center', va='center')
        ax.text(900, 1600, '7774 + OH', fontsize=15, ha='center', va='center')
        ax.text(1800, 1600, '6300', fontsize=15, ha='center', va='center')
        ax.text(2300, 1600, '5577', fontsize=15, ha='center', va='center')
        ax.text(2800, 1600, '4278', fontsize=15, ha='center', va='center')

        ax.set_xticks([])
        ax.set_yticks([])

        dtime = datetime.fromtimestamp(tstamp).astimezone(timezone.utc)
        ax.set_title(f'{dtime:%Y-%m-%dZ%H:%M:%S}\nExposure: {exp:.2f} s', color='k', )
        
        Path('plots').mkdir(parents=True, exist_ok=True)
        fig.savefig(f'plots/{idx}.png', bbox_inches='tight')
        plt.close(fig)
        
        div = 120
        if exp < 1:
            exp = 1/div
        else:
            exp = exp / div
        ofile.write(f"file 'plots/{idx}.png'\n")
        ofile.write(f'duration {exp:.5f}\n')

# %%
date = fns[0].stem.split('_')[0]
animation_name = f'hmsao_v2_{date}'
command = f'ffmpeg -f concat -i filelist.txt -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -fps_mode vfr -pix_fmt yuv420p {animation_name}.mp4 -y'
subprocess.run(command, shell = True)

#%%



# %%
