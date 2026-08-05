"""
Batch Watermark / Logo Overlay
--------------------------------
Applies a logo or watermark image to every video in a folder in one
pass, instead of dragging it onto each timeline in Premiere one by one.
"""

import os
import glob
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
from modules.export_settings import target_height, moviepy_write_kwargs

POSITIONS = {
    "bottom-right": ("right", "bottom"),
    "bottom-left": ("left", "bottom"),
    "top-right": ("right", "top"),
    "top-left": ("left", "top"),
    "center": ("center", "center"),
}


def apply_watermark(video_path, watermark_path, output_path,
                     position="bottom-right", opacity=0.7, scale=0.15, margin=20,
                     resolution="Original", quality="Standard"):
    """
    Overlays `watermark_path` (a PNG, ideally with transparency) onto
    `video_path` and writes the result to `output_path`.

    scale: watermark width as a fraction of video width (e.g. 0.15 = 15%)
    margin: pixel padding from the chosen corner
    resolution / quality: export settings labels from modules.export_settings
    """
    video = VideoFileClip(video_path)

    h = target_height(resolution)
    if h and video.h > h:
        video = video.resized(height=h)

    logo = (ImageClip(watermark_path)
            .with_duration(video.duration)
            .resized(width=int(video.w * scale)))

    logo = logo.with_opacity(opacity)

    pos = POSITIONS.get(position, ("right", "bottom"))
    # Convert named position + margin into an explicit (x, y) so margins apply
    x = margin if pos[0] == "left" else (video.w - logo.w - margin if pos[0] == "right" else "center")
    y = margin if pos[1] == "top" else (video.h - logo.h - margin if pos[1] == "bottom" else "center")
    logo = logo.with_position((x, y))

    final = CompositeVideoClip([video, logo])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None,
                           **moviepy_write_kwargs(quality))

    video.close()
    final.close()
    return output_path


def batch_apply_watermark(folder_path, watermark_path, output_dir, **kwargs):
    """Applies the same watermark to every .mp4/.mov file in a folder."""
    os.makedirs(output_dir, exist_ok=True)
    videos = glob.glob(os.path.join(folder_path, "*.mp4")) + \
             glob.glob(os.path.join(folder_path, "*.mov"))

    results = []
    for v in videos:
        name = os.path.splitext(os.path.basename(v))[0]
        out_path = os.path.join(output_dir, f"{name}_watermarked.mp4")
        apply_watermark(v, watermark_path, out_path, **kwargs)
        results.append(out_path)
    return results


if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    logo = sys.argv[2] if len(sys.argv) > 2 else "test_assets/logo.png"
    out = apply_watermark(video, logo, "test_assets/watermarked_output.mp4")
    print(f"Watermarked video saved to: {out}")
