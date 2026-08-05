"""
Visualizations
----------------
Builds the two chart types used across the dashboard:
  - Audio waveform with silent regions shaded (Silence Detector)
  - Horizontal timeline with markers/segments (Scene Detector, Highlight Reel)

Both return a matplotlib Figure so Streamlit can render them directly
with st.pyplot(), and both are styled to match the app's dark theme.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DARK_BG = "#111A2E"
TEAL = "#2DD4BF"
TEAL_DIM = "#2DD4BF33"
LINE = "#22304D"
TEXT = "#8B96AE"
RED = "#FB7185"


def _style_axes(ax, fig):
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    for spine in ax.spines.values():
        spine.set_color(LINE)
    ax.tick_params(colors=TEXT, labelsize=8)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def plot_waveform(times, volumes_db, duration, silences=None, figsize=(10, 2.6)):
    """
    Draws the audio volume curve over time, with silent regions (from
    find_silences) shaded in red so they're visually obvious.
    """
    fig, ax = plt.subplots(figsize=figsize)
    _style_axes(ax, fig)

    ax.plot(times, volumes_db, color=TEAL, linewidth=0.8)
    ax.fill_between(times, volumes_db, volumes_db.min(), color=TEAL_DIM)

    if silences:
        for s in silences:
            ax.axvspan(s["start"], s["end"], color=RED, alpha=0.25)

    ax.set_xlim(0, duration)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Volume (dB)")
    ax.set_title("Audio Waveform" + (" — silent regions shaded" if silences else ""),
                 color="#E8ECF4", fontsize=10, loc="left")
    fig.tight_layout()
    return fig


def plot_timeline(duration, markers=None, segments=None, figsize=(10, 1.4),
                   marker_label="Scene change", segment_label="Kept"):
    """
    Draws a single horizontal bar representing the full video duration.

    markers: list of timestamps (floats) to show as vertical tick marks
        (e.g. scene changes).
    segments: list of {"start":..., "end":...} dicts to show as filled
        blocks (e.g. highlight-reel chunks that were kept).
    """
    fig, ax = plt.subplots(figsize=figsize)
    _style_axes(ax, fig)

    # base track
    ax.barh(0, duration, left=0, height=0.5, color=LINE)

    if segments:
        for s in segments:
            ax.barh(0, s["end"] - s["start"], left=s["start"], height=0.5, color=TEAL)

    if markers:
        for m in markers:
            ax.axvline(m, color=RED, linewidth=1.4, ymin=0.15, ymax=0.85)

    ax.set_xlim(0, duration)
    ax.set_ylim(-1, 1)
    ax.set_yticks([])
    ax.set_xlabel("Time (s)")

    title_bits = []
    if markers:
        title_bits.append(f"{len(markers)} {marker_label.lower()}(s)")
    if segments:
        title_bits.append(f"{len(segments)} {segment_label.lower()} segment(s)")
    title = "Timeline — " + ", ".join(title_bits) if title_bits else "Timeline"
    ax.set_title(title, color="#E8ECF4", fontsize=10, loc="left")

    fig.tight_layout()
    return fig
