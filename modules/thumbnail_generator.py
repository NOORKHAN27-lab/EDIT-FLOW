"""
Auto-Thumbnail Generator
-------------------------
Scans a video and picks out the most "visually interesting" frames to
use as thumbnail candidates — instead of scrubbing through footage by
hand to find a good freeze-frame.

"Interesting" here means high sharpness (in-focus, not motion-blurred)
combined with good contrast — frames that are dark, blurry, or flat
score low and get skipped automatically.
"""

import cv2
import os


def score_frame(frame):
    """Higher score = sharper, more visually interesting frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Sharpness: variance of the Laplacian (blurry frames have low variance)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Contrast: standard deviation of pixel intensities
    contrast = gray.std()
    return sharpness * 0.7 + contrast * 0.3


def generate_thumbnails(video_path, output_dir, num_candidates=5, sample_every_sec=1.0):
    """
    Samples frames across the video, scores them, and saves the top
    `num_candidates` as thumbnail images.

    Returns a list of dicts: [{"path": ..., "timestamp": ..., "score": ...}, ...]
    sorted best-first.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frame_interval = max(int(fps * sample_every_sec), 1)

    candidates = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            score = score_frame(frame)
            timestamp = frame_idx / fps
            candidates.append((score, timestamp, frame))
        frame_idx += 1
    cap.release()

    if not candidates:
        return []

    # Keep the top N distinct frames by score
    candidates.sort(key=lambda c: c[0], reverse=True)
    top = candidates[:num_candidates]

    results = []
    for i, (score, ts, frame) in enumerate(top):
        filename = f"thumb_{i+1}_{ts:.1f}s.jpg"
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, frame)
        results.append({"path": out_path, "timestamp": round(ts, 2), "score": round(score, 1)})

    return results


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    results = generate_thumbnails(path, "test_assets/thumbnails")
    print(f"Generated {len(results)} thumbnail candidates:")
    for r in results:
        print(f"  {r['path']}  (t={r['timestamp']}s, score={r['score']})")
