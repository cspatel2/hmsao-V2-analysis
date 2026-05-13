#%%
import matplotlib.pyplot as plt
import xarray as xr
from pathlib import Path 
from datetime import datetime, timezone
# %%
p = Path('~/locsststor/raw/hmsao-v2').expanduser()
fns = list(p.glob('*/*fits'))
fns.sort()
# %%
dates = ['20251116', '20251117', '20251118']
# %%
fns = list(p.glob(f'*/*{dates[0]}*fits'))

# %%
datetime.strptime(dates[0], '%Y%m%d').replace(tzinfo=timezone.utc)
# %%
