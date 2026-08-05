"""
Batch Rename & Organize
-------------------------
Takes a folder of raw camera footage (DSC001.mp4, DSC002.mp4, ...) and
renames + sorts it into date-based folders using each file's creation
date — so nothing has to be organized by hand before an edit.
"""

import os
import glob
import shutil
import subprocess
from datetime import datetime


def get_creation_date(video_path):
    """Reads the creation_time tag from a video's metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags=creation_time",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    raw = result.stdout.strip()

    if raw:
        try:
            return datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

    # Fall back to the file's filesystem modified time if no metadata tag exists
    return datetime.fromtimestamp(os.path.getmtime(video_path))


def organize_footage(folder_path, output_dir, project_name="clip"):
    """
    Renames and sorts every video in folder_path into
    output_dir/YYYY-MM-DD/ subfolders, named sequentially.

    Returns a list of (original_path, new_path) tuples.
    """
    os.makedirs(output_dir, exist_ok=True)
    videos = sorted(
        glob.glob(os.path.join(folder_path, "*.mp4")) +
        glob.glob(os.path.join(folder_path, "*.mov"))
    )

    counters = {}
    moved = []

    for v in videos:
        date = get_creation_date(v)
        date_str = date.strftime("%Y-%m-%d")
        day_folder = os.path.join(output_dir, date_str)
        os.makedirs(day_folder, exist_ok=True)

        counters[date_str] = counters.get(date_str, 0) + 1
        seq = counters[date_str]
        ext = os.path.splitext(v)[1]
        new_name = f"{project_name}_{date_str}_{seq:03d}{ext}"
        new_path = os.path.join(day_folder, new_name)

        shutil.copy2(v, new_path)
        moved.append((v, new_path))

    return moved


if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "test_assets"
    results = organize_footage(folder, "test_assets/organized", project_name="shoot")
    for old, new in results:
        print(f"{old}  ->  {new}")
