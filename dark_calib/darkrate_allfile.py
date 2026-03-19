#%%

import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import os
import sys
from hmspython.Utils._files import *
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
#%%
def open_fitsfile(file:str) -> np.array:
    with pf.open(file) as hdul: 
        data = hdul[1].data.astype(np.float64)
    return data

def get_exposure_from_fits(file:str) -> float:
    with pf.open(file) as hdul: 
        exposure = hdul[0].header['EXPOSURE']
        exp,unit = separate_numbers_letters(exposure)
        if unit == 'ms': exp = int(exp)*1e-3 #ms -> s
        elif unit == 'us': exp = int(exp)*1e-6 #us -> s
        else: exp = int(exp) # already in s
    return exp

def separate_numbers_letters(string:str):
    numbers = []
    letters = []
    for char in string:
        if char.isdigit():
            numbers.append(char)
        elif char.isalpha():
            letters.append(char)
    return ''.join(numbers), ''.join(letters)

def get_temp_from_fname(paths: list[str]) -> list:
    return [int(x.split('_')[-1]) for x in paths]

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
##### the final dataset should have a variable with the demensions [x,y,gain,exposure,temp]
fdir = 'calib_data'

dirs = glob(os.path.join(fdir,"*"))
dirs.sort()
len(dirs)
temps = get_temp_from_fname(dirs)
subdirs = np.asarray([glob(os.path.join(dir,'*')) for dir in dirs]).flatten()
#%%
tdir = glob(os.path.join(fdir,'*'))
gdir = []
for i in tdir:gdir+= glob(os.path.join(i,'*'))
fnames = []
for i in gdir:fnames += glob(os.path.join(i,'*'))


# %% Get mean and std for each exposure collection
meanpix = []
stdpix = []
exposures = []

for sub in subdirs:
    files = glob(os.path.join(sub,'*fits'))
    pixval = list(map(open_fitsfile, files))
    exps = list(map(get_exposure_from_fits,files))
    meanpix.append(np.mean(pixval, axis=0))
    stdpix.append(np.std(pixval, axis=0))
    exposures.append(np.mean(exps))


# %%
exposure = np.array(exposures)
meanpix = np.array(meanpix)
stdpix = np.array(stdpix)

dark = np.zeros(meanpix.shape[1:])
dark_std = np.zeros(meanpix.shape[1:])
bias = np.zeros(meanpix.shape[1:])
bias_std = np.zeros(meanpix.shape[1:])

for i in tqdm(range(meanpix.shape[1])):
    for j in range(meanpix.shape[2]):
        p, cov = curve_fit(lambda x, m, b: m*x+b, exposure,
                        meanpix[:, i, j], sigma=stdpix[:, i, j], absolute_sigma=True, p0=[0, 100])
        dark[i, j] = p[0]
        dark_std[i, j] = np.sqrt(cov[0, 0])
        bias[i, j] = p[1]
        bias_std[i, j] = np.sqrt(cov[1, 1])


# %%
data = dark
data_std = dark_std
vmin = np.mean(data) - 3 * np.mean(data_std)
vmax = np.mean(data) + 3 * np.mean(data_std)
plt.imshow(data, cmap='gist_ncar',vmin = vmin,vmax = vmax)
plt.colorbar(label='Dark Rate [Counts/sec]')
plt.xlabel('Pixel Postion X')
plt.ylabel('Pixel Postion Y')
plt.title('ZWO ASI432mm')
plt.show()
#%%
data = bias
data_std = bias_std[np.where(np.isfinite(bias_std))]
vmin = np.mean(data) - 3 * np.mean(data_std)
vmax = np.mean(data) + 3 * np.mean(data_std)
plt.imshow(data, cmap='gist_ncar',vmin = vmin,vmax = vmax)
plt.colorbar(label='Bias [Counts]')
plt.xlabel('Pixel Postion X')
plt.ylabel('Pixel Postion Y')
plt.title('ZWO ASI432mm')
plt.show()
# %%

# with lzma.open('../hitmis_l1_converter/pixis_dark_bias.xz', 'rb') as f:
#     data = pickle.load(f)
#     plt.imshow((data['dark']), cmap='gray')
#     plt.colorbar()
#     plt.show()

# %%
hist = plt.hist(dark.flatten(),100,(-0.3,0.3),True)
# %%

# %%
import lzma
import pickle

with lzma.open('pixis_dark_bias.xz', 'rb') as dfile:
        dark_data = pickle.load(dfile)
# %%
dark_data
# %%
dark = dark_data['dark']
# %%
np.shape(dark)
# %%
with fits.open('calib_data/temp_-10/gain_100/img_50_0.fits') as hdul:
    header = hdul[1].header
# %%
header
# %%
