# %%
from __future__ import annotations
import argparse
import os
from pathlib import Path
from l1a_converter.hmsao_l1a_converter import main as l1a_main, L1AConfig, str2bool, list_of_strings
from l1b_converter.hmsao_l1b_converter import main as l1b_main, WINDOWS
from l1c_converter.hmsao_l1C_converter import main as l1c_main
# %%

# argument parser
parser = argparse.ArgumentParser(
    description='Execute full pipeline for HiT&MIS data'
)

parser.add_argument(
    '--rootdir',
    metavar='rootdir',
    # required = True,
    type=str,
    # default =
    nargs='?',
    help='Root Directory containing HiT&MIS data'
)

parser.add_argument(
    '--dest',
    metavar='dest',
    # required = False,
    type=str,
    default=os.getcwd(),
    nargs='?',
    help='Root directory where L1 data will be stored.'
)

parser.add_argument(
    '--dest_prefix',
    metavar='dest_prefix',
    # required = False,
    type=str,
    default=None,
    nargs='?',
    help='Prefix of the saved L1 data finename.'
)

parser.add_argument(
    '--overwrite',
    required=False,
    type=str2bool,
    default=False,
    nargs='?',
    help='If you want to rewrite an existing file, then True. Defaults to False.'
)

parser.add_argument(
    '--dates',
    required=False,
    type=list_of_strings,
    default=None,
    nargs='?',
    help='Dates to process in the format YYYYMMDD  (list seperated by commas).'
)

parser.add_argument(
    '--dark',
    # metavar = 'NAME',
    required=False,
    type=str,
    # default = None,
    nargs='?',
    help='Dark data (.nc) file path.'
)

parser.add_argument(
    '--slitsizeum',
    # metavar = 'NAME',
    required=True,
    type=str,
    # default = AS REQUIRED,
    nargs='?',
    help='Slit size (width) in micrometers.'
)

parser.add_argument(
    '--chunksize',
    # metavar = 'NAME',
    required=False,
    type=int,
    default=10,  # fix this later depending on what the ideal number of files should be per chunk
    nargs='?',
    help='Number of files per chunk.'
)

parser.add_argument(
    '--readnoise',
    # metavar = 'NAME',
    required=False,
    type=float,
    default=6,
    nargs='?',
    help='Readnoise value (ADU) to be used for readnoise correction.'
)
args = parser.parse_args()
config = L1AConfig(
    rootdir=args.rootdir,
    dest=os.path.join(args.dest, 'l1a'),
    dest_prefix=args.dest_prefix,
    overwrite=args.overwrite,
    windows=WINDOWS,
    dates=args.dates,
    dark=args.dark,
    slitsizeum=args.slitsizeum,
    chunksize=args.chunksize,
    readnoise=args.readnoise
)
# L1A Conversion
l1a_main(config)
# L1B Conversion
print("Starting L1B Conversion...")
print(f"L1A data directory: {Path(args.dest) / 'l1a'}")
print(f"L1B destination directory: {Path(args.dest) / 'l1b'}")
l1b_main(
    datadir=Path(args.dest) / 'l1a',
    destdir=Path(args.dest) / 'l1b',
)
# L1C Conversion
print("Starting L1C Conversion...")
print(f"L1B data directory: {Path(args.dest) / 'l1b'}")
print(f"L1C destination directory: {Path(args.dest) / 'l1c'}")
l1c_main(
    config.rootdir=Path(args.dest) / 'l1b',
    destdir=Path(args.dest) / 'l1c',
    photon=True
)