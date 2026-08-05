"""
Export Settings
-----------------
Shared resolution/quality presets used across every tool that renders
a video, so the whole app has one consistent set of export options
instead of each module inventing its own.
"""

RESOLUTIONS = {
    "Original": None,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
}

# Maps a friendly quality label to an ffmpeg/moviepy-style CRF value.
# Lower CRF = higher quality + bigger file. 18 is visually lossless-ish,
# 28 is noticeably compressed but small.
QUALITY_PRESETS = {
    "High quality": 18,
    "Standard": 23,
    "Compressed (smaller file)": 28,
}


def target_height(resolution_label):
    """Returns the target pixel height for a resolution label, or None for 'Original'."""
    return RESOLUTIONS.get(resolution_label)


def crf_for(quality_label):
    """Returns the ffmpeg CRF value for a quality label."""
    return QUALITY_PRESETS.get(quality_label, 23)


def moviepy_write_kwargs(quality_label):
    """
    ffmpeg_params to pass into moviepy's write_videofile() for a given
    quality preset.
    """
    crf = crf_for(quality_label)
    return {"ffmpeg_params": ["-crf", str(crf)]}
