#%%
import matplotlib.pyplot as plt
import numpy as np
from wcwidth import width
import xarray as xr
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
#%%

def get_datafiles(path, win, version):
    p = Path(path).expanduser()
    fns = list(p.glob(f'*{version}/l1b/*/*{win}*.nc'))
    fns.sort()
    return fns

def load_ref_spectra( kind,path:str| Path ="~/locsststor/proc/ref_spectra" ):
    if kind not in ['solar', 'night']:
        raise ValueError(f"kind must be either 'solar' or 'night', got {kind}")
    if isinstance(path, str):
        path = Path(path).expanduser()
    fns = list(path.glob(f'*{kind}*.nc')) 
    ds = xr.open_dataset(fns[0])
    return ds

def Normalize(da, dim=None,sigma=0, invert_signal=False):
    """
    Normalize the data array `da` along the specified dimension `dim`.
    If `dim` is None, normalize the entire array globally.
    If `invert_signal` is True, invert the normalized signal (1 - normalized value).
    """
    if dim is None:
        # normalize the entire array globally
        vmin = da.min()
        vmax = da.max()
        da = da - vmin
        da = da / (vmax - vmin)
        if sigma > 0:
            da = gaussian_filter1d(da, sigma=sigma)
    else:
        # normalize each slice along `dim` independently
        vmin = da.min(dim=dim)
        vmax = da.max(dim=dim)
        da = da - vmin
        da = da / (vmax - vmin)
        if sigma > 0:
            da = gaussian_filter1d(da, sigma=sigma, axis=da.get_axis_num(dim))
    if invert_signal:
        da = 1 - da
    return da

def Gaussian_r(x, amplitude, width, offset, residual):
    return amplitude * np.exp(-((x - offset) ** 2) / (2 * width ** 2)) + residual
#%%

win = '5577'
version = 'v2'
p = Path("~/local_data")
fns = get_datafiles(p, win, version)    
print(len(fns))
# %%
ds = xr.open_dataset(fns[0]) 
ds = ds.drop_vars(['param'])
tidx = 3
da = ds.countrate.isel(tstamp=tidx)
da.plot(y = 'za')
#%%
da = da.coarsen(za=20, boundary="trim").mean()
da.plot(y = 'za')
# %%
windowsize = 0.2
central_wl = int(win)/10
fitda = da.curvefit(
        coords="wavelength",
        func=Gaussian_r,
        skipna=True,
        p0={
            "amplitude": np.abs(np.abs(da.max(skipna=True)) - np.abs(da.min(skipna=True))),
            "width": windowsize / 2,
            "offset": central_wl,
            "residual": 0,},errors="ignore",)  # type: ignore

# %%
zidx = -20
da.isel(za=zidx).plot(label="Signal")  # type: ignore
fitted_coeffs = fitda. curvefit_coefficients.isel(za=zidx).values
x = da.wavelength.values
y_fit = Gaussian_r(x, *fitted_coeffs)
y_fiterr = (fitda.curvefit_covariance.isel(za=zidx).values.diagonal() ** 0.5)  # type: ignore
plt.plot(x, y_fit, color="r", label=f"Fitted Gaussian\nLine Center = {fitted_coeffs[2]:.2f} nm \nFWHM = {fitted_coeffs[1]:.4f} +/- {y_fiterr[1]:.4f} nm")
plt.legend(loc="best")
# %%
paramidx = 1
y = fitda.za.values
x = fitda.curvefit_coefficients.isel(param = paramidx).values
err = [fitda.curvefit_covariance.isel(za=zidx).values.diagonal() ** 0.5 for zidx in range(len(fitda.za))]  # type: ignore
xerr = np.array(err)[:, paramidx]
plt.errorbar(x, y, xerr=xerr, fmt=".", label="Fitted FWHM", capsize=3, elinewidth=.7, markeredgewidth=.7, markersize=3, ecolor="k", color="red")
plt.xlabel("Zenith Angle Index")
plt.ylabel("Fitted FWHM (nm)")
plt.legend(loc="best")  
# %%
