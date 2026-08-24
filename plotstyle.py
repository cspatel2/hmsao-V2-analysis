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
import matplotlib as mpl
mpl.rcParams.update({'mathtext.fontset': 'cm'})
mpl.rc(
    'font',
    **{
        'family': 'serif',
        'serif': ['Times New Roman',]
    }
)
mpl.rc('text', usetex=False)

plt.rcParams.update({
    'font.size': 12,          # Global default
    'axes.titlesize': 16,     # Subplot title
    'axes.labelsize': 14,     # X and Y axis labels
    'xtick.labelsize': 10,    # X-axis tick labels
    'ytick.labelsize': 10,    # Y-axis tick labels
    'legend.fontsize': 11,    # Legend text
    'figure.titlesize': 18    # Main figure title (suptitle)
})