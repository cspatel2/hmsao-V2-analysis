import toml
from pathlib import Path

#COPY THIS FUCTION TO ANY SCRIPT WHERE YOU WANT TO LOAD CONFIG PATHS. MAKE SURE TO UPDATE THE PATH TO YOUR CONFIG FILE IF NEEDED.
#### load config paths ####
def load_config():
    PATH = Path(__file__).resolve()
    ROOT = PATH.parent.parent
    config_path = ROOT / 'config' / 'paths.toml'
    with open(config_path, 'r') as f:
        config = toml.load(f)
    return config, ROOT


#this is an example of how to use the config file to load paths for input and output. You can modify this function to load other types of config data as needed.
config,ROOT = load_config() #load config and root path
cdict = config['instr_info'] #config dict for this script
fn = ROOT / cdict['input']['img_path']
outdir = ROOT / cdict['output']['dir']