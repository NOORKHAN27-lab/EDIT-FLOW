"""
EditFlow — Streamlit Dashboard
==========================================
A single web interface tying together every module in /modules:
silence detection, auto-thumbnails, watermarking, batch rename,
video info reports, AI captions, scene detection, highlight reels,
color grading, and a combined EditFlow pipeline.

Run locally with:
    streamlit run app.py
"""

import os
import tempfile
import datetime
import streamlit as st

from modules import silence_detector, thumbnail_generator, watermark, \
    video_info, batch_rename, scene_detector, highlight_reel, color_grade, \
    visualizations, pipeline
from modules.export_settings import RESOLUTIONS, QUALITY_PRESETS

st.set_page_config(page_title="EditFlow — Automated Video Editing", page_icon="🎬", layout="wide")

# ---------------------------------------------------------------------------
# THEME (dark / light toggle)
# ---------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "history" not in st.session_state:
    st.session_state.history = []


def log_history(action, detail=""):
    st.session_state.history.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "detail": detail,
    })
    st.session_state.history = st.session_state.history[:20]


THEMES = {
    "dark": {
        "bg": "#0A0F1C", "bg_grad": "linear-gradient(180deg, #0A0F1C 0%, #0B1424 100%)",
        "surface": "#0F1830", "surface2": "#141F3D", "surface3": "#182448",
        "line": "#22304D", "line_soft": "#1A2540",
        "accent": "#2DD4BF", "accent2": "#818CF8", "accent_bright": "#5EEAD4",
        "accent_grad": "linear-gradient(135deg, #2DD4BF 0%, #6366F1 100%)",
        "text": "#F1F5F9", "muted": "#8B96AE", "muted2": "#64748B",
        "accent_text_on": "#062A26", "shadow": "0 8px 30px rgba(0,0,0,0.35)",
        "glow": "0 0 0 1px rgba(45,212,191,0.15), 0 8px 24px rgba(45,212,191,0.08)",
    },
    "light": {
        "bg": "#F6F8FC", "bg_grad": "linear-gradient(180deg, #F6F8FC 0%, #EEF2FA 100%)",
        "surface": "#FFFFFF", "surface2": "#F5F7FB", "surface3": "#EEF1F8",
        "line": "#E1E7F2", "line_soft": "#EAEEF6",
        "accent": "#0D9488", "accent2": "#6366F1", "accent_bright": "#0F766E",
        "accent_grad": "linear-gradient(135deg, #0D9488 0%, #6366F1 100%)",
        "text": "#0F172A", "muted": "#5B6472", "muted2": "#8791A3",
        "accent_text_on": "#FFFFFF", "shadow": "0 8px 30px rgba(15,23,42,0.06)",
        "glow": "0 0 0 1px rgba(13,148,136,0.12), 0 8px 24px rgba(13,148,136,0.06)",
    },
}
T = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}

.stApp{{ background:{T['bg_grad']}; color:{T['text']}; }}
#MainMenu, footer, header[data-testid="stHeader"]{{ background:transparent; }}
.block-container{{ padding-top:1.6rem; max-width:1220px; }}

section[data-testid="stSidebar"]{{
  background:{T['surface']}; border-right:1px solid {T['line_soft']};
}}
section[data-testid="stSidebar"] .block-container{{ padding-top:1.4rem; }}

h1,h2,h3{{ color:{T['text']} !important; font-weight:700; letter-spacing:-0.01em; }}
p, span, label, .stMarkdown{{ color:{T['text']}; }}

/* ---------- Top brand header / nav ---------- */
.editflow-header{{
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 28px; background:{T['surface']};
  border:1px solid {T['line_soft']}; border-radius:16px; margin-bottom:20px;
  box-shadow:{T['shadow']};
}}
.editflow-logo{{ display:flex; align-items:center; gap:14px; }}
.editflow-logo .mark{{
  width:42px; height:42px; border-radius:12px; background:{T['accent_grad']};
  display:flex; align-items:center; justify-content:center; font-size:20px;
  box-shadow:0 4px 14px rgba(45,212,191,0.35);
}}
.editflow-title{{ font-size:20px; font-weight:800; color:{T['text']}; letter-spacing:-0.02em; }}
.editflow-title span{{
  background:{T['accent_grad']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
}}
.editflow-subtitle{{ font-size:12.5px; color:{T['muted']}; margin-top:2px; }}
.editflow-badge{{
  display:inline-flex; align-items:center; gap:6px; font-size:11px; font-weight:700;
  color:{T['accent_bright']}; background:{T['surface2']}; border:1px solid {T['line']};
  padding:5px 11px; border-radius:999px; text-transform:uppercase; letter-spacing:0.04em;
}}
.editflow-badge .dot{{ width:6px; height:6px; border-radius:50%; background:{T['accent']}; box-shadow:0 0 8px {T['accent']}; }}
.editflow-credit{{ font-size:12px; color:{T['muted']}; text-align:right; }}
.editflow-credit b{{ color:{T['accent_bright']}; }}

/* ---------- Nav tabs styled as a real top nav bar ---------- */
.stTabs [data-baseweb="tab-list"]{{
  gap:2px; background:{T['surface']}; padding:8px; border-radius:14px;
  border:1px solid {T['line_soft']}; flex-wrap:wrap; box-shadow:{T['shadow']}; margin-bottom:8px;
}}
.stTabs [data-baseweb="tab"]{{
  background:transparent; border-radius:9px; color:{T['muted']}; padding:11px 18px;
  font-weight:600; font-size:14px; transition:all 0.15s ease;
}}
.stTabs [data-baseweb="tab"]:hover{{ background:{T['surface2']}; color:{T['text']}; }}
.stTabs [aria-selected="true"]{{
  background:{T['accent_grad']} !important; color:{T['accent_text_on']} !important;
  box-shadow:0 4px 14px rgba(45,212,191,0.25);
}}
.stTabs [data-baseweb="tab-highlight"]{{ display:none; }}
.stTabs [data-baseweb="tab-border"]{{ display:none; }}

/* ---------- Cards ---------- */
.card{{
  background:{T['surface']}; border:1px solid {T['line_soft']}; border-radius:14px;
  padding:22px 24px; margin-bottom:20px; box-shadow:{T['shadow']}; position:relative; overflow:hidden;
}}
.card::before{{
  content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:{T['accent_grad']};
}}
.card h4{{ color:{T['text']}; margin-top:0; margin-bottom:6px; font-size:17px; font-weight:700; padding-left:8px; }}
.card p{{ color:{T['muted']}; font-size:13.5px; margin-bottom:0; padding-left:8px; line-height:1.5; }}

/* ---------- Hero / feature strip ---------- */
.hero-strip{{
  display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px;
}}
.pill{{
  font-size:11.5px; font-weight:600; color:{T['muted']}; background:{T['surface']};
  border:1px solid {T['line_soft']}; padding:7px 13px; border-radius:999px;
}}
.pill b{{ color:{T['accent_bright']}; }}

/* ---------- Buttons ---------- */
.stButton button{{
  background:{T['accent_grad']} !important; color:{T['accent_text_on']} !important; border:none !important;
  font-weight:700 !important; border-radius:9px !important; padding:0.55rem 1.3rem !important;
  box-shadow:0 4px 14px rgba(45,212,191,0.25) !important; transition:transform 0.12s ease, box-shadow 0.12s ease !important;
}}
.stButton button:hover{{ transform:translateY(-1px); box-shadow:0 6px 18px rgba(45,212,191,0.35) !important; }}
.stDownloadButton button{{
  background:{T['surface2']} !important; color:{T['accent_bright']} !important;
  border:1px solid {T['line']} !important; font-weight:700 !important; border-radius:9px !important;
}}
.stDownloadButton button:hover{{ background:{T['surface3']} !important; border-color:{T['accent']} !important; }}

/* ---------- Inputs / uploaders ---------- */
div[data-testid="stFileUploaderDropzone"]{{
  background:{T['surface2']}; border:1.5px dashed {T['line']}; border-radius:12px;
}}
.stSlider [data-baseweb="slider"]{{ margin-top:4px; }}
div[data-testid="stMetric"]{{
  background:{T['surface']}; border:1px solid {T['line_soft']}; border-radius:12px; padding:14px 16px;
  box-shadow:{T['shadow']};
}}
div[data-testid="stMetricLabel"]{{ color:{T['muted']} !important; font-size:12.5px !important; }}
div[data-testid="stMetricValue"]{{ color:{T['accent_bright']} !important; }}

.stDataFrame{{ border-radius:12px; overflow:hidden; border:1px solid {T['line_soft']}; }}
.stProgress > div > div{{ background:{T['accent_grad']} !important; }}

/* ---------- Sidebar ---------- */
.sidebar-brand{{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
.sidebar-brand .mark{{
  width:30px; height:30px; border-radius:9px; background:{T['accent_grad']};
  display:flex; align-items:center; justify-content:center; font-size:15px;
}}
.sidebar-brand-text{{ font-size:15px; font-weight:800; color:{T['text']}; }}
.sidebar-section-label{{
  font-size:11px; font-weight:700; color:{T['muted2']}; text-transform:uppercase;
  letter-spacing:0.06em; margin:18px 0 10px 0;
}}
.history-item{{
  font-size:12px; color:{T['muted']}; padding:10px 12px; border-radius:9px;
  background:{T['surface2']}; margin-bottom:6px; border:1px solid {T['line_soft']};
}}
.history-item b{{ color:{T['text']}; }}
.history-empty{{
  font-size:12.5px; color:{T['muted2']}; padding:16px; text-align:center;
  background:{T['surface2']}; border-radius:10px; border:1px dashed {T['line']};
}}
.compare-label{{
  text-align:center; font-size:11px; color:{T['muted']}; font-weight:700; letter-spacing:0.06em;
  text-transform:uppercase; margin-bottom:8px; background:{T['surface2']}; padding:5px; border-radius:6px;
}}

/* ---------- Footer ---------- */
.editflow-footer{{
  margin-top:36px; padding:18px 24px; text-align:center; font-size:12px; color:{T['muted2']};
  border-top:1px solid {T['line_soft']};
}}
.editflow-footer b{{ color:{T['accent_bright']}; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="editflow-header">
  <div class="editflow-logo">
    <div class="mark">🎬</div>
    <div>
      <div class="editflow-title">Edit<span>Flow</span></div>
      <div class="editflow-subtitle">Batch video-editing automation — silence cuts, captions, highlights &amp; more</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:16px;">
    <span class="editflow-badge"><span class="dot"></span>10 tools online</span>
    <div class="editflow-credit">Developed by<br><b>Noor Ahmed Khan</b></div>
  </div>
</div>
""", unsafe_allow_html=True)


def save_upload(uploaded_file):
    """Writes an uploaded file to a temp path and returns that path."""
    suffix = os.path.splitext(uploaded_file.name)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.close()
    return tmp.name


def export_settings_widget(key_prefix):
    """Shared resolution + quality picker used by every export-producing tool."""
    c1, c2 = st.columns(2)
    resolution = c1.selectbox("Export resolution", list(RESOLUTIONS.keys()), key=f"{key_prefix}_res")
    quality = c2.selectbox("Export quality", list(QUALITY_PRESETS.keys()), index=1, key=f"{key_prefix}_qual")
    return resolution, quality


# ---------------------------------------------------------------------------
# SIDEBAR — theme toggle + processing history
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
      <div class="mark">🎬</div>
      <div class="sidebar-brand-text">EditFlow</div>
    </div>
    <div style="font-size:12px; color:{T['muted2']}; margin-bottom:4px;">Video editing automation suite</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">⚙️ Appearance</div>', unsafe_allow_html=True)
    theme_choice = st.radio("Theme", ["dark", "light"], index=0 if st.session_state.theme == "dark" else 1,
                             horizontal=True, label_visibility="collapsed")
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.markdown('<div class="sidebar-section-label">📜 Session History</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown('<div class="history-empty">Nothing processed yet this session.<br>Run a tool to see it here.</div>',
                     unsafe_allow_html=True)
    else:
        for item in st.session_state.history:
            st.markdown(
                f'<div class="history-item">{item["time"]} — <b>{item["action"]}</b><br>{item["detail"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown(f"""
    <div style="margin-top:24px; padding-top:16px; border-top:1px solid {T['line_soft']}; font-size:11px; color:{T['muted2']}; text-align:center;">
      EditFlow v1.0 · Built by <b style="color:{T['accent_bright']}">Noor Ahmed Khan</b>
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
<div class="hero-strip">
  <span class="pill">🎯 <b>10 tools</b> in one dashboard</span>
  <span class="pill">📦 <b>Batch</b> processing</span>
  <span class="pill">👀 <b>Live</b> before/after preview</span>
  <span class="pill">🖥 Runs <b>fully offline</b></span>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "⚡ Full Pipeline", "🔇 Silence Cuts", "🖼 Thumbnails", "🏷 Watermark", "📋 Video Info",
    "📁 Batch Rename", "🎞 Scene Detect", "🎬 Highlight Reel", "🎨 Color Grade", "📝 Captions",
])

# ---------------------------------------------------------------------------
# 0. FULL PIPELINE
# ---------------------------------------------------------------------------
with tabs[0]:
    st.markdown('<div class="card"><h4>Full EditFlow Pipeline</h4>'
                '<p>Runs silence removal → scene detection → thumbnails → captions in one pass, '
                'instead of using each tool separately.</p></div>', unsafe_allow_html=True)

    file = st.file_uploader("Upload a video", type=["mp4", "mov"], key="pipeline_upload")
    if file:
        st.markdown('<div class="compare-label">Preview</div>', unsafe_allow_html=True)
        st.video(file)

    c1, c2 = st.columns(2)
    thresh = c1.slider("Silence threshold (dB)", -60, -10, -35, key="pipe_thresh")
    min_len = c2.slider("Minimum silence length (sec)", 0.2, 3.0, 0.6, key="pipe_minlen")
    want_captions = st.checkbox("Also generate captions (slower)", value=False)
    caption_model = st.selectbox("Caption model size", ["tiny", "base", "small"], index=1,
                                  disabled=not want_captions)
    resolution, quality = export_settings_widget("pipeline")

    if file and st.button("Run Full Pipeline", key="btn_pipeline"):
        path = save_upload(file)
        out_dir = tempfile.mkdtemp()
        progress_bar = st.progress(0, text="Starting...")

        def update_progress(step, frac):
            progress_bar.progress(frac, text=step)

        result = pipeline.run_pipeline(
            path, out_dir,
            silence_thresh_db=thresh, min_silence_len=min_len,
            generate_captions=want_captions, caption_model=caption_model,
            resolution=resolution, quality=quality,
            progress_callback=update_progress,
        )
        log_history("Ran full pipeline", f"{file.name} — {len(result['silences_removed'])} silences removed")

        st.success("Pipeline complete!")
        st.video(result["trimmed_video_path"])
        with open(result["trimmed_video_path"], "rb") as f:
            st.download_button("Download final video", f, file_name="editflowed.mp4")

        m1, m2, m3 = st.columns(3)
        m1.metric("Silences removed", len(result["silences_removed"]))
        m2.metric("Scene changes", len(result["scene_changes"]))
        m3.metric("Thumbnails generated", len(result["thumbnails"]))

        if result["thumbnails"]:
            st.markdown("**Thumbnail candidates**")
            cols = st.columns(min(len(result["thumbnails"]), 5) or 1)
            for i, r in enumerate(result["thumbnails"]):
                with cols[i % len(cols)]:
                    st.image(r["path"], caption=f"t={r['timestamp']}s")

        if result["captions"]:
            st.markdown("**Captions**")
            st.dataframe(result["captions"], use_container_width=True)
            with open(result["captions_srt_path"], "rb") as f:
                st.download_button("Download .srt", f, file_name="captions.srt")

# ---------------------------------------------------------------------------
# 1. SILENCE / JUMP-CUT DETECTOR
# ---------------------------------------------------------------------------
with tabs[1]:
    st.markdown('<div class="card"><h4>Silence / Jump-Cut Detector</h4>'
                '<p>Finds dead-air gaps in your footage so you don\'t have to scrub for them by hand.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="silence_upload", accept_multiple_files=True)
    if files:
        st.markdown('<div class="compare-label">Preview — first file</div>', unsafe_allow_html=True)
        st.video(files[0])

    col1, col2 = st.columns(2)
    thresh = col1.slider("Silence threshold (dB)", -60, -10, -35)
    min_len = col2.slider("Minimum silence length (sec)", 0.2, 3.0, 0.6)
    resolution, quality = export_settings_widget("silence")
    export_trimmed = st.checkbox("Also export a trimmed video (not just detect)", value=False)

    if files and st.button("Detect Silences", key="btn_silence"):
        for file in files:
            st.markdown(f"#### {file.name}")
            path = save_upload(file)
            with st.spinner("Analyzing audio..."):
                times, vols, duration = silence_detector.analyze_audio(path)
                results = silence_detector.find_silences(path, silence_thresh_db=thresh, min_silence_len=min_len)

            if len(times) > 0:
                fig = visualizations.plot_waveform(times, vols, duration, results)
                st.pyplot(fig, use_container_width=True)

            if results:
                st.success(f"Found {len(results)} silent segment(s)")
                st.dataframe(results, use_container_width=True)
            else:
                st.info("No silences found at this threshold.")

            log_history("Detected silences", f"{file.name} — {len(results)} found")

            if export_trimmed and results:
                out_path = os.path.join(tempfile.mkdtemp(), f"trimmed_{file.name}")
                with st.spinner("Rendering trimmed video..."):
                    silence_detector.build_trimmed_clip(path, results, out_path,
                                                         resolution=resolution, quality=quality)
                st.video(out_path)
                with open(out_path, "rb") as f:
                    st.download_button(f"Download trimmed — {file.name}", f,
                                        file_name=f"trimmed_{file.name}", key=f"dl_{file.name}")

# ---------------------------------------------------------------------------
# 2. THUMBNAIL GENERATOR
# ---------------------------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="card"><h4>Auto-Thumbnail Generator</h4>'
                '<p>Scores frames by sharpness and contrast to surface the best freeze-frame candidates.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="thumb_upload", accept_multiple_files=True)
    n = st.slider("Number of candidates per video", 1, 10, 5)

    if files and st.button("Generate Thumbnails", key="btn_thumb"):
        for file in files:
            st.markdown(f"#### {file.name}")
            path = save_upload(file)
            out_dir = tempfile.mkdtemp()
            with st.spinner("Scanning frames..."):
                results = thumbnail_generator.generate_thumbnails(path, out_dir, num_candidates=n)
            cols = st.columns(min(len(results), 5) or 1)
            for i, r in enumerate(results):
                with cols[i % len(cols)]:
                    st.image(r["path"], caption=f"t={r['timestamp']}s · score={r['score']}")
            log_history("Generated thumbnails", f"{file.name} — {len(results)} candidates")

# ---------------------------------------------------------------------------
# 3. WATERMARK
# ---------------------------------------------------------------------------
with tabs[3]:
    st.markdown('<div class="card"><h4>Batch Watermark / Logo Overlay</h4>'
                '<p>Stamps a logo onto every uploaded video in the corner of your choice.</p></div>',
                unsafe_allow_html=True)
    video_files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="wm_video", accept_multiple_files=True)
    logo_file = st.file_uploader("Upload a logo (PNG)", type=["png"], key="wm_logo")
    position = st.selectbox("Position", list(watermark.POSITIONS.keys()))
    opacity = st.slider("Opacity", 0.1, 1.0, 0.7)
    resolution, quality = export_settings_widget("wm")

    if video_files and logo_file and st.button("Apply Watermark", key="btn_wm"):
        lpath = save_upload(logo_file)
        for video_file in video_files:
            st.markdown(f"#### {video_file.name}")
            vpath = save_upload(video_file)
            out_path = os.path.join(tempfile.mkdtemp(), f"watermarked_{video_file.name}")
            with st.spinner("Rendering..."):
                watermark.apply_watermark(vpath, lpath, out_path, position=position,
                                           opacity=opacity, resolution=resolution, quality=quality)

            colA, colB = st.columns(2)
            with colA:
                st.markdown('<div class="compare-label">Before</div>', unsafe_allow_html=True)
                st.video(vpath)
            with colB:
                st.markdown('<div class="compare-label">After</div>', unsafe_allow_html=True)
                st.video(out_path)

            with open(out_path, "rb") as f:
                st.download_button(f"Download — {video_file.name}", f,
                                    file_name=f"watermarked_{video_file.name}", key=f"dlwm_{video_file.name}")
            log_history("Applied watermark", video_file.name)

# ---------------------------------------------------------------------------
# 4. VIDEO INFO REPORT
# ---------------------------------------------------------------------------
with tabs[4]:
    st.markdown('<div class="card"><h4>Video Info Report</h4>'
                '<p>Upload a batch of clips to see duration, resolution, codec, and total footage at a glance.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload one or more videos", type=["mp4", "mov"], accept_multiple_files=True, key="info_upload")

    if files and st.button("Generate Report", key="btn_info"):
        folder = tempfile.mkdtemp()
        for f in files:
            with open(os.path.join(folder, f.name), "wb") as out:
                out.write(f.read())
        rows, totals = video_info.generate_report(folder)
        c1, c2, c3 = st.columns(3)
        c1.metric("Clips", totals["clip_count"])
        c2.metric("Total Duration", f"{totals['total_duration_sec']}s")
        c3.metric("Total Size", f"{totals['total_size_mb']} MB")
        st.dataframe(rows, use_container_width=True)
        log_history("Generated video info report", f"{totals['clip_count']} clip(s)")

# ---------------------------------------------------------------------------
# 5. BATCH RENAME
# ---------------------------------------------------------------------------
with tabs[5]:
    st.markdown('<div class="card"><h4>Batch Rename &amp; Organize</h4>'
                '<p>Sorts raw camera footage into date-based folders with consistent naming.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload raw footage", type=["mp4", "mov"], accept_multiple_files=True, key="rename_upload")
    project_name = st.text_input("Project name prefix", value="clip")

    if files and st.button("Organize Footage", key="btn_rename"):
        folder = tempfile.mkdtemp()
        for f in files:
            with open(os.path.join(folder, f.name), "wb") as out:
                out.write(f.read())
        out_dir = tempfile.mkdtemp()
        results = batch_rename.organize_footage(folder, out_dir, project_name=project_name)
        st.success(f"Organized {len(results)} file(s)")
        for old, new in results:
            st.text(f"{os.path.basename(old)}  →  {new.replace(out_dir, '')}")
        log_history("Organized footage", f"{len(results)} file(s)")

# ---------------------------------------------------------------------------
# 6. SCENE DETECTOR
# ---------------------------------------------------------------------------
with tabs[6]:
    st.markdown('<div class="card"><h4>Scene Change Detector</h4>'
                '<p>Flags likely cut points by comparing color histograms between frames.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="scene_upload", accept_multiple_files=True)
    sensitivity = st.slider("Sensitivity (lower = more cuts detected)", 0.1, 0.9, 0.5)

    if files and st.button("Detect Scene Changes", key="btn_scene"):
        for file in files:
            st.markdown(f"#### {file.name}")
            path = save_upload(file)
            with st.spinner("Scanning..."):
                changes = scene_detector.detect_scene_changes(path, threshold=sensitivity)
                _, _, duration = silence_detector.analyze_audio(path)

            if duration:
                fig = visualizations.plot_timeline(duration, markers=changes, marker_label="Scene change")
                st.pyplot(fig, use_container_width=True)

            if changes:
                st.success(f"Detected {len(changes)} scene change(s)")
                st.write(changes)
            else:
                st.info("No scene changes detected at this sensitivity.")
            log_history("Detected scene changes", f"{file.name} — {len(changes)} found")

# ---------------------------------------------------------------------------
# 7. HIGHLIGHT REEL
# ---------------------------------------------------------------------------
with tabs[7]:
    st.markdown('<div class="card"><h4>Highlight Reel Auto-Generator</h4>'
                '<p>Keeps the loudest, most motion-heavy chunks and stitches them into a rough-cut reel.</p></div>',
                unsafe_allow_html=True)
    file = st.file_uploader("Upload a video", type=["mp4", "mov"], key="highlight_upload")
    if file:
        st.markdown('<div class="compare-label">Preview</div>', unsafe_allow_html=True)
        st.video(file)

    top_fraction = st.slider("Keep top % of footage", 0.1, 0.8, 0.3)
    resolution, quality = export_settings_widget("hl")

    if file and st.button("Generate Highlight Reel", key="btn_highlight"):
        path = save_upload(file)
        out_path = os.path.join(tempfile.mkdtemp(), "highlight_reel.mp4")
        with st.spinner("Scoring & rendering..."):
            kept = highlight_reel.generate_highlight_reel(path, out_path, top_fraction=top_fraction,
                                                            resolution=resolution, quality=quality)
            _, _, duration = silence_detector.analyze_audio(path)

        if duration:
            fig = visualizations.plot_timeline(duration, segments=kept, segment_label="Kept")
            st.pyplot(fig, use_container_width=True)

        st.success(f"Kept {len(kept)} chunk(s)")
        st.video(out_path)
        with open(out_path, "rb") as f:
            st.download_button("Download highlight reel", f, file_name="highlight_reel.mp4")
        log_history("Generated highlight reel", f"{file.name} — {len(kept)} chunks kept")

# ---------------------------------------------------------------------------
# 8. COLOR GRADE
# ---------------------------------------------------------------------------
with tabs[8]:
    st.markdown('<div class="card"><h4>Color Grading Preset Applier</h4>'
                '<p>Applies a consistent look across clips using built-in presets.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="grade_upload", accept_multiple_files=True)
    preset = st.selectbox("Preset", list(color_grade.PRESETS.keys()))
    resolution, quality = export_settings_widget("grade")

    if files and st.button("Apply Color Grade", key="btn_grade"):
        for file in files:
            st.markdown(f"#### {file.name}")
            path = save_upload(file)
            out_path = os.path.join(tempfile.mkdtemp(), f"graded_{file.name}")
            with st.spinner("Rendering..."):
                color_grade.apply_grade(path, out_path, preset=preset, resolution=resolution, quality=quality)

            colA, colB = st.columns(2)
            with colA:
                st.markdown('<div class="compare-label">Before</div>', unsafe_allow_html=True)
                st.video(path)
            with colB:
                st.markdown(f'<div class="compare-label">After — {preset}</div>', unsafe_allow_html=True)
                st.video(out_path)

            with open(out_path, "rb") as f:
                st.download_button(f"Download — {file.name}", f,
                                    file_name=f"graded_{file.name}", key=f"dlgr_{file.name}")
            log_history("Applied color grade", f"{file.name} — {preset}")

# ---------------------------------------------------------------------------
# 9. AI CAPTIONS
# ---------------------------------------------------------------------------
with tabs[9]:
    st.markdown('<div class="card"><h4>AI Auto-Captions</h4>'
                '<p>Transcribes speech into a ready-to-import .srt file using OpenAI Whisper (runs offline).</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="caption_upload", accept_multiple_files=True)
    model_size = st.selectbox("Model size", ["tiny", "base", "small"], index=1,
                               help="Bigger = more accurate but slower")

    if files and st.button("Generate Captions", key="btn_captions"):
        for file in files:
            st.markdown(f"#### {file.name}")
            path = save_upload(file)
            out_path = os.path.join(tempfile.mkdtemp(), "captions.srt")
            with st.spinner("Transcribing (this can take a minute)..."):
                from modules import captions
                segments = captions.generate_captions(path, out_path, model_size=model_size)
            st.success(f"Generated {len(segments)} caption segment(s)")
            st.dataframe(segments, use_container_width=True)
            with open(out_path, "rb") as f:
                st.download_button(f"Download .srt — {file.name}", f,
                                    file_name=f"{file.name}_captions.srt", key=f"dlcap_{file.name}")
            log_history("Generated captions", f"{file.name} — {len(segments)} segments")

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="editflow-footer">
  🎬 <b>EditFlow</b> — Batch video-editing automation, built by <b>Noor Ahmed Khan</b>
</div>
""", unsafe_allow_html=True)
