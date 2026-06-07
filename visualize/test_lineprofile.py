#%%
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pathlib import Path
# %%
win = '6563'
p = Path("../config_requirements/line_profiles").expanduser()
fn = list(p.glob(f'*{win}*.nc'))[0]

#%%
ds = xr.open_dataset(fn)
da = ds['line_profile']
da.plot(y = 'za')

# %%
