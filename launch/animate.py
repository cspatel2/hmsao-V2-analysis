# %%
from __future__ import annotations
from dateutil.parser import parse
from typing import SupportsFloat as Numeric
import subprocess
from typing import Iterable
from tqdm import tqdm
import xarray as xr
from matplotlib.ticker import LogLocator, ScalarFormatter
import numpy as np
from datetime import datetime,timezone,timedelta
import matplotlib.pyplot as plt
# from uncertainties import ufloat, unumpy as unp
from glob import glob
import os

import astropy.io.fits as fits
import pytz
from matplotlib.colors import LogNorm, PowerNorm


# %%
# solref = xr.open_dataset('sao_2010_solref.nc')
# solref.sel(wavelength=slice(654, 658)).counts.plot()

# %%
def get_time_from_fn(fn:str) -> int:
    return float(fn.strip('.fits').split('/')[-1])

def get_tstamp_from_hdu(hdu) -> Numeric:
    if 'TIMESTAMP_S' in hdu.header:
        time_s = hdu.header['TIMESTAMP_S']
        if 'TIMESTAMP_NS' in hdu.header:
            time_ns = hdu.header['TIMESTAMP_NS']
        else:
            time_ns = 0
        time = time_s + 1e-9*time_ns
        return time
    else:
        raise ValueError('Invalid file')

def get_tstamp_from_fn(fn: str) -> Numeric:
    with fits.open(fn) as ffile:
        if len(ffile) > 1:
            hdu = ffile[1]
        else: hdu = ffile[0]
        if 'TIMESTAMP_S' in hdu.header:
            time_s = hdu.header['TIMESTAMP_S']
            if 'TIMESTAMP_NS' in hdu.header:
                time_ns = hdu.header['TIMESTAMP_NS']
            else:
                time_ns = 0
            time = time_s + 1e-9*time_ns
            return time
        else:
            raise ValueError('Invalid file')
        
get_tstamp_from_fn('20250124/000520.609.fits')
# %%
sweden = pytz.timezone('Europe/Stockholm')
# cd_start = datetime(2025, 1, 24, 14, 0, tzinfo=pytz.timezone('Europe/Stockholm')) #countdown start

launch_start = datetime(2025, 1, 24, 17, 35, tzinfo=timezone.utc).astimezone(sweden)  #liftoff at 17:35 utc -> sweden local time
launch_end = launch_start + timedelta(minutes=10)
start = launch_start - timedelta(hours=2)
end = launch_end + timedelta(hours=2)

#%%
datdir = '20250124/'
fn = glob(os.path.join(datdir,'*.fit*'))
fn.sort(key = get_time_from_fn)
print(len(fn))
# %%
times = list(map(get_tstamp_from_fn, fn))
times = np.asarray(times)
# %%
valid = (times > start.timestamp()) & (times < end.timestamp())
# %%
fn = np.asarray(fn, dtype=object)
fn = fn[valid]
#%%
bounds = {'7774':[None,1593],
        '6300':[1593,2077],
        '5577':[2077,2593],
        '4278':[2593,None]
}
#%%
fname = fn[3]
with fits.open(fname) as hdul:
            exptime = hdul[1].header['EXPOSURE']
            tstamp = get_tstamp_from_hdu(hdul[1])
            data = np.array(hdul[1].data, dtype=float)

data = data[1686:,:]
for key,bound in bounds.items():
    d = data[:,bound[0]:bound[-1]].copy()
    vmin = np.nanpercentile(d,20)
    vmax = np.nanpercentile(d,99)
    d = np.clip(d, vmin,vmax)
    # vmin = np.min(d)
    # vmax = np.max(d)
    d = (d - vmin)
    d /= (vmax-vmin)
    plt.figure()
    plt.imshow(d, vmin = 0, vmax = 1)
    plt.colorbar()
    data[:,bound[0]:bound[-1]] = d

#%%

fig, ax = plt.subplots(figsize=(1900/300, 1080/300), dpi=300)

im = ax.imshow(data,cmap =  'cividis_r', aspect='equal',norm=PowerNorm(.5))
ax.axvline(1593, ymin=0, ymax=1, color='k', ls='--', lw=0.5)
ax.axvline(2077, ymin=0, ymax=1, color='k', ls='--', lw=0.5)
ax.axvline(2593, ymin=0, ymax=1, color='k', ls='--', lw=0.5)

ax.text(900, 1400, '7774 + OH', fontsize=15, ha='center', va='center')
ax.text(1800, 1400, '6300', fontsize=15, ha='center', va='center')
ax.text(2300, 1400, '5577', fontsize=15, ha='center', va='center')
ax.text(2800, 1400, '4278', fontsize=15, ha='center', va='center')
ax.set_xticks([])
ax.set_yticks([])

# plt.colorbar()


# %%
with open('filelist.txt', 'w') as ofile:
    for idx, fname in tqdm(enumerate(fn), total=len(fn), desc='Generating plots'):
        with fits.open(fname) as hdul:
            exptime = hdul[1].header['EXPOSURE']
            tstamp = get_tstamp_from_hdu(hdul[1])
            data = np.array(hdul[1].data, dtype=float)

            data = data[1686:,:]
            for key,bound in bounds.items():
                d = data[:,bound[0]:bound[-1]].copy()
                vmin = np.nanpercentile(d,20)
                vmax = np.nanpercentile(d,99)
                d = np.clip(d, vmin,vmax)
                # vmin = np.min(d)
                # vmax = np.max(d)
                d = (d - vmin)
                d /= (vmax-vmin)
                data[:,bound[0]:bound[-1]] = d

            fig, ax = plt.subplots(figsize=(1900/300, 1080/300), dpi=300)

            im = ax.imshow(data,cmap =  'cividis_r', aspect='equal',norm=PowerNorm(.5))
            color = 'k'
            div = 120
            if not (tstamp - 120 <= launch_start.timestamp() or launch_end.timestamp() <= tstamp + 120):
                # print('In launch window')
                color = 'r'
                div = 60
            ax.axvline(1593, ymin=0, ymax=1, color='k', ls='--', lw=0.5)
            ax.axvline(2077, ymin=0, ymax=1, color='k', ls='--', lw=0.5)
            ax.axvline(2593, ymin=0, ymax=1, color='k', ls='--', lw=0.5)

            ax.text(900, 1400, '7774 + OH', fontsize=15, ha='center', va='center')
            ax.text(1800, 1400, '6300', fontsize=15, ha='center', va='center')
            ax.text(2300, 1400, '5577', fontsize=15, ha='center', va='center')
            ax.text(2800, 1400, '4278', fontsize=15, ha='center', va='center')
            ax.set_xticks([])
            ax.set_yticks([])

            dtime = datetime.fromtimestamp(tstamp).astimezone(pytz.utc)
            ax.set_title(f'{dtime:%Y-%m-%dZ%H:%M:%S}\nExposure: {exptime:.2f} s', color=color)

            fig.savefig(f'plots/{idx}.png', bbox_inches='tight')
            plt.close(fig)
        # with fits.open(fname) as hdul:
        #     exptime = hdul[1].header['EXPOSURE']
        #     tstamp = get_tstamp_from_hdu(hdul[1])
        #     data = np.array(hdul[1].data, dtype=float)
        #     fig, ax = plt.subplots(figsize=(1900/300, 1080/300), dpi=300)
        #     vmin = np.percentile(data, 1)
        #     vmax = np.percentile(data, 99.5)
        #     im = ax.imshow(data, vmin=vmin, vmax=vmax, aspect='equal', cmap='gist_heat')#'gist_ncar_r')
        #     color = 'k'
        #     div = 120
        #     if not (tstamp - 120 <= launch_start.timestamp() or launch_end.timestamp() <= tstamp + 120):
        #         # print('In launch window')
        #         color = 'r'
        #         div = 60
        #     fig.colorbar(im, label='Counts (ADU)')
        #     ax.axhline(1686, color='k', ls='--', lw=0.5)
        #     ax.axvline(1593, ymin=0, ymax=((3008-1686)/3008), color='k', ls='--', lw=0.5)
        #     ax.axvline(2077, ymin=0, ymax=((3008-1686)/3008), color='k', ls='--', lw=0.5)
        #     ax.axvline(2593, ymin=0, ymax=((3008-1686)/3008), color='k', ls='--', lw=0.5)
        #     ax.text(900, 1600, '7774 + OH', fontsize=6, ha='center', va='center')
        #     ax.text(1800, 1600, '6300', fontsize=6, ha='center', va='center')
        #     ax.text(2300, 1600, '5577', fontsize=6, ha='center', va='center')
        #     ax.text(2800, 1600, '4278', fontsize=6, ha='center', va='center')
        #     dtime = datetime.fromtimestamp(tstamp).astimezone(pytz.utc)
        #     fig.suptitle(f'{dtime:%Y-%m-%dZ%H:%M:%S}\nExposure: {exptime:.2f} s', color=color)
        #     fig.savefig(f'plots/{idx}.png', bbox_inches='tight')
        #     plt.close(fig)
            # plt.show()
            if exptime < 1:
                exptime = 1/div
            else:
                exptime = exptime / div
            ofile.write(f"file 'plots/{idx}.png'\n")
            ofile.write(f'duration {exptime:.5f}\n')
        # break

# %%
subprocess.run(
    'ffmpeg -f concat -i filelist.txt -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -fps_mode vfr -pix_fmt yuv420p hitmis_originlaunch.mp4 -y',
    shell=True
)
#%%

subprocess.run(
    'ffmpeg -f concat -i filelist.txt -vsync vfr -pix_fmt yuv420p hitmis_originlaunch.mp4 -y', shell=True)
# %%
ds = xr.open_dataset('../keocounts/hitmis_datagram_20240408_6300.nc')
ds = ds.sel(wl=slice(630.1, 630.4), height=slice(None, 330), tstamp=slice(
    ecl_start.timestamp(), ecl_end.timestamp()
))
imgs: xr.DataArray = ds.imgs
exposure: xr.DataArray = ds.exposure
imgs = imgs.coarsen({'height': 10}, boundary='pad').mean()
# with open('filelist.txt', 'w') as ofile:
#     for i, image in enumerate(imgs):
#         fig, ax = plt.subplots(figsize=(1920/300, 1080/300), dpi=300)
#         # for img in image:
#         #     img.plot(ax=ax)
#         (image).plot(ax=ax, cmap='viridis')
#         time = float(image.tstamp)
#         exp = float(ds.exposure[i])
#         time = datetime.fromtimestamp(time)
#         ax.set_title(f'{time:%Y-%m-%d %H:%M:%S}')
#         fig.savefig(f'plots/{i}.png', dpi=300)
#         plt.close(fig)
#         ofile.write(f"file 'plots/{i}.png'\n")
#         ofile.write(f'duration {exp/20:.5f}\n')
# subprocess.run(
#     'ffmpeg -f concat -i filelist.txt -vsync vfr -pix_fmt yuv420p hitmis_6300_new.mp4 -y', shell=True)
# %%


def background_fcn(x, a0):
    return a0  # + a2*(x-x0)**2


def feature_fcn(x, c, a, w):
    return a*np.exp(-((x-c)/w)**2)


bfunc = GenericFitFunc(background_fcn=background_fcn, num_background_params=1)
bfunc.register_feature_fcn(fcn=feature_fcn, num_params=3)
bfunc.finalize()

emission = np.full(imgs.values.shape[:-1], np.nan)
emission_std = np.full(imgs.values.shape[:-1], np.nan)

for i, image in enumerate(imgs):
    time = float(image.tstamp)
    time = datetime.fromtimestamp(time)
    plotted = False
    for j, img in enumerate(image):
        x = img.wl.values
        y = img.values
        # y = gaussian_filter1d(y, 10)

        p0 = [y.mean()] + [630.2, y.std()*0.01, 0.1]
        p_min = [-np.inf] + [630.1, 0, 0.05]
        p_max = [np.inf] + [630.35, y.std()*5, 0.15]
        gfit = GenericFitManager(
            img.wl.values,
            img.values,
            p0=p0,
            baseclass=bfunc,
            window_title=f'{time:%H:%M:%S} ({i}) {j}',
            plot=False
        )
        try:
            gfit.run(bounds=(p_min, p_max))
            res = gfit.wrap_results()
            p, cov = res['output']
            amp = ufloat(p[-2], np.sqrt(cov[-2, -2]))
            fwhm = ufloat(p[-1], np.sqrt(cov[-1, -1]))
            area = amp*fwhm*np.sqrt(np.pi)
            areastd = area.std_dev
            area = area.nominal_value
            # if np.isfinite(area) and np.isinf(areastd):
            emission[i, j] = area
            emission_std[i, j] = areastd
            print(f'{time:%H:%M:%S} ({i}) {j}: {area} ± {areastd}, {fwhm}')
            if not plotted:
                fig, ax = gfit.plot(
                    figure_title=f'{time:%H:%M:%S} ({i}) {j}', show_kwargs={'block': False})
                plt.pause(1)
                plt.close(fig)
                plotted = True

        except Exception as e:
            print(f'Error {time:%H:%M:%S} ({i}) {j}: {e}')

eds = xr.Dataset(
    data_vars={
        'emission': (('tstamp', 'height'), emission[:, ::-1], {'units': 'counts/s'}),
        'emission_std': (('tstamp', 'height'), emission_std[:, ::-1], {'units': 'counts/s'}),
        'exposure': (('tstamp',), ds.exposure.values, {'units': 's'})
    },
    coords={
        'tstamp': (('tstamp',), imgs.tstamp.values, {'units': 's', 'description': 'Unix timestamp'}),
        'height': (('height',), 25 - np.arange(len(imgs.height)) * 1.2285012285012442, {'units': 'deg'}),
    }
)

eds.to_netcdf('eclipse_6300.nc')
# %%
with xr.open_dataset('eclipse_6300.nc') as eds:
    with open('filelist.txt', 'w') as ofile:
        for i, image in enumerate(eds.emission):
            fig, ax = plt.subplots(figsize=(1920/300, 1080/300), dpi=300)
            image.plot(ax=ax)
            # np.log10(image).plot(ax=ax, cmap='viridis')
            time = float(image.tstamp)
            exp = float(ds.exposure[i])
            time = datetime.fromtimestamp(time)
            ax.set_title(f'{time:%Y-%m-%d %H:%M:%S}')
            fig.savefig(f'plots/{i}.png', dpi=300)
            plt.close(fig)
            ofile.write(f"file 'plots/{i}.png'\n")
            ofile.write(f'duration {exp/20:.5f}\n')
    subprocess.run(
        'ffmpeg -f concat -i filelist.txt -vsync vfr -pix_fmt yuv420p counts_6300.mp4 -y', shell=True)

# %%
eds = xr.open_dataset('emission_6300.nc')
# %%
eds = eds.sel(height=slice(0, 25))
emission = eds.emission / eds.emission_std
(emission).T.plot(vmin=np.nanmin(emission), vmax=np.nanmax(emission))
# %%
# ds = xr.open_dataset('../keocounts/hitmis_datagram_20240408_6300.nc')
# ds = ds.sel(wl=slice(None, 631), height=slice(None, 350))
# with open('filelist.txt', 'w') as ofile:
#     for i in range(len(ds.imgs)):
#         fig, ax = plt.subplots(figsize=(1920/300, 1080/300), dpi=300)
#         np.log10(ds.imgs[i]).plot(ax=ax)
#         time = float(ds.tstamp[i])
#         exp = float(ds.exposure[i])
#         time = datetime.fromtimestamp(time)
#         ax.set_title(f'{time:%Y-%m-%d %H:%M:%S}')
#         fig.savefig(f'plots/{i}.png', dpi=300)
#         plt.close(fig)
#         ofile.write(f"file 'plots/{i}.png'\n")
#         ofile.write(f'duration {exp/10:.5f}\n')
# # %%
# ds = xr.open_dataset('../keocounts/hitmis_datagram_20240408_5577.nc')
# # ds = ds.sel(wl=slice(None, 631), height=slice(None, 350))
# with open('filelist.txt', 'w') as ofile:
#     for i in range(len(ds.imgs)):
#         fig, ax = plt.subplots(figsize=(1920/300, 1080/300), dpi=300)
#         np.log10(ds.imgs[i]).plot(ax=ax)
#         time = float(ds.tstamp[i])
#         exp = float(ds.exposure[i])
#         time = datetime.fromtimestamp(time)
#         ax.set_title(f'{time:%Y-%m-%d %H:%M:%S}')
#         fig.savefig(f'plots/{i}.png', dpi=300)
#         plt.close(fig)
#         ofile.write(f"file 'plots/{i}.png'\n")
#         ofile.write(f'duration {exp/10:.5f}\n')
# # %%
# ds = xr.open_dataset('../keocounts/hitmis_datagram_20240408_4861.nc')
# ds = ds.sel(wl=slice(485, 487), height=slice(None, 350))
# with open('filelist.txt', 'w') as ofile:
#     for i in range(len(ds.imgs)):
#         fig, ax = plt.subplots(figsize=(1920/300, 1080/300), dpi=300)
#         np.log10(ds.imgs[i]).plot(ax=ax)
#         time = float(ds.tstamp[i])
#         exp = float(ds.exposure[i])
#         time = datetime.fromtimestamp(time)
#         ax.set_title(f'{time:%Y-%m-%d %H:%M:%S}')
#         fig.savefig(f'plots/{i}.png', dpi=300)
#         plt.close(fig)
#         ofile.write(f"file 'plots/{i}.png'\n")
#         ofile.write(f'duration {exp/10:.5f}\n')
# %%
