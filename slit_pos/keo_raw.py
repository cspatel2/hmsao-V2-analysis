#%%
#creates a keogram of the raw data for each day (UTC). this will help us see when and where the stars are crossing our slits

#%%
import numpy as np 
import matplotlib.pyplot as plt
import astropy.io.fits as fits
from glob import glob
import os
from skimage.transform import rotate
# %%
fdir = '20250124/'
fnames = glob(os.path.join(fdir,'*.fit*'))
len(fnames)
# %%
i = 100
with fits.open(fnames[i]) as hdul:
    if len(hdul) > 1: idx = 1
    else: idx = 0 
    data = np.asarray(hdul[idx].data, dtype=float)
    
data = rotate(data,-.7)
# %%
vmin = np.percentile(data,.1)
vmax = np.percentile(data,99.9)
#%%
plt.imshow(data, vmin = vmin, vmax = vmax)


kwargs = {'lw' : 0.5,
        'ls' : '--',
        'c' : 'white'}
plt.axvline(1520, **kwargs)
plt.axhline(1460, **kwargs)
plt.colorbar()
# %%
midh = 1475 # middle horizontal line seperation at pixel 1475
hav = 1515 # h-alpha vertial line speration from the panel next to it 
ha = data[:midh,:hav]
hb = data[:midh,hav:]

ohv = 1570
oh = data[midh:,:ohv ]
redv = ohv+ 495
red = data[midh:, ohv:redv]
greenv = redv+ 520
green = data[midh:, redv:greenv]
blue = data[midh:, greenv:]
vmin = np.percentile(blue,1)
vmax = np.percentile(blue,99)
plt.imshow(blue, vmin = vmin, vmax = vmax)
# %%
