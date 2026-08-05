"""
Scene Change Detector
-----------------------
Walks through a video frame-by-frame and flags timestamps where the
shot likely changed (a hard cut, camera angle switch, etc.) by
comparing color histograms between consecutive frames — useful for
quickly splitting long, unedited footage into rough chunks.
"""

import cv2
import numpy as np


def detect_scene_changes(video_path, threshold=0.5, sample_every_nth_frame=1):
    """
    Returns a list of timestamps (seconds) where a scene change was detected.

    threshold: how different two consecutive frames' color histograms
        need to be (0-1 scale) to count as a scene change. Lower = more
        sensitive (more cuts detected).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24

    prev_hist = None
    changes = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every_nth_frame == 0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist)

            if prev_hist is not None:
                # Correlation close to 1 = very similar frames, close to 0/negative = very different
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                diff = 1 - similarity
                if diff > threshold:
                    changes.append(round(frame_idx / fps, 2))

            prev_hist = hist

        frame_idx += 1

    cap.release()
    return changes


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    changes = detect_scene_changes(path)
    print(f"Detected {len(changes)} scene change(s) at: {changes}")
