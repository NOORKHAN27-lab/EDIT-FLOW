# EditFlow

EditFlow is a Python toolkit that automates the repetitive parts of a video edit — the
kind of work that normally means scrubbing through footage by hand in
Premiere Pro. Built to combine software engineering with real video-editing
workflow knowledge, not as a generic tutorial project.

**Live app:** _add your Streamlit Cloud link here once deployed_
**Built by:** Noor Ahmed Khan

## What it does

Ten tools, all wrapped in one web dashboard:

| Tool | What it solves |
|---|---|
| ⚡ **Full EditFlow Pipeline** | Chains silence removal → scene detection → thumbnails → captions into a single run |
| 🔇 **Silence / Jump-Cut Detector** | Finds dead-air gaps in the audio track, with a waveform visualization showing exactly where |
| 🖼 **Auto-Thumbnail Generator** | Scores frames by sharpness + contrast to surface the best freeze-frame candidates |
| 🏷 **Batch Watermark / Logo Overlay** | Stamps a logo onto a video, with a before/after side-by-side preview |
| 📋 **Video Info Report** | Duration, resolution, codec, and total footage size across a whole folder at a glance |
| 📁 **Batch Rename & Organize** | Sorts raw camera footage into date-based folders with consistent naming |
| 🎞 **Scene Change Detector** | Flags likely cut points, plotted on a visual timeline |
| 🎬 **Highlight Reel Generator** | Keeps the loudest, most motion-heavy chunks and stitches them into a rough-cut reel, with a kept-segments timeline |
| 🎨 **Color Grading Presets** | Applies a consistent look (warm / cool / cinematic / vibrant / muted) across clips, with before/after preview |
| 📝 **AI Auto-Captions** | Transcribes speech into a ready-to-import `.srt` file using OpenAI Whisper — runs fully offline |

**Every tool also supports:**
- **Batch processing** — upload multiple clips and process them all in one pass
- **Preview before processing** — see the uploaded video before committing to a render
- **Export settings** — choose output resolution (Original/1080p/720p/480p) and quality (High/Standard/Compressed)
- **Session history** — a sidebar log of everything processed in the current session
- **Dark / light theme toggle**

## How to run it

```bash
git clone https://github.com/NOORKHAN27-lab/EDITFLOW.git
cd EDITFLOW
pip install -r requirements.txt
streamlit run app.py
```

You'll also need [ffmpeg](https://ffmpeg.org/download.html) installed on your
system (used under the hood by moviepy and the color-grading module).

Each tool also works as a standalone script, e.g.:

```bash
python -m modules.silence_detector test_assets/sample.mp4
python -m modules.pipeline test_assets/sample.mp4
```

## How the core pieces work

- **Silence detection** samples the audio waveform at a fixed rate, flags
  stretches below a volume threshold, and groups them into timestamped
  segments. The same sampled data feeds a matplotlib waveform chart with
  the detected silences shaded directly on it.
- **Thumbnail scoring** combines Laplacian sharpness (rejects blurry frames)
  with contrast (rejects flat, low-detail frames).
- **Scene detection** compares HSV color histograms between consecutive
  sampled frames — a big drop in similarity usually means a cut. Detected
  changes are plotted as markers on a horizontal timeline.
- **Highlight reel** scores short chunks by a blend of audio loudness and
  frame-to-frame motion, keeps the top-scoring chunks, and restores their
  original order so the reel still reads chronologically. Kept segments
  are shown on the same timeline visualization.
- **The pipeline** runs silence removal first (so every later step works
  off the already-tightened footage), then scene detection, thumbnails,
  and optionally captions — reporting progress back to the UI at each step.
- **Captions** run entirely offline through Whisper — no API key or internet
  connection required after the model's first download.
- **Export settings** are centralized in `modules/export_settings.py` so
  every tool shares the same resolution/quality options and behavior
  (always downscales, never upscales past the source resolution).

## Why this project

This isn't a generic "learn Python" exercise — every tool here solves a real
step in an actual editing workflow, built from hands-on experience with
Adobe Premiere Pro and After Effects. It's a small proof that the same
structured, problem-solving mindset from software engineering carries over
directly into creative tooling.

## Tech stack

Python · Streamlit · MoviePy · OpenCV · OpenAI Whisper · FFmpeg

---
Built by Noor Ahmed Khan
