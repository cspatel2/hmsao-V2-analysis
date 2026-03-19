#%%
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits as fits
# %%
fn = 'solar_spec.fits'
# %%
with fits.open(fn) as hdul:
    if len(hdul) > 1: idx = 1
    else: idx = 0
    data = hdul[idx].data # type:ignore
    wls = [d[0]/10 for d in data]
    fluxes = [d[1] for d in data]
# %%
plt.plot(wls, fluxes)
plt.xlim(770,780)
# %%
