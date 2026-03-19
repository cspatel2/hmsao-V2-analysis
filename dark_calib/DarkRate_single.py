#%%
#this file creates a dict (saved as .nc file) of dark rate and bias FOR A GIVEN TEMP AND GAIN SETTING.

from ast import Raise
from multiprocessing import Value
# from _pytest.stash import D
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import os
import sys
# from hmspython.Utils._files import *
import pickle
import lzma
import os
import astropy.io.fits as pf
from PIL import Image
import numpy as np
from glob import glob
from tqdm import tqdm
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy.optimize import curve_fit
from typing import SupportsFloat as Numeric
import xarray as xr
import argparse
#%%
def get_temp_from_path(path:str) -> int | None:
    if 'temp' in path:
        for word in fdir.split('/'):
            if 'temp' in word:
                return(int(word.split('_')[-1]))
    else: raise ValueError('No temp in path.')
    
def get_gain_from_path(path:str) -> int | None:
    if 'gain' in path:
        for word in fdir.split('/'):
            if 'gain' in word:
                return(int(word.split('_')[-1]))
    else: raise ValueError('No temp in path.')
    
def get_exposure_from_path(path:str) -> int:
    fn = os.path.basename(path)
    return int(fn.split('_')[1])

def get_exposure_from_hdu(hdu) -> Numeric:
    if 'EXPOSURE_S' in hdu.header:
        exp_s = hdu.header['EXPOSURE_S']
        if 'EXPOSURE_NS' in hdu.header:exp_ns = hdu.header['EXPOSURE_NS']
        else: exp_ns = 0 
        exp = exp_s + 1e-9*exp_ns
        return exp
    else:
        raise ValueError('Invalid File')
#%%
parser = argparse.ArgumentParser(
    description='This file converts raw dark images (at a set temp and gain) taken at multiple exposures to darkrate and bias img. Returns a .nc file.'
)

parser.add_argument(
    'rootdir',
    metavar= 'rootdir',
    type = str,
    help = 'Root directory where raw data is stored.'
)

#%%

# get all the file paths
fdir = '/home/charmi/Projects/hms-ao/dark_calib/calib_data/temp_-15/gain_100'
# args = parser.parse_args()
# fdir = args.rootdir

# if not os.path.exists(fdir): raise ValueError('Root Directory provided does not exist.')
# elif os.path.exists(fdir) and os.path.isfile(fdir): raise ValueError('Path provided is a file.')

##
temp = get_temp_from_path(fdir)
gain = get_gain_from_path(fdir)
print(f'temp setting: {temp} C \nGain setting: {gain} db')

# exposures to loop through
loop_exp = np.unique([get_exposure_from_path(f) for f in glob(os.path.join(fdir,"*"))]) 
print(f'number of unique exposures: {len(loop_exp)}')
# %% Get mean and std for each exposure collection
meanpix = []
stdpix = []
exposures = []
for exp in tqdm(loop_exp):
    files = glob(os.path.join(fdir,f'*{exp}_*.fit*'))
    pixval,exposure = [],[]
    for fn in files:
        with fits.open(fn) as hdul:
            hdu = hdul['IMAGE']
            pixval.append(hdu.data) # counts
            exposure.append(get_exposure_from_hdu(hdu)) #s
    meanpix.append(np.mean(pixval, axis=0))
    stdpix.append(np.std(pixval, axis=0))
    exposures.append(np.mean(exposure))

e= np.asarray(exposures)
m= np.asarray(meanpix)
s= np.asarray(stdpix)
#%%
# Reshape meanpix to (x, y*y) to treat each exposure as a 2D array flattened into 1D
reshaped = m.reshape(m.shape[0], -1)

# Compute statistics over pixels for each exposure
percentile_1 = np.percentile(reshaped, 1, axis=1)
mean_counts = np.mean(reshaped, axis=1)
median_counts = np.median(reshaped, axis=1)
percentile_99 = np.percentile(reshaped, 99, axis=1)

# Define exposure indices
exposures = np.arange(m.shape[0])
#%%
# Plot the results
plt.plot(exposures, percentile_1, label="1 percentile", linestyle="-")
plt.plot(exposures, mean_counts, label="mean", linestyle="-")
plt.plot(exposures, median_counts, label="Median", linestyle="-.")
plt.plot(exposures, percentile_99, label="99 percentile", linestyle="-")
plt.xlabel('Exosure [s]')
plt.ylabel('Counts/pix')
plt.title(f'temp setting: {temp} C \nGain setting: {gain} db')
plt.legend()
#%%
plt.plot(e,m[:,1,1])
plt.xlabel('Exosure [s]')
plt.ylabel('Counts/pix')
plt.title(f'temp setting: {temp} C \nGain setting: {gain} db')
#%%%
a= 10
b = -1
exposures= e[a:b]
meanpix = m[a:b]
stdpix = s[a:b]
i = 20
j = 2
p, cov = curve_fit(lambda x, m, b: m*x+b, exposures,
                        meanpix[:, i, j], sigma=stdpix[:, i, j], absolute_sigma=True, p0=[0, np.median(meanpix)])
plt.plot(exposures, meanpix[:, i, j])
plt.plot(exposures, p[0]*exposures+p[1])
print(p[0],p[1])
print(f'dark current (e/s/pix) = {p[0]}')
#%% fit each pixel for dark and bias
print(f'Fitting each pixel...')
exposures= np.asarray(exposures)
meanpix = np.asarray(meanpix)
stdpix = np.asarray(stdpix)

dark = np.zeros(meanpix.shape[1:])
dark_std = np.zeros(meanpix.shape[1:])
bias = np.zeros(meanpix.shape[1:])
bias_std = np.zeros(meanpix.shape[1:])

for i in tqdm(range(meanpix.shape[1])):
    for j in range(meanpix.shape[2]):
        p, cov = curve_fit(lambda x, m, b: m*x+b, exposures,
                        meanpix[:, i, j], sigma=stdpix[:, i, j], absolute_sigma=True, p0=[0, 100])
        dark[i, j] = p[0]
        dark_std[i, j] = np.sqrt(cov[0, 0])
        bias[i, j] = p[1]
        bias_std[i, j] = np.sqrt(cov[1, 1])
print('Fitting done.')

#%% make a dataset and save
outname = os.path.join(os.path.dirname(__file__), f'zwoasi533_darkbias_T{temp}_G{gain}.nc')
print(f'Saiving {outname}...')

darkdict = {'darkrate': dark,
            'darkrate_std': dark_std,
            'bias':bias,
            'bias_std':bias_std}

ds = xr.Dataset(
     data_vars=dict(
         darkrate=(["xpix", "ypix"], dark),
         darkrate_std=(["xpix", "ypix"], dark_std),
         bias=(["xpix", "ypix"], bias),
         bias_std=(["xpix", "ypix"], bias_std),
         ),
     coords=dict(
         xpix = np.arange(0,np.shape(dark)[0],1),
         ypix = np.arange(0,np.shape(dark)[1],1),
         ),
     attrs=dict(description=f"Dark rate and bias of ZWO ASI533 cam at temp {temp}C and gain {gain} db."),
     )


ds.to_netcdf(outname)
print('Done.')

# %%
# data = dark
# data_std = dark_std
# vmin = np.mean(data) - 3 * np.mean(data_std)
# vmax = np.mean(data) + 3 * np.mean(data_std)
# plt.imshow(data, cmap='gist_ncar',vmin = vmin,vmax = vmax)
# plt.colorbar(label='Dark Rate [Counts/sec]')
# plt.xlabel('Pixel Postion X')
# plt.ylabel('Pixel Postion Y')
# plt.title('ZWO ASI533mm')
# plt.show()
# #%%
# data = bias
# data_std = bias_std[np.where(np.isfinite(bias_std))]
# vmin = np.mean(data) - 3 * np.mean(data_std)
# vmax = np.mean(data) + 3 * np.mean(data_std)
# plt.imshow(data, cmap='gist_ncar',vmin = vmin,vmax = vmax)
# plt.colorbar(label='Bias [Counts]')
# plt.xlabel('Pixel Postion X')
# plt.ylabel('Pixel Postion Y')
# plt.title('ZWO ASI533mm')
# plt.show()

#%%
ds =xr.open_dataset('/mnt/d/Projects/hms-ao/dark_calib/zwoasi533_darkbias_T-15_G100.nc')
#%%

ds.bias.plot()

#%%
fdir = 'trial_data/20250126'
files = glob(os.path.join(fdir,'*.fit*'))
len(files)
# %%
from astropy.io import fits 
import datetime

file = files[-1]
with fits.open(file) as hdul:
    hdu = hdul[1]
    data = hdu.data
    

# %%
dt = datetime.datetime.strptime(file.strip('.fits').split('/')[-1].split('.')[0], '%Y%m%d%H%M%S')

vmin = np.nanpercentile(data,.01)
vmax = np.nanpercentile(data,99.9)
plt.imshow(data, vmin = vmin,vmax = vmax)
plt.colorbar()
plt.title(dt.strftime('%Y-%m-%d %H:%M:%S'))
# %%

# %%

# %%
