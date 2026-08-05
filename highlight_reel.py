"""
Highlight Reel Auto-Generator
-------------------------------
Scores a video in short chunks by combining audio energy (loudness)
and visual motion, then stitches the highest-scoring chunks together
into a short highlight compilation — a rough-cut starting point for
social clips instead of scrubbing through everything by hand.
"""

import numpy as np
import cv2
from moviepy import VideoFileClip, concatenate_videoclips
from modules.export_settings import target_height, moviepy_write_kwargs


def _audio_energy(clip, chunk_start, chunk_end, sample_rate=200):
    """Average loudness of the audio within a time window."""
    if clip.audio is None:
        return 0
    times = np.linspace(chunk_start, chunk_end, int((chunk_end - chunk_start) * sample_rate))
    energies = []
    for t in times:
        try:
            frame = clip.audio.get_frame(t)
            energies.append(np.sqrt(np.mean(np.square(frame))))
        except Exception:
            pass
    return float(np.mean(energies)) if energies else 0


def _motion_score(video_path, chunk_start, chunk_end, sample_fps=4):
    """Average frame-to-frame pixel difference within a time window — a cheap motion proxy."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(chunk_start * fps))

    prev_gray = None
    diffs = []
    frames_to_read = int((chunk_end - chunk_start) * sample_fps)
    step = max(int(fps / sample_fps), 1)

    for _ in range(frames_to_read):
        for _ in range(step):
            ret, frame = cap.read()
            if not ret:
                cap.release()
                return float(np.mean(diffs)) if diffs else 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray).mean()
            diffs.append(diff)
        prev_gray = gray

    cap.release()
    return float(np.mean(diffs)) if diffs else 0


def generate_highlight_reel(video_path, output_path, chunk_len=2.0, top_fraction=0.3,
                             resolution="Original", quality="Standard"):
    """
    Splits the video into `chunk_len`-second chunks, scores each by
    audio energy + motion, keeps the top `top_fraction` of chunks
    (in their original order), and writes a highlight reel.

    Returns the list of (start, end, score) chunks that were kept.
    """
    clip = VideoFileClip(video_path)
    duration = clip.duration

    chunks = []
    t = 0.0
    while t < duration:
        end = min(t + chunk_len, duration)
        audio_score = _audio_energy(clip, t, end)
        motion_score = _motion_score(video_path, t, end)
        # Normalize-ish combine: audio tends to dominate scale, so weight motion up
        score = audio_score * 3 + motion_score * 0.1
        chunks.append({"start": t, "end": end, "score": score})
        t += chunk_len

    if not chunks:
        clip.close()
        return []

    chunks_sorted = sorted(chunks, key=lambda c: c["score"], reverse=True)
    keep_count = max(1, int(len(chunks) * top_fraction))
    kept = chunks_sorted[:keep_count]
    # Restore chronological order so the reel still makes narrative sense
    kept = sorted(kept, key=lambda c: c["start"])

    subclips = [clip.subclipped(c["start"], c["end"]) for c in kept]
    final = concatenate_videoclips(subclips)

    h = target_height(resolution)
    if h and final.h > h:
        final = final.resized(height=h)

    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None,
                           **moviepy_write_kwargs(quality))

    clip.close()
    final.close()
    return kept


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    kept = generate_highlight_reel(path, "test_assets/highlight_reel.mp4", chunk_len=2.0, top_fraction=0.5)
    print(f"Kept {len(kept)} chunk(s) for the highlight reel:")
    for c in kept:
        print(f"  {c['start']}s -> {c['end']}s  (score={c['score']:.2f})")
