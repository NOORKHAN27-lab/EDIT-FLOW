"""
Color Grading Preset Applier
------------------------------
Applies a consistent color grade across a whole folder of clips in one
batch, using ffmpeg's built-in curve/eq filters (no external LUT file
needed) — useful for keeping footage from different cameras or shoots
looking consistent before they're cut together.
"""

import os
import glob
import subprocess
from modules.export_settings import target_height, crf_for

# A few ready-made "looks" built from ffmpeg's eq/curves filters.
# Feel free to tweak these numbers or add your own presets.
PRESETS = {
    "warm": "eq=contrast=1.08:saturation=1.15:gamma_r=1.05:gamma_b=0.95",
    "cool": "eq=contrast=1.05:saturation=1.05:gamma_b=1.08:gamma_r=0.95",
    "cinematic": "eq=contrast=1.15:saturation=0.9:brightness=-0.02,curves=preset=darker",
    "vibrant": "eq=contrast=1.1:saturation=1.35:brightness=0.02",
    "muted": "eq=contrast=0.95:saturation=0.75:brightness=0.01",
}


def apply_grade(video_path, output_path, preset="cinematic", resolution="Original", quality="Standard"):
    """Applies one of the built-in color presets to a single video."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {list(PRESETS)}")

    vf = PRESETS[preset]
    h = target_height(resolution)
    if h:
        # Only ever downscale — an explicit height check avoids upscaling
        # small source footage past its native resolution.
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=height", "-of", "csv=p=0", video_path],
            capture_output=True, text=True
        )
        try:
            src_height = int(probe.stdout.strip())
        except ValueError:
            src_height = 0
        if src_height > h:
            vf = f"scale=-2:{h}," + vf

    crf = crf_for(quality)
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-c:a", "copy",
        output_path,
        "-loglevel", "error",
    ]
    subprocess.run(cmd, check=True)
    return output_path


def batch_apply_grade(folder_path, output_dir, preset="cinematic"):
    """Applies the same color grade to every video in a folder."""
    os.makedirs(output_dir, exist_ok=True)
    videos = glob.glob(os.path.join(folder_path, "*.mp4"))

    results = []
    for v in videos:
        name = os.path.splitext(os.path.basename(v))[0]
        out_path = os.path.join(output_dir, f"{name}_{preset}.mp4")
        apply_grade(v, out_path, preset)
        results.append(out_path)
    return results


if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    preset = sys.argv[2] if len(sys.argv) > 2 else "cinematic"
    out = apply_grade(video, f"test_assets/graded_{preset}.mp4", preset)
    print(f"Graded video ({preset}) saved to: {out}")
