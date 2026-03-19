# CREATES A CALIBRATION MAP USING THE CALIBRATION LAMP CURVE, FLATFIELD DATA FROM INSTRUMENT, AND COUNTRATE DATA FROM CALIBRATION LAMP MEASUREMENTS OBTAINED WITH THE INSTRUMENT
# %%
import argparse
from dataclasses import dataclass
from pathlib import Path

from matplotlib.style import available
import xarray as xr
import numpy as np
import os
import matplotlib.pyplot as plt
from glob import glob
from scipy.signal import find_peaks, peak_widths
from typing import SupportsFloat as Numeric, List
import pandas as pd


# %%
def get_fnames(datadir:str| Path, identifier:str):
    if isinstance(datadir, str):
        datadir = Path(datadir)
    datadir = datadir.expanduser()
    fnames = list(datadir.glob(f"*{identifier}*.nc"))
    fnames.sort()
    return fnames


@dataclass
class CalibGenConfig:
    """
    Configuration class for generating photometric calibration maps.
    Attributes:
        rootdir (str | Path): Root directory containing input L1b data files.
        destdir (str | Path | List[str] | List[Path] | None): Directory or list of directories to save the generated calibration maps. If None, maps are not saved.
        windows (List[str]): List of spectral window identifiers to process.
        calib_params_csv (str | Path): Path to CSV file containing calibration geometry parameters.
        calib_curve_ds_path (str | Path): Path to NetCDF file containing calibration lamp curve data.
        sourcename (str): Name of the calibration light source for metadata.
    """
    rootdir: str | Path
    destdir: str | Path | List[str] | List[Path] | None
    windows: List[str]
    calib_params_csv: str | Path
    calib_curve_ds_path: str | Path
    pos_identifier: str | List[str]
    sourcename: str


def create_photometric_calib_map(
    win: str,
    datads: xr.Dataset,
    flatds: xr.Dataset,
    calibds: xr.Dataset,
    source_diam: float,
    slit_width: float,
    foreoptic_fl: float,
    foreoptic_diam: float,
    savedir: str |Path| List[str]|List[Path] | None = None,
    sourcename: str = "Gamma Scientific RS-12D Calibration Light Source",
) -> bool:
    """
    Create a photometric calibration map (kmap) that converts countrate -> photonrate.

    Parameters:
    -----------
    win : str
        Wavelength window identifier.
    datads : xr.Dataset
        Dataset containing countrate measurements from calibration lamp.
    flatds : xr.Dataset
        Dataset containing flatfield measurements.
    calibds : xr.Dataset
        Dataset containing calibration lamp curve.
    source_diam : Numeric
        Diameter of the calibration lamp source in inches.
    slit_width : Numeric
        Width of the slit at the foreoptic in cm.
    foreoptic_fl : Numeric
        Effective focal length of the foreoptic in cm.
    foreoptic_diam : Numeric
        Diameter of the foreoptic lens in cm.
    savedir : str | Path | List[str] | List[Path] | None, optional
        Directory or list of directories to save the calibration map. If None, the map is not saved.
    sourcename : str, optional
        Name of the calibration light source.

    Returns:
    --------
    calib_map_ds : xr.Dataset
        Dataset containing the photometric calibration map.
    """
    # Extract countrate data
    nda = datads.copy()
    nda = nda.countrate
    # -----------------------------------------------------------------------------
    #   MEASURED COUNTRATE CALCULATION (calib lamp imaged by hms)
    # -----------------------------------------------------------------------------
    # Find the width of the lamp signal along za axis
    signal = nda.fillna(0).isel(pos=0).max(dim="wavelength", skipna=True)
    signal.values -= np.nanmin(signal.values)
    signal.values /= np.nanmax(signal.values)
    peaks, _ = find_peaks(
        signal.data, prominence=0.9
    )  # location of peaks in lamp singnal
    res = peak_widths(
        signal.data, peaks, rel_height=0.97
    )  # width of the lamp signal in za
    za_norm = signal.za.data[peaks]  # for later, use it to normalize flatfield
    zidx_min = int(np.floor(res[-2][0]))  # za index min of peak width
    zidx_max = int(np.ceil(res[-1][0]))  # za index max of the peak width
    zaslice = slice(zidx_min, zidx_max + 1)  # za slice covering the lamp signal

    # Calculate measured countrate
    cr_measured = nda.isel(za=zaslice).sum("za")  # 1d
    dwl = np.mean(np.diff(datads.wavelength.data))  # wavelength bin size
    cr_measured *= dwl  # countrate <-----

    # -----------------------------------------------------------------------------
    #  PHOTONS ENTERING THE SYSTEM FROM THE CALIBRATION LAMP CALCULATION (using calibration curve)
    # -----------------------------------------------------------------------------
    # Prepare calibration curve
    calibda = calibds["radiance"] * 1e-6  # Convert to W/(sr cm^2 nm)
    calibda = calibda.interp(
        wavelength=datads.wavelength
    )  # interpolate to data wavelengths

    # convert power to photonrate
    h = 6.626e-34  # Planck's constant in J*s
    c = 2.998e8  # Speed of light in m/s
    hclam = (h * c) / (
        datads.wavelength.data * 1e-9
    )  # Convert wavelength from nm to m for calculation, result in J
    calibda = calibda / hclam  # in photons/(s sr cm^2 nm)
    calibda = calibda * dwl  # in countrate/(sr cm^2)

    # calulate photonrate entering the system from the calibration lamp
    solid_angle = (
        slit_width / foreoptic_fl
    ) * source_diam  # needs to be divided by pos but that will happen in the next step
    area_lens = np.pi * (foreoptic_diam / 2) ** 2  # cm^2
    photonds = calibda.copy()
    cr_enter = photonds * area_lens * solid_angle  # CountRate* in
    cr_enter = cr_enter / nda.pos  # countrate <----

    # -----------------------------------------------------------------------------
    # CALIBRATION MAP CALCULATION
    # -----------------------------------------------------------------------------
    # Calculate calibration factor for each wavelength in a row
    k = cr_enter / cr_measured

    # Normalize flatfield data
    flatds = flatds.countrate  # .isel(pos = 0) #does not have >1 pos
    # flatds = flatds.drop_vars('pos')
    flatda = flatds.copy()
    ref_values = flatda.sel(za=za_norm, method="nearest").data
    flatda /= ref_values  # normalize to lamp signal za postion

    # Calculate calibration map : k  =  (photons entering the system) / (measured countrate) * flatfield
    calib_map = flatda * k

    # convert to Rayleighs
    aw = (
        slit_width / foreoptic_fl * np.deg2rad(np.mean(np.diff(datads.za.data)))
    )  # cm^2 sr
    calib_map_r = (
        calib_map.copy() / aw / (4 * np.pi * 1e6)
    )  # photons/(s cm^2 sr) to Rayleighs

    # Create output dataset
    calib_map_ds = xr.Dataset(
        data_vars={
            "kp": (
                ("za", "wavelength"),
                calib_map.mean("pos").data,
                {
                    "units": "photons/(s cm^2 sr) per countrate",
                    "description": "calibration map  to convert countrate -> photonrate",
                    "long_name": "K_PhotonRate",
                },
            ),
            "kr": (
                ("za", "wavelength"),
                calib_map_r.mean("pos").data,
                {
                    "units": "Rayleighs per countrate",
                    "description": "calibration map to convert countrate -> Rayleighs",
                    "long_name": "K_Rayleighs",
                },
            ),
        },
        coords={
            "za": (("za"), datads.za.data, datads.za.attrs),
            "wavelength": (
                ("wavelength"),
                datads.wavelength.data,
                datads.wavelength.attrs,
            ),
        },
        # datads.drop_dims('pos').coords,
        attrs={
            "description": "Photometric calibration map to convert countrate to photonrate and Rayleighs",
            "source_name": sourcename,
            "source_diam_in": source_diam,
            "slit_width_cm": slit_width,
            "foreoptic_focal_length_cm": foreoptic_fl,
            "foreoptic_diameter_cm": foreoptic_diam,
            "date_created": np.datetime_as_string(np.datetime64("now"), unit="s"),
        },
    )  # type: ignore
    if savedir is not None:
        if isinstance(savedir, list):
            for dir in savedir:
                dir = Path(dir).expanduser()
                dir.mkdir(parents=True, exist_ok=True)
                outfname = dir / f"photometric_calib_map_{win}.nc"
                calib_map_ds.to_netcdf(outfname)
                print(f"Calibration map saved to {outfname}")
        else:
            savedir = Path(savedir).expanduser()
            savedir.mkdir(parents=True, exist_ok=True)
            outfname = savedir / f"photometric_calib_map_{win}.nc"
            calib_map_ds.to_netcdf(outfname)
            print(f"Calibration map saved to {outfname}")
    return True


# %%

def main (config : CalibGenConfig):
    """Process 

    Args:
        config (CalibGenConfig):
    """    
    # calibration geometry parameters
    if isinstance(config.calib_params_csv, str):
        config.calib_params_csv = Path(config.calib_params_csv)
    config.calib_params_csv = config.calib_params_csv.expanduser()
    df = pd.read_csv(config.calib_params_csv, comment="#")
    df = df.set_index("item")
    source_diam = df.loc["source_diam", "value"]
    slit_width = df.loc["slit_width", "value"]
    foreoptic_fl = df.loc["foreoptic_fl", "value"]
    foreoptic_diam = df.loc["foreoptic_diam", "value"]

    if isinstance(config.rootdir, str):
        config.rootdir = Path(config.rootdir)
    config.rootdir = config.rootdir.expanduser()

    available_windows = [fn.stem.split('_')[-1] for fn in config.rootdir.glob('*flat*.nc')]
    if config.windows == ['']:
        valid_windows = available_windows
    else:
        valid_windows = [w for w in config.windows if w in available_windows]

    # calibration lamp curve data
    calibds = xr.open_dataset(config.calib_curve_ds_path)

    if isinstance(config.pos_identifier, str):
        config.pos_identifier = [config.pos_identifier]

    for win in valid_windows:
        print(f"Processing window: {win}")
        # flatfield data from hms
        fnames = get_fnames(config.rootdir, f"*flat*{win}*")
        flatds = xr.open_dataset(fnames[0])


        for p in config.pos_identifier:
            # calibration lamp imgs from hms
            fnames = get_fnames(config.rootdir, f"{p}*{win}")
            print(len(fnames), f"files found for position identifier {p} in {config.rootdir}")
            for fn in fnames:
                datads = xr.open_dataset(fn)

                kmap = create_photometric_calib_map(
                    win,
                    datads,
                    flatds,
                    calibds,
                    source_diam,  # type: ignore
                    slit_width,  # type: ignore
                    foreoptic_fl,  # type: ignore
                    foreoptic_diam,  # type: ignore
                    savedir=config.destdir,  # type: ignore
                )
                del datads, kmap

# %%
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate photometric calibration maps for HMSAO data.')
    parser.add_argument('--rootdir', 
                        type=str, 
                        required=True, 
                        help='Root directory containing input L1b data files.')
    parser.add_argument('--destdir', 
                        type=str, default='', help='Directory to save the generated calibration maps. If empty, maps are not saved.')
    parser.add_argument('--windows', 
                        type=str, required=True, help='Comma-separated list of spectral window identifiers to process.')
    parser.add_argument('--calib_params_csv', 
                        type=str, required=True, help='Path to CSV file containing calibration geometry parameters.')
    parser.add_argument('--calib_curve_ds_path', 
                        type=str, required=True, help='Path to NetCDF file containing calibration lamp curve data.')
    parser.add_argument('--pos_identifier', 
                        type=str, required=True, help='Identifier for the position variable in the data files. If multiple, provide a comma-separated list.')
    parser.add_argument('--sourcename', 
                        type=str, default="Gamma Scientific RS-12D Calibration Light Source", help='Name of the calibration light source for metadata.')
    

    args = parser.parse_args()
    config = CalibGenConfig(
        rootdir=args.rootdir,
        destdir=args.destdir,
        windows=args.windows.split(','),
        calib_params_csv=args.calib_params_csv,
        calib_curve_ds_path=args.calib_curve_ds_path,
        pos_identifier=args.pos_identifier.split(','),
        sourcename=args.sourcename
    )
    

# %%
# test
# TEST = False
# if TEST:
#     ds = xr.open_dataset("photometric_calib_map_5577.nc")
#     plt.figure()
#     ds.kr.plot(vmin=np.nanpercentile(ds.kr, 0.1), vmax=np.nanpercentile(ds.kr, 99.99))
#     plt.figure()
#     ds.kp.plot(vmin=np.nanpercentile(ds.kp, 0.1), vmax=np.nanpercentile(ds.kp, 99.99))

# %%
