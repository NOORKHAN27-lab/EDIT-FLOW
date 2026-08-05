"""
AI Auto-Captions Generator
----------------------------
Transcribes a video's speech into timestamped captions using OpenAI's
Whisper (runs fully offline once the model is downloaded — no API key
needed) and exports a ready-to-import .srt subtitle file.

Note: the Whisper model (~140MB for the "base" model) downloads once
the first time this runs, so it needs an internet connection on first use.
"""

import whisper


def format_timestamp(seconds):
    """Converts seconds (float) into SRT's HH:MM:SS,mmm format."""
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_captions(video_path, output_srt_path, model_size="base"):
    """
    Transcribes the audio in video_path and writes an .srt file.

    model_size: "tiny", "base", "small", "medium", "large" —
        bigger models are more accurate but slower.

    Returns the list of segments (start, end, text) that were written.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, verbose=False)

    segments = result["segments"]

    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    return [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
            for s in segments]


if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "test_assets/sample.mp4"
    segments = generate_captions(video, "test_assets/captions.srt")
    print(f"Generated {len(segments)} caption segment(s). Saved to test_assets/captions.srt")
    for s in segments[:5]:
        print(f"  [{s['start']}s -> {s['end']}s] {s['text']}")
