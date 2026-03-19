#%%
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits as fits
from PIL import Image
from misdesigner import *

## solar spectrum from NIST: https://bass2000.obspm.fr/solar_spect.php

# %%
CAMSCALE = 66.2
# fn = '20260217_160440.383.fits'
fn = '20260217_155635.249.fits'
# %%
pixdict = {
    #win: [x1,x2,y1,y2]
    'ha': [0,1500,0,1500],
    'Hb': [0,1500,1501,-1],
    '7774': [1500,-1,0,1560],
    '6300': [1500,-1,1561,2060],
    '5577': [1500,-1,2060, 2580],
    '4278': [1500,-1,2580,-1],
} 

def read_raw_img(fn:Path|str, pixdict:dict|None = None, PILimg = False):
    if isinstance(fn, str):
        fn = Path(fn)
    #open fits file and read data
    with fits.open(fn) as hdul:
        if len(hdul) > 1: idx = 1
        else: idx = 0
        data = hdul[idx].data # type:ignore
        data = np.clip(data, np.percentile(data,1), np.percentile(data,99.99))

        #normalize by panel if pixdict is provided
        if pixdict is not None: 
            normdata = np.full(data.shape, np.nan)

            for key,lims in pixdict.items():
                x1, x2, y1, y2 = lims
                dat = data[x1:x2, y1:y2]
                dat -= np.nanmin(dat)
                dat /= (np.nanmax(dat)-np.nanmin(dat))
                normdata[x1:x2, y1:y2] = dat
            data = normdata
        if PILimg:#convert to PIL image
            img = Image.fromarray(data*255)
            return img
        else:
            return data

def misdesigner_model_init(plot:bool = False):
    SYSTEM = 'HMSAO-V2' #hit&mis A origin Version 2
    SLIT_WIDTH = 200
    SLIT_TO_EDGE = -5.93  # -3.55 -> -70.8 (α)
    EDGE_TO_MOSAIC = -2.3
    MOSAIC_WIDTH = 52.5
    MOSAIC_HEIGHT = 58.98
    MOSAIC_X0 = SLIT_TO_EDGE + EDGE_TO_MOSAIC
    MOSAIC_X1 = MOSAIC_X0 - MOSAIC_WIDTH
    slit_height = 66.5
    FL1 = 409
    FL2 = 414
    ALPHA = 71.1
    GAMMA = -0.2
    # CAMSCALE = 65.25

    slits = {
            'BL': MisSlit(29, -slit_height / 4, SLIT_WIDTH*1e-3, slit_height / 2, ranges=[(3150, 4450)]),
            'BR': MisSlit(0, -slit_height / 4, SLIT_WIDTH*1e-3, slit_height / 2, ranges=[(4950, np.inf)]),
            'TL': MisSlit(29, slit_height / 4, SLIT_WIDTH*1e-3, slit_height / 2, ranges=[(5900, np.inf)]),
            'TR': MisSlit(0, slit_height / 4, SLIT_WIDTH*1e-3, slit_height / 2, ranges=[(4350, 5000)]),
            }
    mosaic =  MisMosaic(
        x = (MOSAIC_X0 + MOSAIC_X1)*0.5, 
        y = (-1.8+2.5),
        width = MOSAIC_WIDTH,
        height = MOSAIC_HEIGHT,
        windows = [
            # Hβ, 20nm around 4861
            MisMosaicFilter(0, 1.8, 24.63, 26.96, [(4860-50, 4861+50)], name='4861'),
            # Hα, 20nm around 6563
            MisMosaicFilter(24.63, 1.8, 27.57 - 2.68, 26.96, [(6510, 6600)], name='6563'), #true range is 6563-100 -> 6563 +100. Changed here for convience. 
            # OI, 10nm around 4300
            MisMosaicFilter(0, 26.96 + 1.8, 8.13, 27.72, [(4300-50, 4300+50)], name='4278'),
            # OI, 10nm around 5580
            #  MisMosaicFilter(8.13, 26.96 + 1.8, 8, 27.72, [(5500-125, 5500+125)], name='5577'),
            MisMosaicFilter(8.13, 26.96 + 1.8, 8, 27.72, [(5500, 5600)], name='5577'),
            # OI, 10nm around 6300
            MisMosaicFilter(8.13 + 8, 26.96 + 1.8, 7.5, 27.72, [(6320-50, 6320+50)], name='6300'),
            # N2+, 10nm around 7750
            MisMosaicFilter(8.13 + 8 + 7.5, 26.96 + 1.8, 28.57 - 2.68, 27.72, [(7750-125, 7750+125)], name='7774'),     
                ]
            )
    grat = MisConfig(fl_collimator=FL1, 
                    fl_mosaic=FL2,
                    sigma=98.76,
                    slits=slits,
                    mosaic=mosaic
                    )
    model = MisInstrumentModel(SYSTEM, grat, gamma_ofst=GAMMA, alpha=-ALPHA)
    if plot:
        fig, ax = model.plot_lines([
            MisFeatures(6300, plot_styles={'color': 'red'}),
            MisFeatures(5577, plot_styles={'color': 'green'}),
            MisFeatures(7774, plot_styles={'color': 'brown'}),
            MisFeatures(4278, plot_styles={'color': 'violet'}),
            MisFeatures(6563, plot_styles={'color': 'orange'}),
            MisFeatures(4861, plot_styles={'color': 'cyan'}),
            # 7821, 7841, 6522, 6568, 7808, 7860
        ],
            fig_kwargs={'figsize': (6.4, 5.6), 'dpi': 300})
        
    camera = MisCamera(
        aperture=np.pi*9*9, # 9mm radius
        scale = 1, # 
        pixel_size= 1/CAMSCALE, # um
        exposure=1, # s
        )
    model.set_camera(camera)
    mmap = model.mosaic_map(unique=True)
    return model, mmap
#%%
#initalize model and get mosaic map
model,mmap = misdesigner_model_init()

#process image and rotate to align with model
img = read_raw_img(fn, pixdict, PILimg = True)   
img = img.rotate(-.19, resample = Image.Resampling.BILINEAR, fillcolor = np.nan)
img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

# CAMSCALE = 65.25
width,height = mmap.wavelength.shape[::-1]
fullimg = Image.new('F', mmap.wavelength.shape[::-1], color=np.nan)
fullimg.paste(img, (110,410))
# %%
#plot
fig, ax = model.plot_lines([

        ############### ROI: Red ##########################################
        MisFeatures(6300, plot_styles={'color': 'red','ls': '-.','lw': 0.1,'ms': 0.2}),

        ############### ROI: Green ##########################################
        MisFeatures(5577, plot_styles={'color': 'green','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(5586, plot_styles={'color': 'green','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(5590, plot_styles={'color': 'green','ls': '-.','lw': 0.1,'ms': 0.2}),

        ############### ROI: Blue ##########################################
        MisFeatures(4278, plot_styles={'color': 'blue','ls': '-.','lw': 0.1,'ms': 0.2}),

        ############### ROI: Ha ##########################################
        MisFeatures(6546, plot_styles={'color': 'orange','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(6563, plot_styles={'color': 'orange','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(6569, plot_styles={'color': 'orange','ls': '-.','lw': 0.1,'ms': 0.2}),


        ############### ROI: Hb ##########################################
        MisFeatures(4861, plot_styles={'color': 'cyan','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(4855, plot_styles={'color': 'cyan','ls': '-.','lw': 0.1,'ms': 0.2}),


        ############### ROI: 7774 ##########################################
        MisFeatures(7774, plot_styles={'color': 'purple','ls': '-.','lw': 0.1,'ms': 0.2}),
  
        MisFeatures(7780, plot_styles={'color': 'pink','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(7788, plot_styles={'color': 'pink','ls': '-.','lw': 0.1,'ms': 0.2}),

        #last 4th doublet from the left
        MisFeatures(7797, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(7801, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.2}),

        #third doublet from the left
        MisFeatures(7807, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.2}),
        MisFeatures(7810, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.2}),

        #second doublet from the left
        MisFeatures(7832, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.1}),
        MisFeatures(7836, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.1}),

        #first doublet from the left
        MisFeatures(7849, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.1}),
        MisFeatures(7855, plot_styles={'color': 'yellow','ls': '-.','lw': 0.1,'ms': 0.1}),

    ],
        fig_kwargs={'figsize': (6.4, 5.6), 'dpi': 300})
ax.imshow(np.asarray(fullimg), origin='lower', extent=(0, -width/CAMSCALE, 0, height/CAMSCALE),
          aspect='equal',cmap = 'grey')


fig.savefig('misdesigner_fit.png', dpi=300)
# %%
model.store('model_HMSAO-v2.JSON')
# %%
