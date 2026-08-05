"""
Silence / Jump-Cut Detector
----------------------------
Scans a video's audio track and finds segments where the volume drops
below a threshold for longer than a minimum duration — the classic
"dead air" you'd normally scrub through manually to trim out.

Returns a list of (start, end) timestamps (in seconds) that are safe
to cut, plus a ready-to-use ffmpeg filter string if you want to
actually produce a trimmed video.
"""

import numpy as np
from moviepy import VideoFileClip, concatenate_videoclips


def analyze_audio(video_path, frame_rate=50):
    """
    Samples the audio volume across the whole clip. Returns (times, volumes_db, duration).
    Shared by find_silences() and the waveform visualizer so both work off
    the exact same data.
    """
    clip = VideoFileClip(video_path)
    if clip.audio is None:
        clip.close()
        return np.array([]), np.array([]), 0

    audio = clip.audio
    duration = clip.duration
    times = np.arange(0, duration, 1.0 / frame_rate)
    volumes = []
    for t in times:
        try:
            frame = audio.get_frame(t)
            rms = np.sqrt(np.mean(np.square(frame)))
            db = 20 * np.log10(max(rms, 1e-6))
            volumes.append(db)
        except Exception:
            volumes.append(-100)
    clip.close()
    return times, np.array(volumes), duration


def find_silences(video_path, silence_thresh_db=-35, min_silence_len=0.6, frame_rate=50):
    """
    Detects silent segments in a video's audio track.

    Args:
        video_path: path to the video file
        silence_thresh_db: volume (in dBFS-like units) below which audio
            is considered "silent". More negative = stricter.
        min_silence_len: minimum duration (seconds) for a silence to count
        frame_rate: how many audio samples per second to analyze

    Returns:
        List of dicts: [{"start": float, "end": float, "duration": float}, ...]
    """
    times, volumes, duration = analyze_audio(video_path, frame_rate=frame_rate)
    if len(times) == 0:
        return []

    is_silent = volumes < silence_thresh_db

    # Walk through the boolean array and group consecutive silent frames
    silences = []
    start_idx = None
    for i, silent in enumerate(is_silent):
        if silent and start_idx is None:
            start_idx = i
        elif not silent and start_idx is not None:
            start_t = times[start_idx]
            end_t = times[i]
            if end_t - start_t >= min_silence_len:
                silences.append({"start": round(start_t, 2), "end": round(end_t, 2),
                                  "duration": round(end_t - start_t, 2)})
            start_idx = None
    if start_idx is not None:
        start_t = times[start_idx]
        end_t = times[-1]
        if end_t - start_t >= min_silence_len:
            silences.append({"start": round(start_t, 2), "end": round(end_t, 2),
                              "duration": round(end_t - start_t, 2)})

    return silences


def build_trimmed_clip(video_path, silences, output_path, resolution="Original", quality="Standard"):
    """
    Given the silences found above, cuts them out and writes a new,
    tightened video to output_path.
    """
    clip = VideoFileClip(video_path)
    duration = clip.duration

    # Build the list of segments to KEEP (the inverse of the silences)
    keep_segments = []
    cursor = 0.0
    for s in silences:
        if s["start"] > cursor:
            keep_segments.append((cursor, s["start"]))
        cursor = s["end"]
    if cursor < duration:
        keep_segments.append((cursor, duration))

    if not keep_segments:
        clip.close()
        return None

    subclips = [clip.subclipped(s, e) for s, e in keep_segments if e - s > 0.05]
    final = concatenate_videoclips(subclips)

    from modules.export_settings import target_height, moviepy_write_kwargs
    h = target_height(resolution)
    if h and final.h > h:
        final = final.resized(height=h)

    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None,
                           **moviepy_write_kwargs(quality))
    clip.close()
    final.close()
    return output_path


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    results = find_silences(path)
    print(f"Found {len(results)} silent segment(s):")
    for s in results:
        print(f"  {s['start']}s -> {s['end']}s  ({s['duration']}s)")
