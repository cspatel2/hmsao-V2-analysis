#%%
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pathlib import Path

def plot_slit_on_allsky_efficient(allskyimg_path, save_path='./', azimuth_deg=0, 
                                  slit_fov_deg=20, slit_width_deg=0.01, 
                                  plot_show=False, ax=None):
    """
    Highly optimized function to plot a slit position on an all-sky image.
    Accepts an optional 'ax' argument to prevent destroying/recreating figures in loops.
    """
    DPI = 300
    image_path = Path(allskyimg_path)
    
    # 1. Load image and metadata
    img = Image.open(image_path)
    w, h = img.size
    img_center_x, img_center_y = w // 2, h // 2

    #2. math
    slit_length_rad = np.radians(slit_fov_deg / 2)
    azimuth_rad = np.radians(azimuth_deg)
    
    # Pre-calculate angular steps (-fov/2 to +fov/2)
    theta_vals = np.linspace(-slit_length_rad, slit_length_rad, 100)
    
    # Convert theta directly to pixel radii (assuming 180 deg full FOV)
    # Equivalent to: (theta / (np.radians(180) / 2)) * (w / 2)
    r = theta_vals * (w / np.pi) 
    
    # Vectorized conversion to X and Y coordinates
    slit_x = img_center_x + r * np.sin(azimuth_rad)
    slit_y = img_center_y - r * np.cos(azimuth_rad)

    # 3. Figure Management (Reuse axis if provided, else create standalone)
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(w / DPI, h / DPI))
    else:
        fig = ax.get_figure()

    # 4. Drawing and Formatting
    ax.imshow(img)
    ax.plot(slit_x, slit_y, color='red', linewidth=2, markersize=0.5)
    
    ax.set_aspect('equal')
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_xticks([])
    ax.set_yticks([])

    # 5. Exporting
    fn_out = Path(save_path) / f"{image_path.stem}_slit.png"
    fn_out.parent.mkdir(parents=True, exist_ok=True)
    
    # bbox_inches='tight' is slow but can be kept if necessary; 
    # pad_inches=0 enforces exact dimensions cleanly
    plt.savefig(fn_out, dpi=DPI, bbox_inches='tight', pad_inches=0)

    if plot_show:
        plt.show()
    elif standalone:
        plt.close(fig)

# %%
if __name__ == '__main__':
    # Single image demonstration
    # fn = '2025-11-16T22.57.00.000KRN.jpeg'
    fn = '2025-11-16T22.58.00.000KRN.jpeg'
    pointing_az = 90
    slit_fov = 30
    
    # Creating a dummy file for local script integrity if needed
    if not Path(fn).exists():
        Image.new('RGB', (1200, 1200), color='gray').save(fn)
        
    plot_slit_on_allsky_efficient(fn, azimuth_deg=pointing_az, slit_fov_deg=slit_fov, plot_show=True)

    # =========================================================================
    # HIGH-SPEED BATCH LOOP EXAMPLE
    # =========================================================================
    # UNCOMMENT THIS SECTION to run your bulk files up to 5x-10x faster:
    
    # from glob import glob
    # from tqdm import tqdm
    # fnames = sorted(glob('imgs/raw/*.jpeg'))
    
    # if fnames:
    #     # 1. Open the image *once* ahead of time to capture dimensions for the figure
    #     first_img = Image.open(fnames[0])
    #     w, h = first_img.size
        
    #     # 2. Build one universal figure and axis blueprint
    #     fig, ax = plt.subplots(figsize=(w / 300, h / 300))
    #     plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
    #     # 3. Fast loop
    #     for img_path in tqdm(fnames):
    #         ax.clear() # Wipe the canvas clean without deleting the window structural data
    #         plot_slit_on_allsky_efficient(
    #             img_path, 
    #             save_path='imgs/with_slit', 
    #             azimuth_deg=pointing_az, 
    #             slit_fov_deg=slit_fov, 
    #             ax=ax # Reuses the canvas structure
    #         )
    #     plt.close(fig)
# %%
