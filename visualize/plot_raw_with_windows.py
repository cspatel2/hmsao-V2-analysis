#%%
from tkinter import font

from matplotlib.colors import PowerNorm
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from pathlib import Path

from scipy.datasets import face

#%%
def get_tstamp_from_hdu(hdu) -> float:
    if 'TIMESTAMP_S' in hdu.header:
        time_s = hdu.header['TIMESTAMP_S']
        if 'TIMESTAMP_NS' in hdu.header:
            time_ns = hdu.header['TIMESTAMP_NS']
        else:
            time_ns = 0
        time = time_s + 1e-9*time_ns
        return time
    else:
        raise Warning('Invalid file')
#%%
bounds_panel_bottom = {'7774':[None,1593],
        '6300':[1593,2077],
        '5577':[2077,2593],
        '4278':[2593,None],
        
}

bounds_panel_top = {'6563':[None,1573],
                    '4861':[1573,None]
                    }

p = Path('~/locsststor/raw/hmsao-V2').expanduser()
date = '20251116'
time = '2257'
fns = list(p.glob(f'*{date}*/*{time}*.fits'))
fns.sort()
print(len(fns))
#%%
fname = fns[0]
with fits.open(fname) as hdul:
            exptime = hdul[1].header['EXPOSURE']
            tstamp = get_tstamp_from_hdu(hdul[1])
            data = np.array(hdul[1].data, dtype=float)

outdata = np.zeros_like(data)
bottom = data[1686:,:]
for key,bound in bounds_panel_bottom.items():
    d = bottom[:,bound[0]:bound[-1]].copy()
    vmin = np.nanpercentile(d,1)
    vmax = np.nanpercentile(d,99)
    d = np.clip(d, vmin,vmax)
    # vmin = np.min(d)
    # vmax = np.max(d)
    d = (d - vmin)
    d /= (vmax-vmin)
    # plt.figure()
    # plt.imshow(d, vmin = 0, vmax = 1)
    # plt.colorbar()
    bottom[:,bound[0]:bound[-1]] = d
outdata[1686:,:] = bottom

top = data[:1500 - 186,:]
for key,bound in bounds_panel_top.items():
    d = top[:,bound[0]:bound[-1]].copy()
    vmin = np.nanpercentile(d,5)
    vmax = np.nanpercentile(d,99)
    d = np.clip(d, vmin,vmax)
    # vmin = np.min(d)
    # vmax = np.max(d)
    d = (d - vmin)
    d /= (vmax-vmin)
    # plt.figure()
    # plt.imshow(d, vmin = 0, vmax = 1)
    # plt.colorbar()
    top[:,bound[0]:bound[-1]] = d

outdata[:1500-186,:] = top

#%%
plt.figure(figsize=(6.8, 4.6), dpi=300)
plt.imshow(outdata, vmax = 1, cmap = 'bone')
plt.colorbar()


#%%
outimg = outdata.copy()

fig, ax = plt.subplots(figsize=(3008/300, 3008/300), dpi=300, constrained_layout=True, facecolor='k')

im = ax.imshow(outimg,cmap =  'bone', aspect='equal')#,norm=PowerNorm(.5))
linecolor = 'white'
lw = 1.5
ax.axvline(1593, ymin=0, ymax=0.5, color=linecolor, ls='--', lw=lw)
ax.axvline(2077, ymin=0, ymax=0.5, color=linecolor, ls='--', lw=lw)
ax.axvline(2593, ymin=0, ymax=0.5, color=linecolor, ls='--', lw=lw)

ax.axvline(1573, ymin=0.5, ymax=1, color=linecolor, ls='--', lw=lw)

ax.axhline(1500, xmin=0, xmax=1, color=linecolor , ls='--', lw=lw)


font = {'family': 'serif',
        'color':  'white',
        'weight': 'normal',
        'size': 27,
        }
y_text = 1400
ax.text(750, y_text, '6563', ha='center', va='center', color='white', fontdict=font)
ax.text(2250, y_text, '4861', ha='center', va='center', color='white', fontdict=font)
y_text = 1600
ax.text(900, y_text, r'7774 + OH + $N_2^+$', ha='center', va='center', color='white', fontdict=font)
ax.text(1800, y_text, '6300', ha='center', va='center', color='white', fontdict=font)
ax.text(2300, y_text, '5577', ha='center', va='center', color='white', fontdict=font)
ax.text(2800, y_text, '4278', ha='center', va='center', color='white', fontdict=font)
ax.set_xticks([])
ax.set_yticks([])
outfn = Path ('cedar/plots/raw_with_windows.png')
outfn.parent.mkdir(exist_ok=True)
plt.savefig(outfn, dpi=300, facecolor='k')
# %%
