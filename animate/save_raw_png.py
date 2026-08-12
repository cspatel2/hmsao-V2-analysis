#%%
import PIL.Image as Image
import numpy as np
from astropy.io import fits
from pathlib import Path
from datetime import datetime, timezone

# %%
p = Path('~/locsststor/raw/hmsao-V2').expanduser()
date = '20251116'
time = '2257'
fns = list(p.glob(f'*{date}*/*{time}*.fits'))
fns.sort()
# %%
fn = fns[0]
with fits.open(fn) as hdul:
    data = hdul[1].data
    header = hdul[1].header
    print(header['DATE-OBS'])
    print(data.shape)
    print(data.dtype)
    # convert to uint16
    data = data.astype(float)
    vmin = np.percentile(data, 0.1)
    vmax = np.percentile(data, 99.9)
    data = (data - vmin) / (vmax - vmin) * 65535
    data = data.astype(np.uint16)
    # save as png
    img = Image.fromarray(data)
    img.save(f'plots/raw_png/raw_{fn.stem}.png')
# %%
