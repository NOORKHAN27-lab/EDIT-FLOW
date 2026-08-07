"""
Image Tools
-------------
The image-editing counterpart to the video tools: watermarking, color
filters, batch resize/format conversion, background removal, and merging
two people (each cut out from their own photo) onto a chosen background.

Background removal and the people-merge tool use `rembg`, which downloads
a small pretrained segmentation model (~176MB) the first time it runs —
same one-time-download pattern as the Whisper captions model.
"""

import os
import glob
from PIL import Image, ImageEnhance


def _flatten_to_rgb(img, bg_color=(255, 255, 255)):
    """
    Converts any image to RGB, properly compositing transparency onto a
    solid background first. A raw .convert("RGB") on an RGBA image just
    drops the alpha channel and keeps whatever garbage RGB values sit
    underneath it (often rendering as black or noisy patches) — this
    flattens onto a real background color instead, the way it visually looks.
    """
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        solid = Image.new("RGB", img.size, bg_color)
        solid.paste(img, mask=img.split()[3])
        return solid
    return img.convert("RGB")

# ---------------------------------------------------------------------------
# Watermark / logo overlay
# ---------------------------------------------------------------------------
POSITIONS = {
    "bottom-right": ("right", "bottom"),
    "bottom-left": ("left", "bottom"),
    "top-right": ("right", "top"),
    "top-left": ("left", "top"),
    "center": ("center", "center"),
}


def apply_watermark(image_path, watermark_path, output_path,
                     position="bottom-right", opacity=0.7, scale=0.15, margin=20):
    """Overlays a logo (ideally a transparent PNG) onto an image."""
    base = Image.open(image_path).convert("RGBA")
    logo = Image.open(watermark_path).convert("RGBA")

    logo_w = int(base.width * scale)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((max(logo_w, 1), max(logo_h, 1)))

    if opacity < 1.0:
        alpha = logo.split()[3].point(lambda p: int(p * opacity))
        logo.putalpha(alpha)

    pos_x, pos_y = POSITIONS.get(position, ("right", "bottom"))
    x = margin if pos_x == "left" else (base.width - logo.width - margin if pos_x == "right" else (base.width - logo.width) // 2)
    y = margin if pos_y == "top" else (base.height - logo.height - margin if pos_y == "bottom" else (base.height - logo.height) // 2)

    composited = Image.new("RGBA", base.size)
    composited.paste(base, (0, 0))
    composited.paste(logo, (x, y), logo)

    if os.path.splitext(output_path)[1].lower() == ".png":
        composited.save(output_path)
    else:
        _flatten_to_rgb(composited).save(output_path, quality=95)
    return output_path


def batch_apply_watermark(folder_path, watermark_path, output_dir, **kwargs):
    os.makedirs(output_dir, exist_ok=True)
    images = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.jpeg")) + \
        glob.glob(os.path.join(folder_path, "*.png"))
    results = []
    for img in images:
        name = os.path.splitext(os.path.basename(img))[0]
        out_path = os.path.join(output_dir, f"{name}_watermarked.jpg")
        apply_watermark(img, watermark_path, out_path, **kwargs)
        results.append(out_path)
    return results


# ---------------------------------------------------------------------------
# Color grading / filter presets
# ---------------------------------------------------------------------------
PRESETS = {
    "warm": {"color": 1.2, "contrast": 1.05, "brightness": 1.03, "warmth": 15},
    "cool": {"color": 0.9, "contrast": 1.05, "brightness": 1.0, "warmth": -15},
    "cinematic": {"color": 0.85, "contrast": 1.2, "brightness": 0.95, "warmth": -5},
    "vibrant": {"color": 1.4, "contrast": 1.15, "brightness": 1.05, "warmth": 5},
    "muted": {"color": 0.7, "contrast": 0.92, "brightness": 1.02, "warmth": 0},
    "black_and_white": {"color": 0.0, "contrast": 1.1, "brightness": 1.0, "warmth": 0},
}


def _shift_warmth(img, amount):
    """Small red/blue channel push for a warmer or cooler look."""
    if amount == 0:
        return img
    r, g, b = img.split()
    r = r.point(lambda p: min(255, max(0, p + amount)))
    b = b.point(lambda p: min(255, max(0, p - amount)))
    return Image.merge("RGB", (r, g, b))


def apply_filter(image_path, output_path, preset="cinematic"):
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {list(PRESETS)}")
    settings = PRESETS[preset]
    img = Image.open(image_path)
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    save_as_png = os.path.splitext(output_path)[1].lower() == ".png"

    if has_alpha:
        img = img.convert("RGBA")
        alpha = img.split()[3]
        # If we're about to reattach this alpha channel (saving as PNG), the
        # underlying RGB values under transparent pixels don't matter — they
        # get hidden again. Only flatten onto white when alpha is being
        # dropped for good (saving to a format with no transparency support).
        rgb = img.convert("RGB") if save_as_png else _flatten_to_rgb(img)
    else:
        rgb = img.convert("RGB")

    rgb = ImageEnhance.Color(rgb).enhance(settings["color"])
    rgb = ImageEnhance.Contrast(rgb).enhance(settings["contrast"])
    rgb = ImageEnhance.Brightness(rgb).enhance(settings["brightness"])
    rgb = _shift_warmth(rgb, settings["warmth"])

    if has_alpha and save_as_png:
        result = rgb.convert("RGBA")
        result.putalpha(alpha)
        result.save(output_path)
    else:
        rgb.save(output_path, quality=95)
    return output_path


def batch_apply_filter(folder_path, output_dir, preset="cinematic"):
    os.makedirs(output_dir, exist_ok=True)
    images = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.jpeg")) + \
        glob.glob(os.path.join(folder_path, "*.png"))
    results = []
    for img in images:
        name = os.path.splitext(os.path.basename(img))[0]
        out_path = os.path.join(output_dir, f"{name}_{preset}.jpg")
        apply_filter(img, out_path, preset)
        results.append(out_path)
    return results


# ---------------------------------------------------------------------------
# Batch resize & format conversion
# ---------------------------------------------------------------------------
FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def resize_and_convert(image_path, output_path, width=None, height=None, fmt="JPEG", keep_aspect=True):
    img = Image.open(image_path)
    if fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
        img = _flatten_to_rgb(img)

    if width or height:
        if keep_aspect:
            img.thumbnail((width or 100000, height or 100000))
        else:
            img = img.resize((width or img.width, height or img.height))

    img.save(output_path, fmt)
    return output_path


def batch_resize_convert(folder_path, output_dir, width=None, height=None, fmt="JPEG", keep_aspect=True):
    os.makedirs(output_dir, exist_ok=True)
    images = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.jpeg")) + \
        glob.glob(os.path.join(folder_path, "*.png")) + glob.glob(os.path.join(folder_path, "*.webp"))
    results = []
    ext = FORMATS.get(fmt, ".jpg")
    for img in images:
        name = os.path.splitext(os.path.basename(img))[0]
        out_path = os.path.join(output_dir, f"{name}{ext}")
        resize_and_convert(img, out_path, width, height, fmt, keep_aspect)
        results.append(out_path)
    return results


# ---------------------------------------------------------------------------
# Background removal (rembg — downloads a small model on first use)
# ---------------------------------------------------------------------------
def remove_background(image_path, output_path):
    """Removes the background, saving a transparent PNG. Returns output_path."""
    from rembg import remove
    with open(image_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open(output_path, "wb") as f:
        f.write(output_bytes)
    return output_path


# ---------------------------------------------------------------------------
# Merge two people (each cut out from their own photo) onto a chosen background
# ---------------------------------------------------------------------------
def merge_people_onto_background(person_a_path, person_b_path, background_path, output_path,
                                  scale_a=0.5, x_a=0.25, y_a=0.6,
                                  scale_b=0.5, x_b=0.75, y_b=0.6):
    """
    Cuts each person out of their own photo (background removal), then
    composites both onto the chosen background image.

    scale_* is the cutout's height as a fraction of the background's height.
    x_*/y_* are the cutout's center position as a fraction of the
    background's width/height (0,0 = top-left, 1,1 = bottom-right).
    """
    from rembg import remove

    bg = Image.open(background_path).convert("RGBA")

    def _cutout(person_path):
        with open(person_path, "rb") as f:
            raw = f.read()
        cut_bytes = remove(raw)
        import io as _io
        return Image.open(_io.BytesIO(cut_bytes)).convert("RGBA")

    def _place(canvas, cutout, scale, x_frac, y_frac):
        target_h = int(bg.height * scale)
        target_w = int(cutout.width * (target_h / cutout.height))
        cutout = cutout.resize((max(target_w, 1), max(target_h, 1)))
        cx = int(bg.width * x_frac - cutout.width / 2)
        cy = int(bg.height * y_frac - cutout.height / 2)
        canvas.paste(cutout, (cx, cy), cutout)
        return canvas

    canvas = bg.copy()
    cutout_a = _cutout(person_a_path)
    cutout_b = _cutout(person_b_path)
    canvas = _place(canvas, cutout_a, scale_a, x_a, y_a)
    canvas = _place(canvas, cutout_b, scale_b, x_b, y_b)

    canvas.convert("RGB").save(output_path, quality=95)
    return output_path
