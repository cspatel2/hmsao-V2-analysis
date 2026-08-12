#%%
from turtle import color

from matplotlib import cm, path
from matplotlib import colors
from matplotlib.colors import LinearSegmentedColormap
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib as mpl
import matplotlib.dates as mdates
from datetime import datetime, timedelta, timezone
from PIL import Image
import numpy as np
import seaborn as sns
import matplotlib.ticker as ticker

# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import matplotlib.ticker as ticker
# from matplotlib.colors import LinearSegmentedColormap
# from datetime import timezone
# import numpy as np
mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc(
    'font',
    **{
        'family': 'serif',
        'serif': ['Times New Roman',]
    }
)
mpl.rc('text', usetex=False)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)
fontsize = 18

#%%
def asi_keogram_png2ds(path_png: Path, year: int, month: int, day: int) -> xr.DataArray:
    '''
    Loads a keogram image from the ASI and converts it into an xarray DataArray with dimensions 'za', 'tstamp', and 'channel'. The 'za' coordinate ranges from 90 to -90 degrees, and the 'tstamp' coordinate is generated based on the provided date, spanning 24 hours. The 'channel' coordinate corresponds to the RGB channels of the image. The function returns the DataArray with brightness values in the RGB channels, which can be used for further analysis or visualization.
    '''
    img = Image.open(path_png).convert("RGB")
    img_array = np.array(img)
    H, W = img_array.shape[:2]

    deg_per_pix = H / 180
    za_ = np.linspace(90,-90,H)

    start = datetime(year, month, day, 12, tzinfo=timezone.utc)
    end  = start + timedelta(hours = 24)
    tstamp_ = np.linspace(start.timestamp(), end.timestamp(), W, endpoint=True)
    time_ = [datetime.fromtimestamp(t,tz=timezone.utc) for t in tstamp_] 

    imgda = xr.DataArray(
        img_array,
        dims = ['za','tstamp','channel'],
        coords = dict(
            za = ('za',za_, {'units': r'$^\circ$', 'long_name': 'Zenith Angle'}),
            tstamp = ('tstamp',tstamp_, {'long_name': 'Time'}),
            channel = ('channel', ['r','g','b'])
        )
    )
    
    imgda = imgda.assign_coords({'time': ('tstamp', time_)})
    imgda = imgda.sortby('za', ascending=False)
    return imgda

def get_ds_dict(fdir: Path, features: list) -> dict:
    ''' loads the datasets for the specified features and returns a dictionary of DataArrays with brightness values in kR, clipped to the 1st and 99th percentiles. The keys of the dictionary are the wavelengths as strings.
    '''
    dsdict = {}
    for wl in features:
        fns = list(fdir.glob(f'*{wl}*.nc'))
        ds = xr.open_dataset(fns[0])
        ds = ds.assign_coords({'time': ('tstamp', [datetime.fromtimestamp(t, tz=timezone.utc) for t in ds.tstamp.values])})
        da = ds.brightness * (4*np.pi*1e-6)/1e3 # kR
        vmin = np.nanpercentile(da.values, 1)
        vmax = np.nanpercentile(da.values, 99.8)
        da = da.clip(vmin,vmax)
        da.za.attrs['units'] = r'$^\circ$'
        da.za.attrs['long_name'] = 'Zenith Angle'
        # da.tstamp.attrs['long_name'] = 'Time'
        dsdict[wl] = da
    return dsdict

def load_mag_data(path: Path, timeslice: slice) -> xr.Dataset:
    mag = xr.open_dataset(path)
    mag = mag.assign_coords({'time': ('tstamp', [datetime.fromtimestamp(t, tz=timezone.utc) for t in mag.tstamp.values])})
    mag = mag.sel(tstamp=slice(timeslice.start, timeslice.stop))
    mag = mag.swap_dims({'tstamp': 'time'})
    return mag

#%% PLOT


#%%

# %%

def plot(features: list, dsdict: dict, imgda: xr.DataArray, mag: xr.Dataset, year: int, month: int, day: int, hour:int|None = None, minute:int|None = None, tdelta: timedelta = timedelta(hours=1)) -> None:
    '''
    Plots the emission features, ASI keogram, and magnetometer data. The function creates a multi-panel figure with 5 rows and 2 columns, where the first column contains the emission features and ASI keogram, and the second column contains the corresponding colorbars and labels. The magnetometer data is plotted in the last row with three y-axes for Bx, By, and Bz components. The x-axis is shared across all subplots and formatted to show time in UTC. The function saves the resulting figure as a PNG file.
    '''
    # --- 1. Custom Colormaps ---
    colors = {
        '5577': '#00FF00',  # Vibrant Green
        '6300': "#ff3131",  # Vibrant Red
        '7774': '#00FFFF'   # Vibrant Cyan
    }
    basecolor = '#242323'
    cmaps = [LinearSegmentedColormap.from_list(f"Black{color}", [basecolor, color]) for color in colors.values()]

    locator = mdates.AutoDateLocator(minticks=3)
    formatter = mdates.ConciseDateFormatter(locator, tz=timezone.utc)

    # --- 2. Define GridSpec Layout (Thinner Colorbars via width_ratios) ---
    fig = plt.figure(figsize=(10, 9), dpi=300)
    # Changed width_ratios from [18, 1] to [35, 1] to make colorbars thinner
    gs = fig.add_gridspec(5, 2, width_ratios=[35, 1], hspace=0.15, wspace=0.04)

    # Create the 5 main axes sharing the x-axis
    ax_mag = fig.add_subplot(gs[4, 0])  
    axs = [fig.add_subplot(gs[i, 0], sharex=ax_mag) for i in range(4)]
    axs.append(ax_mag)

    # 3. Slice your datasets using your numeric timestamps
    wl = '6300'
    zaslice = slice(np.ceil(dsdict[wl].za.values[-1]), np.ceil(dsdict[wl].za.values[0]))
    if hour is not None and minute is not None:
        start_time = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        end_time = start_time + tdelta
        timeslice = slice(start_time.timestamp(), end_time.timestamp())
    else:
        timeslice = slice(dsdict[wl].tstamp.values[0], dsdict[wl].tstamp.values[-1])
    xlim = (timeslice.start, timeslice.stop)
    # --- 4. Plot Emission Features (Rows 0, 1, 2) ---
    for i, wl in enumerate(features):
        ds_sliced = dsdict[wl].sel(tstamp=timeslice, za=slice(zaslice.stop, zaslice.start))
        
        p = ds_sliced.swap_dims({'tstamp': 'time'}).plot.imshow(
            ax=axs[i], x="time", y="za", cmap=cmaps[i], add_colorbar=False
        )
        
        cax = fig.add_subplot(gs[i, 1])
        wl_label = r'$N_{2}^+ M(2,0)$' if wl == '7774' else f'{wl}Å'
        cbar = fig.colorbar(p, cax=cax, format="%.0f")
        cbar.set_label(wl_label, labelpad=8, fontsize=14)  # Bigger label
        cbar.ax.tick_params(labelsize=9)  # Smaller ticks
        
        # axs[i].set_ylabel('')
        axs[i].set_ylabel(r"Zenith Angle [$^\circ$]", fontsize=14)

        axs[i].set_xlabel('')
        
        axs[i].yaxis.set_major_locator(ticker.MaxNLocator(3))
        axs[i].tick_params(axis='y', labelsize=9)  # Smaller ticks
        plt.setp(axs[i].get_xticklabels(), visible=False)

    # --- 5. Plot Kiruna Imager Data (Row 3) ---
    imgda_sliced = imgda.sel(tstamp=timeslice, za=zaslice)
    imgda_sliced.swap_dims({'tstamp': 'time'}).plot.imshow(x='time', ax=axs[3], add_colorbar=False)

    ax_asi_label = fig.add_subplot(gs[3, 1])
    ax_asi_label.axis('off')
    ax_asi_label.text(0.3, 0.5, "Kiruna ASI", va="center", ha="center", rotation=90, transform=ax_asi_label.transAxes, fontsize=14)

    # axs[3].set_ylabel('')
    axs[3].set_ylabel(r"Zenith Angle [$^\circ$]", fontsize=14)

    axs[3].set_xlabel('')
    axs[3].yaxis.set_major_locator(ticker.MaxNLocator(3))
    axs[3].tick_params(axis='y', labelsize=9)  # Smaller ticks
    plt.setp(axs[3].get_xticklabels(), visible=False)

    # --- 6. Plot Magnetometer Data (Row 4) ---
    ls = '-'
    lw = 1.0

    # axs[4].set_title("Kiruna Magnetometer", fontsize=16, pad=12)
    # Axis 1: Bx (Left Y-Axis - Scaled / 100)
    color = 'black'
    l1 = (mag.KIRX / 100).plot(x='time', label=r'$B_x$', ax=axs[4], color=color, linestyle=ls, lw=lw)
    axs[4].set_ylabel(r'$B_x$ [$\times 10^2$ nT]', color=color, labelpad=10, fontsize=14)
    axs[4].tick_params(axis='y', labelcolor=color, labelsize=9)

    # Axis 2: By (First Right Y-Axis - Scaled / 100)
    color = 'blue'
    ax2 = axs[4].twinx()
    l2 = (mag.KIRY / 100).plot(x='time', label=r'$B_y$', ax=ax2, color=color, linestyle=ls, lw=lw)
    ax2.set_ylabel(r'$B_y$ [$\times 10^2$ nT]', color=color, labelpad=10, fontsize=14)
    ax2.tick_params(axis='y', labelcolor=color, labelsize=9)

    # Axis 3: Bz (Second Right Y-Axis - Scaled / 100)
    color = 'red'
    ax3 = axs[4].twinx()
    l3 = (mag.KIRZ / 100).plot(x='time', label=r'$B_z$', ax=ax3, color=color, linestyle=ls, lw=lw)
    ax3.set_ylabel(r'$B_z$ [$\times 10^2$ nT]', color=color, labelpad=10, fontsize=14)
    ax3.tick_params(axis='y', labelcolor=color, labelsize=9)
    ax3.spines['right'].set_position(('outward', 65))

    # Combined Legend
    # labels = [r'$B_x$', r'$B_y$', r'$B_z$']
    # lines = [l1, l2, l3]
    # axs[4].legend(lines, labels, loc='upper left', framealpha=0.9, fontsize=11)
    axs[4].set_xlabel('')
    axs[4].tick_params(axis='x', labelsize=10)

    # Apply shared formatting to the bottom X-axis
    axs[4].xaxis.set_major_locator(locator)
    axs[4].xaxis.set_major_formatter(formatter)
    
    axs[4].set_xlim(datetime.fromtimestamp(xlim[0], tz=timezone.utc), datetime.fromtimestamp(xlim[1], tz=timezone.utc))
    # --- 7. Global Labels and Layout Tuning ---
    axs[0].set_title("Emission Brightness [kR]", fontsize=16, pad=12)
    # fig.supylabel(r"Zenith Angle [$^\circ$]", fontsize=14)
    fig.supxlabel(r"Time [UTC]", y=0.03, fontsize=14)

    # Adjust bounds layout cleanly to fit labels and outward right spine
    fig.subplots_adjust(left=0.11, right=0.86, top=0.93, bottom=0.08)
    fig.savefig(f"plots/keogram_comparison_{year}{month}{day}.png", dpi=300, bbox_inches="tight")
# %%
if __name__ == "__main__":

    features = ['5577', '6300','7774']
    year, month, day = 2025, 11, 16
    hour, minute = 21, 0

    fdir = Path('~/local_data_cedar/hmsao-v2/l2').expanduser()
    dsdict = get_ds_dict(fdir, features)

    imgfn = Path("dark_keo20251116.png")
    imgda = asi_keogram_png2ds(imgfn, year, month, day)

    mag = load_mag_data(Path('mag_kiruna.nc'), timeslice=slice(dsdict['6300'].tstamp.values[0], dsdict['6300'].tstamp.values[-1]))
    
    plot(features, dsdict, imgda, mag, year, month, day, hour, minute, timedelta(hours=3))
# %%
