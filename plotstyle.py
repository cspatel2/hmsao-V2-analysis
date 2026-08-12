#%%
import matplotlib as mpl
usetex = False

if not usetex:
    # computer modern math text
    mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc('font', **{'family': 'serif',
       'serif': ['Times' if usetex else 'Times New Roman']})
# for Palatino and other serif fonts use:
# rc('font',**{'family':'serif','serif':['Palatino']})
mpl.rc('text', usetex=usetex)
mpl.rc('xtick', labelsize=10) 
mpl.rc('ytick', labelsize=10) 




# fig, ax = plt.subplots(1, 1, figsize=(6.4, 4.8), dpi=300, tight_layout=True, squeeze=True)

mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc(
    'font',
    **{
        'family': 'serif',
        'serif': ['Times New Roman',]
    }
)
mpl.rc('text', usetex=False)