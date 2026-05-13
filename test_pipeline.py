# %%
from __future__ import annotations
from calendar import c
from logging import root
from multiprocessing.pool import RUN
from os import path
from pickle import TRUE
from re import sub
import tomllib
import re
import numpy as np
import os
from pathlib import Path
import xarray as xr

from l1a_converter.hmsao_l1a_converter import main as l1a_main, L1AConfig, str2bool, list_of_strings
from l1b_converter.secondary_straightening.generate_line_profile import main as line_prof_gen_main, LineProfileConfig
from l1b_converter.hmsao_l1b_converter import main as l1b_main, L1BConfig

from l1bc_calibration.step1_fits2ds import main as calib_fits2ds_main, Fits2DsConfig
from l1bc_calibration.step2_ds_l1a_converter import main as calib_l1a_main, CalibL1AConfig
from l1bc_calibration.step3_L1b_converter import main as calib_l1b_main, CalibL1BConfig
from l1bc_calibration.step4_gen_calibmap import main as calib_gen_calibmap, CalibGenConfig

from l1c_converter.hmsao_l1C_converter import main as l1c_main, L1CConfig
from l2_converter.hmsao_l2_converter import main as l2_main, L2Config

# %%
def load_config():
    PATH = Path(__file__).resolve()
    ROOT = PATH.parent
    config_path = ROOT / 'config' / 'config.toml'
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    return config, ROOT
# 
RUN_CALIB_L0 =False
RUN_CALIB_L1A = False
RUN_L1A = True
RUN_LINEPROF_GEN = True
RUN_CALIB = True
RUN_L1B = False
RUN_L1C = False
RUN_L2 = False
CONFIG,ROOT = load_config() #load config dict and root path

#%% populate all the dirs with the common values if they are set to '**' in the config
COMMON = CONFIG['common']
for key, kdict in CONFIG.items():
    if key != 'common':
        for k, val in kdict.items():
            if val == '**':
                CONFIG[key][k] = COMMON[k]
#%%
if RUN_CALIB_L0:
    print("Running calibration - step 1 (Fits2Ds) ########################################")
    subdict = CONFIG['calib_fits2ds']
    #check that position identifiers in the config are found in the rootdir
    a =list(Path(subdict['rootdir']).expanduser().glob('*pos*'))
    poslist = np.unique([p.name.split('_')[0] for p in a])
    poslist = np.unique([re.sub(r'\d+','',p) for p in poslist]) #take numberic out of string to get unique position identifier
    valid_pos = list(set(subdict['pos_identifier']) &(set(poslist)))
    if len(valid_pos) > 0:
        print(f"Position identifiers in the config are found in the rootdir.\navailable position identifiers in the rootdir: {poslist} \nposition identifiers in the config: {subdict['pos_identifier']}")
    else:
        raise ValueError(f"None of the position identifiers in the config are found in the rootdir.\navailable position identifiers in the rootdir: {poslist} \nposition identifiers in the config: {subdict['pos_identifier']}")

    for p in valid_pos:
            fits2ds_config = Fits2DsConfig(
                rootdir=subdict['rootdir'],
                destdir=subdict['destdir'],
                slitsize=subdict['slitsizeum'],
                sourcename=subdict['sourcename'],
                overwrite=str2bool(subdict['overwrite']),
                pos_identifier=p
            )
            calib_fits2ds_main(fits2ds_config)

if RUN_CALIB_L1A:
    print("Running calibration - step 2 (DS to L1A) ########################################")
    subdict = CONFIG['calib_ds_l1a_converter']
    ds2l1a_config = CalibL1AConfig(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        model=subdict['model'],
    )
    calib_l1a_main(ds2l1a_config)
    
if RUN_L1A:
    print("Running L1A conversion ########################################")
    #get config for L1A conversion
    subdict = CONFIG['l1a_converter']
    #set up data class for L1A conversion
    darkpath = list((Path(subdict['darkdir']).expanduser()).glob('**/*dark*l0*.nc'))[0]
    
    l1a_config = L1AConfig(
        rootdir=subdict['rootdir'],
        destdir=os.path.join(subdict['destdir'], 'l1a'),
        dest_prefix=subdict['dest_prefix'],
        overwrite=str2bool(subdict['overwrite']),
        windows=subdict['windows'],
        dates=subdict['dates'],
        dark=darkpath,
        slitsizeum=subdict['slitsizeum'],
        chunksize=subdict['chunksize'],
        readnoise=subdict['readnoise'],
        model = subdict['model'],
    )
    # run L1A Conversion
    l1a_main(l1a_config)

if RUN_LINEPROF_GEN:
    print("Running line profile generation ########################################")

    #config dict for line profile generation (required for L1B conversion)
    subdict = CONFIG['line_profile_gen'] 
    destdir = ROOT / subdict['destdir']

    #set up data class for line profile generation
    line_config = LineProfileConfig(
        rootdir=subdict['rootdir'],
        flatdir = subdict['flatdir'],
        destdir=destdir,
        date=subdict['date'],
        overwrite=str2bool(subdict['overwrite']),
    )

    line_prof_gen_main(line_config)

if RUN_CALIB:
    print("Running calibration - step 3 ########################################")
    subdict = CONFIG['calib_l1b_converter']
    ds2l1b_config = CalibL1BConfig(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        flatdir=subdict['flatdir'],
        windows=subdict['windows'],
        line_profile_dir=subdict['line_profile_dir'],
    )
    calib_l1b_main(ds2l1b_config)

    print("Running calibration - step 4 ########################################")
    subdict = CONFIG['calib_gen_calibmap']
    calibmap_config = CalibGenConfig(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        windows=subdict['windows'], 
        calib_params_csv=subdict['calib_params_csv'],
        calib_curve_ds_path=subdict['calib_curve_ds_path'],
        pos_identifier=subdict['pos_identifier'],
        sourcename=subdict['sourcename']
    )
    calib_gen_calibmap(calibmap_config)

#%%
if RUN_L1B:
    print("Running L1B conversion ########################################")
    subdict = CONFIG['l1b_converter']
    l1b_config = L1BConfig(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        windows=subdict['windows'],
        dates=subdict['dates'],
        flatdir=subdict['flatdir'],
        line_profile_dir=subdict['line_profile_dir']
    )
    l1b_main(l1b_config)

#%%
if RUN_L1C:
    print("Running L1C conversion ########################################")
    subdict = CONFIG['l1c_converter']

    l1c_config = L1CConfig(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        windows=subdict['windows'],
        calibmap_dir=subdict['calibmap_dir'],
        photon=str2bool(subdict['photon'])
    )
    l1c_main(l1c_config)


# %%
if RUN_L2:
    print("Running L2 conversion ########################################")
    subdict = CONFIG['l2_converter']

    l2_config = L2Config(
        rootdir=subdict['rootdir'],
        destdir=subdict['destdir'],
        dest_prefix=subdict['dest_prefix'],
        overwrite=subdict['overwrite'],
        zabinsize=subdict['zabinsize'],
        windows=subdict['windows'],
        dates=subdict['dates'],
        obs_location=subdict['obs_location'],
        soldir=subdict['soldir']
    )
    l2_main(l2_config)
