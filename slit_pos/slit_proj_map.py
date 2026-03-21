# %%
from __future__ import annotations
from re import M
# from settings import ECL_PEAK, PLOTDIR, OBSERVER, TIMEZONE
from slit_projection import on_ellipsoid
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
# from eclipse.utils import mask_lonlat_geo
from datetime import datetime, timedelta
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.crs as ccrs


from tqdm import tqdm
import platform
if platform.system() == 'Darwin':
    from tqdm.contrib.concurrent import thread_map as process_map
else:
    from tqdm.contrib.concurrent import process_map
matplotlib.rcParams.update({'mathtext.fontset': 'cm'})

matplotlib.rc(
    'font',
    **{
        'family': 'serif',
        'serif': ['Times New Roman'],
    }
)
from pathlib import Path
import tomllib

matplotlib.rc('text', usetex=False)

# SHADOWMAP_FILE = PLOTDIR / 'eclipse_shadow_map.nc'
# SHADOWPATH_FILE = PLOTDIR / 'eclipse_shadow_path.nc'

# %%

def load_config():
    PATH = Path(__file__).resolve()
    ROOT = list(PATH.parents)[1]
    config_path = ROOT / 'config' / 'config.toml'
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    return config, ROOT

config, ROOT = load_config()

# [lat,lon,_] = config['common']['obs_location']
lat,lon,alt = 67.83, 20.46,.4

# %%
# %% Slit
slit_width = np.deg2rad(0.1)*1e3  # mrad
slit_height = np.deg2rad(30)*1e3  # mrad
x = np.concatenate(
    [
        np.full(25, slit_width/2),
        np.linspace(slit_width/2, -slit_width/2, 50, endpoint=True),
        np.full(50, -slit_width/2),
        np.linspace(-slit_width/2, slit_width/2, 50, endpoint=True),
        np.full(25, slit_width/2)
    ]
)
y = np.concatenate(
    [
        np.linspace(0, slit_height/2, 25, endpoint=True),
        np.full(50, slit_height/2),
        np.linspace(slit_height/2, -slit_height/2, 50, endpoint=True),
        np.full(50, -slit_height/2),
        np.linspace(-slit_height/2, 0, 25, endpoint=True)
    ]
)
# xx, yy = np.meshgrid(x, y)
r = np.sqrt(x*x + y*y)
phi = np.arctan2(y, x)
phi = np.rad2deg(phi)
# args = np.argsort(phi)
# phi = np.rad2deg(phi[args])
# r = r[args]
azimuth = 271 - 360
zenith = 90
alts = [120, 300]
slits = {}
for alt in alts:
    slits[alt] = on_ellipsoid(
        ssp_lat=lat, ssp_lon=lon,
        hobs=1,
        alt=alt,
        azimuth=azimuth, zenith=zenith,
        # r_opt=np.deg2rad(1)*1e3,
        r_opt=r, xi_opt=phi,  # type: ignore
        shape='custom'
    )
# %%
# create a set of axes with Mercator projection
fig, ax = plt.subplots(
    figsize=(6, 4), dpi=300,
    subplot_kw={"projection": ccrs.Orthographic(central_longitude=lon, central_latitude=lat)},
)
# ax.add_feature(cf.COASTLINE, linewidth=0.3, alpha=1)  # type: ignore
ax.add_feature(   # type: ignore
    cf.BORDERS,
    linewidth=0.75, alpha=0.5,
    edgecolor='k'
)
ax.add_feature(  # type: ignore
    cf.STATES,
    linewidth=0.2, alpha=0.5,
    color='gainsboro', edgecolor='none'
)
ax.add_feature(  # type: ignore
    cf.STATES,
    linewidth=0.5, alpha=0.5,
    edgecolor='k'
)
ax.add_feature(  # type: ignore
    cf.LAKES,
    linewidth=0.5, alpha=0.5,
    edgecolor='k'
)
ax.add_feature(  # type: ignore
    cf.RIVERS,
    linewidth=0.2, alpha=0.5,
    edgecolor='k'
)

lon_formatter = LongitudeFormatter(zero_direction_label=True)
lat_formatter = LatitudeFormatter(True)
# ax.xaxis.set_major_formatter(lon_formatter)
# ax.yaxis.set_major_formatter(lat_formatter)
ax.set_extent([lon - 5, lon + 5, lat - 2, lat + 3])  # type: ignore

# Slits
for idx in range(len(alts)):
    try:
        slat, slon = slits[alts[idx]]
        slat_center = np.mean(slat)
        slon_center = np.mean(slon)
        slat_min = np.min(slat)
        slat_max = np.max(slat)
        slon_min = np.min(slon)
        slon_max = np.max(slon)
        angle = np.rad2deg(
            np.arctan2(
                slat_max - slat_min,
                slon_max - slon_min,
            )
        )
        ax.plot(
            slon, slat, color='r' if idx else 'g',  # marker='.', ls='',
            linestyle=':' if idx else '-',
            linewidth=1 if idx else 2, 
            alpha=0.75, 
            transform=ccrs.PlateCarree(),
        )
    except Exception as e:
        print(f"Error plotting slit at {alts[idx]} km: {e}")
        continue

gl = ax.gridlines(  # type: ignore
    crs=ccrs.PlateCarree(), draw_labels=True,
    linewidth=0.5, color='gray', alpha=0.5,
    linestyle='--'
)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 8, 'font': 'Times New Roman'}
gl.ylabel_style = {'size': 8, 'font': 'Times New Roman'}
ax.scatter(
    [lon], [lat], s=20, marker='x', color='b',
    transform=ccrs.PlateCarree(), linewidths=1, zorder=10
)

# ax.text(
#     lon + 0.5, lat, f"HiT&MIS",
#     fontsize=8, font='Times New Roman', color='b',
#     transform=ccrs.PlateCarree(),
#     horizontalalignment='left', verticalalignment='center'
# )
ax.tick_params(axis='both', which='both', labelsize=5)
ax.scatter(
    [], [], marker='x', color='b',
    label='HiT&MIS Ground Location',
    lw=0.5,
)
ax.plot(
    [], [], ls='-', color='g',
    label='HiT&MIS Slit Projected to 120 km Altitude',
    lw=0.5,
)
ax.plot(
    [], [], ls=':', color='r',
    label='HiT&MIS Slit Projected to 300 km Altitude',
    lw=0.5,
)

ax.legend(
    loc='upper left', fontsize=7, frameon=True,
    facecolor='white', edgecolor='black', framealpha=1
)
fig.savefig( "hitmis_slit_projection_map.png", dpi=600,
    bbox_inches='tight', pad_inches=0.1
)
# fig.savefig(PLOTDIR / "eclipse_shadow_map.pdf", dpi=300)
plt.show()

# %%