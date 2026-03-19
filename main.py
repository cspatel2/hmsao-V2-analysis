#%%
from pathlib import Path
from re import sub
import matplotlib.pyplot as plt
import xarray as xr
import pandas as pd
import numpy as np
# %%
datadir  = Path('/home/charmi/Codes/python/hmsao-V1/l1b_converter/photometric_calib/calib-data/l1a')
# %%
fnames = list(datadir.glob('*.nc'))
fnames.sort()
# %%
ds = xr.open_dataset(fnames[0])
# %%
ds
# %%
fn = 'config_requirements/l1a_converter/hmsao_calibration_slit_100um_20251013_dark_l0.nc'
# %%
ds = xr.open_dataset(fn)
# %%
ds
# %%


# %%
datdir = Path('~/locsststor/raw').expanduser()
# %%
subdirs = list(datdir.glob("*v2*"))
subdirs.sort()
# %%
ddirs = list(subdirs[-2].iterdir())
ddirs.sort()
#%%
ids = np.unique([s.stem.split('_')[0][:-1] for s in ddirs if 'pos' in s.stem])

# %%
ids
# %%

ddir = Path('config_requirements/l1b_converter')
fn = list(ddir.glob('line_profile_*.nc'))
l1 = xr.open_dataset(fn[0])
l2 = xr.open_dataset('line_profile_6300.nc')

print(f'L1 (now) diff: {np.mean(l1.za.diff("za").values)}')
print(f'L2 (before) diff: {np.mean(l2.za.diff("za").values)}')

# %%
datadir = Path('~/locsststor/proc/hmsao-v1_calibration_slit_100um_20251013/l1a').expanduser()
fns = list(datadir.glob('**/*.nc'))
fns.sort()
ds1 = xr.open_dataset(fns[0])
ds2 = xr.open_dataset(Path('postship_calib_202508/data/l1a/hmsao_calibration_slit_100um_20251013_flatfield_opal_l1_4278.nc'))
# %%
print(f'ds1 (now) diff: {np.mean(ds1.za.diff("za").values)}')
print(f'ds2 (before) diff: {np.mean(ds2.za.diff("za").values)}')
# %%
