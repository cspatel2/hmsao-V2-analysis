#%%
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:  # interactive (#%%) session
    BASE_DIR = Path.cwd()

RAW_DIR = BASE_DIR / 'plots' / 'raw'
OUT_DIR = BASE_DIR / 'plots' / 'slit_proj'
IMG_EXTS = ('.jpeg', '.jpg', '.png')

# Output naming convention. Available fields: stem (input filename without
# extension), az (azimuth, deg), fov (slit FOV, deg).
# e.g. 2025-11-16T22.58.00.000KRN_slit_az180_fov30.png
NAME_TEMPLATE = '{stem}_slit_az{az:03g}_fov{fov:02g}.png'


def output_name(image_path, azimuth_deg, slit_fov_deg, template=NAME_TEMPLATE):
    return template.format(stem=Path(image_path).stem,
                           az=azimuth_deg, fov=slit_fov_deg)


def slit_endpoints(w, h, azimuth_deg, slit_fov_deg, x_offset_px=0, y_offset_px=0):
    """Pixel endpoints of the slit (a straight line through the slit center).

    Assumes an equidistant fisheye with 180 deg FOV spanning the image width,
    so pixel radius r = theta * (w / pi).
    The slit center is the image center shifted by (x_offset_px, y_offset_px),
    in image pixel coordinates: +x = right, +y = down.
    """
    cx, cy = w / 2 + x_offset_px, h / 2 + y_offset_px
    r = np.radians(slit_fov_deg / 2) * (w / np.pi)
    az = np.radians(azimuth_deg)
    dx, dy = r * np.sin(az), -r * np.cos(az)
    return (cx - dx, cy - dy), (cx + dx, cy + dy)


def plot_slit_on_allsky_efficient(allskyimg_path, save_path=OUT_DIR, azimuth_deg=90,
                                  slit_fov_deg=20, x_offset_px=0, y_offset_px=0,
                                  linewidth_px=2, color='red',
                                  plot_show=False, compress_level=1,
                                  name_template=NAME_TEMPLATE, overwrite=True):
    """Draw the slit position on an all-sky image and save it as PNG.

    Draws directly onto the image with PIL (no matplotlib figure), so the
    output keeps the original resolution and is much faster to produce.
    x_offset_px, y_offset_px: shift of the slit center from the image center,
    in pixels (+x = right, +y = down).
    compress_level: PNG zlib level 0-9 (1 = fast, slightly larger files).
    overwrite=False skips images whose output file already exists.
    Returns the output path.
    """
    image_path = Path(allskyimg_path)
    fn_out = Path(save_path) / output_name(image_path, azimuth_deg,
                                           slit_fov_deg, name_template)
    if fn_out.exists() and not overwrite and not plot_show:
        return fn_out

    with Image.open(image_path) as im:
        img = im.convert('RGB')
    w, h = img.size

    p0, p1 = slit_endpoints(w, h, azimuth_deg, slit_fov_deg,
                            x_offset_px, y_offset_px)
    ImageDraw.Draw(img).line([p0, p1], fill=color, width=linewidth_px)

    fn_out.parent.mkdir(parents=True, exist_ok=True)
    img.save(fn_out, compress_level=compress_level)

    if plot_show:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(img)
        ax.set_axis_off()
        plt.show()

    return fn_out


def plot_slit_batch(fnames, save_path=OUT_DIR, max_workers=None, **kwargs):
    """Process many images in parallel. kwargs go to plot_slit_on_allsky_efficient."""
    func = partial(plot_slit_on_allsky_efficient, save_path=save_path,
                   plot_show=False, **kwargs)
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(func, fnames, chunksize=4))


def run_all(raw_dir=RAW_DIR, out_dir=OUT_DIR, **kwargs):
    """Draw the slit on every image in raw_dir and save to out_dir."""
    fnames = sorted(p for p in Path(raw_dir).iterdir()
                    if p.suffix.lower() in IMG_EXTS)
    if not fnames:
        print(f'No images found in {raw_dir}')
        return []
    out = plot_slit_batch(fnames, out_dir, **kwargs)
    print(f'Saved {len(out)} images to {out_dir}')
    return out


# %%
if __name__ == '__main__':
    pointing_az = 180
    slit_fov = 30
    x_offset = 0  # px, +right
    y_offset = 20  # px, +down

    run_all(azimuth_deg=pointing_az, slit_fov_deg=slit_fov,
            x_offset_px=x_offset, y_offset_px=y_offset)

    # Single image with preview:
    # plot_slit_on_allsky_efficient(RAW_DIR / '2025-11-16T22.58.00.000KRN.jpeg',
    #                               azimuth_deg=pointing_az,
    #                               slit_fov_deg=slit_fov, plot_show=True)
# %%
