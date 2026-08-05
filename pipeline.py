"""
EditFlow Pipeline
--------------------
Chains multiple tools together into one pass, instead of running each
tool separately by hand:

    1. Remove silences (tightens the footage)
    2. Detect scene changes (for reference/reporting)
    3. Generate thumbnail candidates from the trimmed video
    4. Generate captions for the trimmed video

Returns a single result dict with everything the dashboard needs to
display, plus the path to the final trimmed video.
"""

import os
import tempfile

from modules import silence_detector, scene_detector, thumbnail_generator


def run_pipeline(video_path, output_dir, silence_thresh_db=-35, min_silence_len=0.6,
                  generate_captions=False, caption_model="base",
                  resolution="Original", quality="Standard", progress_callback=None):
    """
    Runs the full EditFlow pipeline on a single video.

    progress_callback: optional function(step_name: str, fraction: float)
        called as each stage completes, so the UI can show a progress bar.

    Returns a dict:
        {
            "trimmed_video_path": str,
            "silences_removed": [...],
            "scene_changes": [...],
            "thumbnails": [...],
            "captions": [...] or None,
            "captions_srt_path": str or None,
        }
    """
    os.makedirs(output_dir, exist_ok=True)

    def report(step, frac):
        if progress_callback:
            progress_callback(step, frac)

    # Step 1: find + remove silences
    report("Detecting silences...", 0.1)
    silences = silence_detector.find_silences(
        video_path, silence_thresh_db=silence_thresh_db, min_silence_len=min_silence_len
    )

    report("Trimming silent segments...", 0.3)
    trimmed_path = os.path.join(output_dir, "pipeline_trimmed.mp4")
    if silences:
        silence_detector.build_trimmed_clip(video_path, silences, trimmed_path,
                                             resolution=resolution, quality=quality)
    else:
        # nothing to trim — just carry the original path through unchanged
        trimmed_path = video_path

    # Step 2: scene changes (reported against the trimmed video)
    report("Detecting scene changes...", 0.5)
    scenes = scene_detector.detect_scene_changes(trimmed_path)

    # Step 3: thumbnails
    report("Generating thumbnails...", 0.7)
    thumb_dir = os.path.join(output_dir, "thumbnails")
    thumbs = thumbnail_generator.generate_thumbnails(trimmed_path, thumb_dir, num_candidates=5)

    # Step 4: captions (optional — slowest step)
    captions_result = None
    srt_path = None
    if generate_captions:
        report("Transcribing captions (this can take a while)...", 0.85)
        from modules import captions as captions_module
        srt_path = os.path.join(output_dir, "pipeline_captions.srt")
        captions_result = captions_module.generate_captions(trimmed_path, srt_path, model_size=caption_model)

    report("Done", 1.0)

    return {
        "trimmed_video_path": trimmed_path,
        "silences_removed": silences,
        "scene_changes": scenes,
        "thumbnails": thumbs,
        "captions": captions_result,
        "captions_srt_path": srt_path,
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    out_dir = tempfile.mkdtemp()

    def cb(step, frac):
        print(f"[{frac*100:5.1f}%] {step}")

    result = run_pipeline(path, out_dir, progress_callback=cb)
    print("\nTrimmed video:", result["trimmed_video_path"])
    print("Silences removed:", len(result["silences_removed"]))
    print("Scene changes:", len(result["scene_changes"]))
    print("Thumbnails:", len(result["thumbnails"]))
