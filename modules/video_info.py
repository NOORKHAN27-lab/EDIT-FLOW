"""
Video Info Report
------------------
Scans a folder of footage and produces a summary table: duration,
resolution, codec, fps, and file size for every clip — so you know
how much footage you're working with before you start cutting.
"""

import os
import glob
import subprocess
import json


def get_video_metadata(video_path):
    """Uses ffprobe to pull technical metadata from a single video file."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate",
        "-show_entries", "format=duration,size",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})

    fps_raw = stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else 0
    except Exception:
        fps = 0

    size_bytes = int(fmt.get("size", 0))

    return {
        "file": os.path.basename(video_path),
        "duration_sec": round(float(fmt.get("duration", 0)), 2),
        "resolution": f"{stream.get('width', '?')}x{stream.get('height', '?')}",
        "codec": stream.get("codec_name", "unknown"),
        "fps": fps,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }


def generate_report(folder_path):
    """Returns metadata for every video file in a folder, plus totals."""
    videos = glob.glob(os.path.join(folder_path, "*.mp4")) + \
             glob.glob(os.path.join(folder_path, "*.mov")) + \
             glob.glob(os.path.join(folder_path, "*.avi"))

    rows = [get_video_metadata(v) for v in sorted(videos)]

    totals = {
        "clip_count": len(rows),
        "total_duration_sec": round(sum(r["duration_sec"] for r in rows), 2),
        "total_size_mb": round(sum(r["size_mb"] for r in rows), 2),
    }
    return rows, totals


if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "test_assets"
    rows, totals = generate_report(folder)
    for r in rows:
        print(r)
    print("\nTotals:", totals)
