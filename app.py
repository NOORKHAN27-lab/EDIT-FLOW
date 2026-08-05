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


def log_history(action, detail="", toast_icon="✅"):
    st.session_state.history.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "detail": detail,
    })
    st.session_state.history = st.session_state.history[:20]
    st.toast(f"**{action}** — {detail}" if detail else action, icon=toast_icon)


# ---------------------------------------------------------------------------
# ICONS — inline SVG (stroke-based), used instead of emoji throughout the UI
# ---------------------------------------------------------------------------
ICON_PATHS = {
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "volume-x": '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "tag": '<path d="M20.59 13.41 11 3.83A2 2 0 0 0 9.58 3.24L4 3.24A1 1 0 0 0 3 4.24L3 9.83A2 2 0 0 0 3.59 11.24L13.17 20.83a2 2 0 0 0 2.83 0l4.59-4.59a2 2 0 0 0 0-2.83Z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="16" y2="15"/>',
    "folder": '<path d="M4 4h5l2 2h9a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"/>',
    "film": '<rect x="2" y="3" width="20" height="18" rx="2"/><line x1="7" y1="3" x2="7" y2="21"/><line x1="17" y1="3" x2="17" y2="21"/><line x1="2" y1="9" x2="22" y2="9"/><line x1="2" y1="15" x2="22" y2="15"/>',
    "clapperboard": '<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="M6.2 5.3 7 9"/><path d="M12.4 3.4 13 7"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "palette": '<circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.5-.7 1.5-1.5 0-.4-.1-.8-.4-1.1-.2-.3-.4-.6-.4-1 0-.8.7-1.4 1.5-1.4H16c3.3 0 6-2.7 6-6 0-4.9-4.5-9-10-9Z"/>',
    "captions": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 15h1.5a1.5 1.5 0 1 0 0-3H7v3Z"/><path d="M13.5 12h2M13.5 15h2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>',
    "history": '<path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "alert-circle": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/>',
    "home": '<path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1Z"/>',
    "arrow-right": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
}


def icon(name, size=17, color="currentColor", stroke_width=2):
    body = ICON_PATHS.get(name, ICON_PATHS["zap"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px">{body}</svg>')


def hint(text):
    """Small muted helper line shown under a control, explaining what it does."""
    st.markdown(f'<div class="control-hint">{icon("info", 13)}<span>{text}</span></div>',
                unsafe_allow_html=True)


def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


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

/* ---------- Website-style top navbar (real buttons, not st.tabs) ---------- */
.navbar-wrap{{
  background:{T['surface']}; border:1px solid {T['line_soft']}; border-radius:14px;
  padding:8px 10px; box-shadow:{T['shadow']}; margin-bottom:20px;
}}
.navbar-wrap div[data-testid="stHorizontalBlock"]{{ flex-wrap:wrap; row-gap:4px; }}
.navbar-wrap div[data-testid="column"]{{ padding:0 2px !important; min-width:100px; }}
.navbar-wrap .stButton{{ margin:0; }}
.navbar-wrap .stButton button{{
  background:transparent !important; color:{T['muted']} !important; border:none !important;
  box-shadow:none !important; font-weight:600 !important; font-size:13px !important;
  padding:10px 6px !important; border-radius:9px !important; white-space:nowrap !important;
  transform:none !important; transition:background 0.15s ease, color 0.15s ease !important;
}}
.navbar-wrap .stButton button:hover{{
  background:{T['surface2']} !important; color:{T['text']} !important;
}}
.navbar-wrap .stButton button[kind="primary"]{{
  background:{T['accent_grad']} !important; color:{T['accent_text_on']} !important;
  box-shadow:0 4px 14px rgba(45,212,191,0.25) !important;
}}
.navbar-wrap .stButton button[kind="primary"]:hover{{
  background:{T['accent_grad']} !important; color:{T['accent_text_on']} !important;
}}

/* ---------- Dashboard / landing tool grid ---------- */
.tool-card{{
  background:{T['surface']}; border:1px solid {T['line_soft']}; border-radius:14px;
  padding:18px 16px 14px 16px; margin-bottom:8px; transition:transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  min-height:132px;
}}
.tool-card:hover{{ transform:translateY(-2px); box-shadow:{T['glow']}; border-color:{T['accent']}44; }}
.tool-card-icon{{
  width:38px; height:38px; border-radius:10px; background:{T['surface2']};
  display:flex; align-items:center; justify-content:center; color:{T['accent_bright']}; margin-bottom:10px;
}}
.tool-card-title{{ font-size:14.5px; font-weight:700; color:{T['text']}; margin-bottom:4px; }}
.tool-card-desc{{ font-size:12px; color:{T['muted']}; line-height:1.45; min-height:48px; }}

/* ---------- Empty state / friendly error cards ---------- */
.empty-state{{
  text-align:center; padding:32px 20px; background:{T['surface2']}; border:1px dashed {T['line']};
  border-radius:12px; color:{T['muted']}; font-size:13px; margin:10px 0;
}}
.empty-state svg{{ color:{T['muted2']}; margin-bottom:8px; }}
.error-card{{
  background:{T['surface2']}; border:1px solid #FB718544; border-left:4px solid #FB7185;
  border-radius:10px; padding:14px 16px; margin:10px 0; color:{T['text']}; font-size:13.5px;
}}
.error-card b{{ color:#FB7185; }}

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
div[data-testid="stFileUploaderDropzone"] button{{
  background:{T['accent_grad']} !important; color:{T['accent_text_on']} !important; border:none !important;
}}

/* Force all widget labels to the theme text color, not Streamlit's default red */
.stSlider label, .stSelectbox label, .stCheckbox label, .stRadio label,
.stTextInput label, .stFileUploader label, .stNumberInput label{{
  color:{T['text']} !important; font-weight:600 !important; font-size:13.5px !important;
}}

/* Slider — recolor from Streamlit's default red to the teal/purple accent */
.stSlider [data-baseweb="slider"]{{ margin-top:6px; }}
.stSlider [role="slider"]{{
  background-color:{T['accent']} !important; border-color:{T['accent']} !important;
  box-shadow:0 0 0 4px {T['accent']}22 !important;
}}
div[data-baseweb="slider"] > div > div{{ background:{T['accent_grad']} !important; }}
div[data-baseweb="slider"] > div{{ background:{T['line']} !important; }}
.stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"]{{ color:{T['muted2']} !important; }}
div[data-testid="stSliderThumbValue"]{{ color:{T['accent_bright']} !important; font-weight:700 !important; }}

/* Checkbox + radio accent recolor */
.stCheckbox [data-baseweb="checkbox"] span{{ border-color:{T['line']} !important; }}
.stCheckbox [aria-checked="true"] span:first-child{{ background:{T['accent']} !important; border-color:{T['accent']} !important; }}
.stRadio [aria-checked="true"] > div:first-child{{ background:{T['accent']} !important; border-color:{T['accent']} !important; }}

/* Selectbox / dropdown restyle */
div[data-baseweb="select"] > div{{
  background:{T['surface2']} !important; border-color:{T['line']} !important; border-radius:9px !important;
}}
div[data-baseweb="select"] > div:hover{{ border-color:{T['accent']} !important; }}
div[data-baseweb="popover"] li{{ font-size:13px; }}

/* Helper caption text under controls */
.control-hint{{
  font-size:12px; color:{T['muted']}; margin:-6px 0 14px 0; line-height:1.5;
  display:flex; align-items:flex-start; gap:6px;
}}
.control-hint svg{{ flex-shrink:0; margin-top:1px; color:{T['muted2']}; }}
.section-label{{
  font-size:12.5px; font-weight:700; color:{T['muted']}; text-transform:uppercase;
  letter-spacing:0.05em; margin:22px 0 4px 0; padding-top:12px; border-top:1px solid {T['line_soft']};
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

div[data-testid="stImage"]{{
  border-radius:10px; overflow:hidden; transition:transform 0.15s ease, box-shadow 0.15s ease;
}}
div[data-testid="stImage"]:hover{{ transform:scale(1.02); box-shadow:{T['shadow']}; }}
div[data-testid="stImage"] img{{ border-radius:10px; }}

/* ---------- Sidebar ---------- */
.sidebar-brand{{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
.sidebar-brand .mark{{
  width:30px; height:30px; border-radius:9px; background:{T['accent_grad']};
  display:flex; align-items:center; justify-content:center; font-size:15px;
}}
.sidebar-brand-text{{ font-size:15px; font-weight:800; color:{T['text']}; }}
.sidebar-stat{{
  background:{T['surface2']}; border:1px solid {T['line_soft']}; border-radius:10px;
  padding:10px 4px; text-align:center; margin-bottom:2px;
}}
.sidebar-stat-num{{
  font-size:19px; font-weight:800; background:{T['accent_grad']}; -webkit-background-clip:text;
  -webkit-text-fill-color:transparent; background-clip:text;
}}
.sidebar-stat-label{{ font-size:10px; color:{T['muted2']}; text-transform:uppercase; letter-spacing:0.04em; margin-top:2px; }}
section[data-testid="stSidebar"] .stButton{{ margin-bottom:2px; }}
section[data-testid="stSidebar"] .stButton button{{
  justify-content:flex-start !important; text-align:left !important; padding:8px 10px !important;
  font-size:12.5px !important; box-shadow:none !important;
}}
section[data-testid="stSidebar"] .stButton button:not([kind="primary"]){{
  background:transparent !important; color:{T['muted']} !important; border:1px solid transparent !important;
}}
section[data-testid="stSidebar"] .stButton button:not([kind="primary"]):hover{{
  background:{T['surface2']} !important; color:{T['text']} !important;
}}
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
    <div class="mark">{icon('clapperboard', 20, '#062A26')}</div>
    <div>
      <div class="editflow-title">Edit<span>Flow</span></div>
      <div class="editflow-subtitle">Batch video-editing automation — silence cuts, captions, highlights &amp; more</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:16px;">
    <span class="editflow-badge">{icon('check-circle', 13)} 10 tools online</span>
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


NAV_ITEMS = [
    ("home", "home", "Dashboard"),
    ("pipeline", "zap", "Full Pipeline"),
    ("silence", "volume-x", "Silence Cuts"),
    ("thumbs", "image", "Thumbnails"),
    ("watermark", "tag", "Watermark"),
    ("info", "clipboard", "Video Info"),
    ("rename", "folder", "Batch Rename"),
    ("scene", "film", "Scene Detect"),
    ("highlight", "clapperboard", "Highlight Reel"),
    ("grade", "palette", "Color Grade"),
    ("captions", "captions", "Captions"),
]

if "active_page" not in st.session_state:
    st.session_state.active_page = "home"


# ---------------------------------------------------------------------------
# SIDEBAR — theme toggle + processing history
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# SIDEBAR — brand, quick nav, theme toggle, session workspace
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
      <div class="mark">{icon('clapperboard', 15, '#062A26')}</div>
      <div>
        <div class="sidebar-brand-text">EditFlow</div>
        <div style="font-size:11px; color:{T['muted2']};">Video editing automation suite</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    scol1, scol2 = st.columns(2)
    with scol1:
        st.markdown(f'<div class="sidebar-stat"><div class="sidebar-stat-num">10</div><div class="sidebar-stat-label">Tools</div></div>', unsafe_allow_html=True)
    with scol2:
        st.markdown(f'<div class="sidebar-stat"><div class="sidebar-stat-num">{len(st.session_state.history)}</div><div class="sidebar-stat-label">This session</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-section-label">{icon("zap", 13)} Quick Access</div>', unsafe_allow_html=True)
    for key, icon_name, label in NAV_ITEMS:
        is_active = st.session_state.active_page == key
        if st.button(f"{icon(icon_name, 14)}  {label}", key=f"sbnav_{key}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.active_page = key
            st.rerun()

    st.markdown(f'<div class="sidebar-section-label">{icon("settings", 13)} Appearance</div>', unsafe_allow_html=True)
    theme_choice = st.radio("Theme", ["dark", "light"], index=0 if st.session_state.theme == "dark" else 1,
                             horizontal=True, label_visibility="collapsed")
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.markdown(f'<div class="sidebar-section-label">{icon("history", 13)} Session Workspace</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown(f'<div class="history-empty">{icon("inbox", 26)}<br><b>All quiet here</b><br>Run a tool and your activity will show up in this space.</div>',
                     unsafe_allow_html=True)
    else:
        for item in st.session_state.history:
            st.markdown(
                f'<div class="history-item">{icon("check-circle", 12)} {item["time"]} — <b>{item["action"]}</b><br>{item["detail"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown(f"""
    <div style="margin-top:24px; padding-top:16px; border-top:1px solid {T['line_soft']}; font-size:11px; color:{T['muted2']}; text-align:center;">
      EditFlow v1.0 · Built by <b style="color:{T['accent_bright']}">Noor Ahmed Khan</b>
    </div>
    """, unsafe_allow_html=True)


st.markdown(f"""
<div class="hero-strip">
  <span class="pill">{icon('zap', 14)} <b>10 tools</b> in one dashboard</span>
  <span class="pill">{icon('folder', 14)} <b>Batch</b> processing</span>
  <span class="pill">{icon('image', 14)} <b>Live</b> before/after preview</span>
  <span class="pill">{icon('check-circle', 14)} Runs <b>fully offline</b></span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# "Back to Dashboard" link shown at the top of every tool page
# ---------------------------------------------------------------------------
active = st.session_state.active_page

if active != "home":
    current_label = next((label for k, _, label in NAV_ITEMS if k == active), "")
    bcol1, bcol2 = st.columns([1, 8])
    with bcol1:
        if st.button(f"{icon('home', 14)}  Dashboard", key="btn_back_home", use_container_width=True):
            st.session_state.active_page = "home"
            st.rerun()
    with bcol2:
        st.markdown(f'<div style="padding-top:8px; color:{T["muted"]}; font-size:13px;">{icon("arrow-right", 13)} You\'re viewing <b style="color:{T["text"]}">{current_label}</b></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOOL CATALOG — used by the dashboard/landing grid
# ---------------------------------------------------------------------------
TOOL_CATALOG = [
    ("pipeline", "zap", "Full Pipeline", "Silence removal → scene detection → thumbnails → captions in one pass."),
    ("silence", "volume-x", "Silence Cuts", "Finds dead-air gaps in your audio track automatically."),
    ("thumbs", "image", "Thumbnails", "Scores frames by sharpness + contrast to find the best freeze-frame."),
    ("watermark", "tag", "Watermark", "Stamps a logo onto your videos, batch-applied across clips."),
    ("info", "clipboard", "Video Info", "Duration, resolution, codec & size for a whole folder at a glance."),
    ("rename", "folder", "Batch Rename", "Sorts raw footage into date-based folders with consistent naming."),
    ("scene", "film", "Scene Detect", "Flags likely cut points by comparing frame color histograms."),
    ("highlight", "clapperboard", "Highlight Reel", "Auto-stitches the loudest, most motion-heavy chunks into a reel."),
    ("grade", "palette", "Color Grade", "Applies a consistent look across clips using built-in presets."),
    ("captions", "captions", "Captions", "Transcribes speech into a ready-to-import .srt file, fully offline."),
]

if active == "home":
    st.markdown(f"""
    <div class="card" style="margin-bottom:24px;">
      <h4 style="font-size:20px;">{icon('home', 22)}&nbsp; Welcome back, Noor 👋</h4>
      <p>Pick a tool below to get started, or run the Full Pipeline to chain everything together in one pass.</p>
    </div>
    """, unsafe_allow_html=True)

    grid_cols = st.columns(5)
    for i, (key, icon_name, title, desc) in enumerate(TOOL_CATALOG):
        with grid_cols[i % 5]:
            st.markdown(f"""
            <div class="tool-card">
              <div class="tool-card-icon">{icon(icon_name, 22)}</div>
              <div class="tool-card-title">{title}</div>
              <div class="tool-card-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open  →", key=f"open_{key}", use_container_width=True):
                st.session_state.active_page = key
                st.rerun()

    st.markdown(f"""
    <div class="card" style="margin-top:8px;">
      <h4>{icon('history', 17)}&nbsp; Your session workspace</h4>
      <p>Everything you process below is tracked here for this browser session — refreshing the page clears it.
      For persistent storage, user accounts, or shareable links, this app would need real backend infrastructure
      (a database + cloud storage) connected to it.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 0. FULL PIPELINE
# ---------------------------------------------------------------------------
if active == "pipeline":
    st.markdown(f'<div class="card"><h4>{icon("zap", 18)}&nbsp; Full EditFlow Pipeline</h4>'
                '<p>Runs silence removal → scene detection → thumbnails → captions in one pass, '
                'instead of using each tool separately.</p></div>', unsafe_allow_html=True)

    file = st.file_uploader("Upload a video", type=["mp4", "mov"], key="pipeline_upload")
    hint("Upload the raw footage you want tightened up — the pipeline works on one video at a time.")
    if file:
        st.markdown('<div class="compare-label">Preview</div>', unsafe_allow_html=True)
        st.video(file)

    section_label("Silence removal")
    c1, c2 = st.columns(2)
    thresh = c1.slider("Silence threshold (dB)", -60, -10, -35, key="pipe_thresh")
    min_len = c2.slider("Minimum silence length (sec)", 0.2, 3.0, 0.6, key="pipe_minlen")
    hint("Audio quieter than the threshold, for longer than the minimum length, gets cut out automatically.")

    section_label("Captions (optional)")
    want_captions = st.checkbox("Also generate captions (slower)", value=False)
    hint("Transcribes the trimmed video's speech into an .srt subtitle file using offline AI — adds extra processing time.")
    caption_model = st.selectbox("Caption model size", ["tiny", "base", "small"], index=1,
                                  disabled=not want_captions)
    hint("Bigger models are more accurate but slower to run — \"base\" is a good default.")

    section_label("Export")
    resolution, quality = export_settings_widget("pipeline")
    hint("Controls the output video's resolution and compression — higher quality means a larger file.")

    if file and st.button("Run Full Pipeline", key="btn_pipeline"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 1. SILENCE / JUMP-CUT DETECTOR
# ---------------------------------------------------------------------------
if active == "silence":
    st.markdown(f'<div class="card"><h4>{icon("volume-x", 18)}&nbsp; Silence / Jump-Cut Detector</h4>'
                '<p>Finds dead-air gaps in your footage so you don\'t have to scrub for them by hand.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="silence_upload", accept_multiple_files=True)
    hint("You can select multiple clips at once — each one is analyzed separately.")
    if files:
        st.markdown('<div class="compare-label">Preview — first file</div>', unsafe_allow_html=True)
        st.video(files[0])

    section_label("Detection settings")
    col1, col2 = st.columns(2)
    thresh = col1.slider("Silence threshold (dB)", -60, -10, -35)
    min_len = col2.slider("Minimum silence length (sec)", 0.2, 3.0, 0.6)
    hint("Lower (more negative) threshold = stricter about what counts as \"silent\". Raise the minimum length to ignore brief pauses.")

    section_label("Export")
    resolution, quality = export_settings_widget("silence")
    export_trimmed = st.checkbox("Also export a trimmed video (not just detect)", value=False)
    hint("Leave unchecked to just see where the gaps are — check this to actually render a shortened video with them removed.")

    if files and st.button("Detect Silences", key="btn_silence"):
        try:
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
                    st.markdown(f'<div class="empty-state">{icon("inbox", 26)}<br><b>No silences found</b><br>Try lowering the threshold or reducing the minimum silence length.</div>', unsafe_allow_html=True)

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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 2. THUMBNAIL GENERATOR
# ---------------------------------------------------------------------------
if active == "thumbs":
    st.markdown(f'<div class="card"><h4>{icon("image", 18)}&nbsp; Auto-Thumbnail Generator</h4>'
                '<p>Scores frames by sharpness and contrast to surface the best freeze-frame candidates.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="thumb_upload", accept_multiple_files=True)
    hint("Works best on videos with varied shots — talking-head footage will score similarly across most frames.")
    n = st.slider("Number of candidates per video", 1, 10, 5)
    hint("How many top-scoring frames to save per video — pick a few extra so you have options to choose from.")

    if files and st.button("Generate Thumbnails", key="btn_thumb"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 3. WATERMARK
# ---------------------------------------------------------------------------
if active == "watermark":
    st.markdown(f'<div class="card"><h4>{icon("tag", 18)}&nbsp; Batch Watermark / Logo Overlay</h4>'
                '<p>Stamps a logo onto every uploaded video in the corner of your choice.</p></div>',
                unsafe_allow_html=True)
    video_files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="wm_video", accept_multiple_files=True)
    hint("Every video here gets the same logo and position applied in one batch run.")
    logo_file = st.file_uploader("Upload a logo (PNG)", type=["png"], key="wm_logo")
    hint("Use a PNG with a transparent background for the cleanest result.")

    section_label("Placement")
    position = st.selectbox("Position", list(watermark.POSITIONS.keys()))
    opacity = st.slider("Opacity", 0.1, 1.0, 0.7)
    hint("Lower opacity makes the watermark more subtle and less distracting from the footage.")

    section_label("Export")
    resolution, quality = export_settings_widget("wm")

    if video_files and logo_file and st.button("Apply Watermark", key="btn_wm"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 4. VIDEO INFO REPORT
# ---------------------------------------------------------------------------
if active == "info":
    st.markdown(f'<div class="card"><h4>{icon("clipboard", 18)}&nbsp; Video Info Report</h4>'
                '<p>Upload a batch of clips to see duration, resolution, codec, and total footage at a glance.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload one or more videos", type=["mp4", "mov"], accept_multiple_files=True, key="info_upload")
    hint("Great for getting a quick snapshot of a whole shoot before you start editing.")

    if files and st.button("Generate Report", key="btn_info"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 5. BATCH RENAME
# ---------------------------------------------------------------------------
if active == "rename":
    st.markdown(f'<div class="card"><h4>{icon("folder", 18)}&nbsp; Batch Rename &amp; Organize</h4>'
                '<p>Sorts raw camera footage into date-based folders with consistent naming.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload raw footage", type=["mp4", "mov"], accept_multiple_files=True, key="rename_upload")
    hint("Upload footage straight off the camera — filenames like DSC001.mp4 work fine.")
    project_name = st.text_input("Project name prefix", value="clip")
    hint("Files are renamed as {prefix}_{date}_{number} and sorted into folders by the date they were shot.")

    if files and st.button("Organize Footage", key="btn_rename"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 6. SCENE DETECTOR
# ---------------------------------------------------------------------------
if active == "scene":
    st.markdown(f'<div class="card"><h4>{icon("film", 18)}&nbsp; Scene Change Detector</h4>'
                '<p>Flags likely cut points by comparing color histograms between frames.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="scene_upload", accept_multiple_files=True)
    sensitivity = st.slider("Sensitivity (lower = more cuts detected)", 0.1, 0.9, 0.5)
    hint("Lower this if the tool is missing real cuts; raise it if it's flagging too many false positives.")

    if files and st.button("Detect Scene Changes", key="btn_scene"):
        try:
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
                    st.markdown(f'<div class="empty-state">{icon("inbox", 26)}<br><b>No scene changes detected</b><br>Try lowering the sensitivity slider for more cuts.</div>', unsafe_allow_html=True)
                log_history("Detected scene changes", f"{file.name} — {len(changes)} found")
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 7. HIGHLIGHT REEL
# ---------------------------------------------------------------------------
if active == "highlight":
    st.markdown(f'<div class="card"><h4>{icon("clapperboard", 18)}&nbsp; Highlight Reel Auto-Generator</h4>'
                '<p>Keeps the loudest, most motion-heavy chunks and stitches them into a rough-cut reel.</p></div>',
                unsafe_allow_html=True)
    file = st.file_uploader("Upload a video", type=["mp4", "mov"], key="highlight_upload")
    hint("Works on one video at a time — best for longer, single-take footage with varied energy.")
    if file:
        st.markdown('<div class="compare-label">Preview</div>', unsafe_allow_html=True)
        st.video(file)

    section_label("Reel settings")
    top_fraction = st.slider("Keep top % of footage", 0.1, 0.8, 0.3)
    hint("A lower percentage makes a tighter, punchier reel; higher keeps more of the original pacing.")

    section_label("Export")
    resolution, quality = export_settings_widget("hl")

    if file and st.button("Generate Highlight Reel", key="btn_highlight"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 8. COLOR GRADE
# ---------------------------------------------------------------------------
if active == "grade":
    st.markdown(f'<div class="card"><h4>{icon("palette", 18)}&nbsp; Color Grading Preset Applier</h4>'
                '<p>Applies a consistent look across clips using built-in presets.</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="grade_upload", accept_multiple_files=True)
    hint("Same preset gets applied to every clip you upload here, in one batch.")
    preset = st.selectbox("Preset", list(color_grade.PRESETS.keys()))
    hint("Cinematic darkens shadows for a filmic look; vibrant boosts saturation; muted mutes it down for a subtle grade.")

    section_label("Export")
    resolution, quality = export_settings_widget("grade")

    if files and st.button("Apply Color Grade", key="btn_grade"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# 9. AI CAPTIONS
# ---------------------------------------------------------------------------
if active == "captions":
    st.markdown(f'<div class="card"><h4>{icon("captions", 18)}&nbsp; AI Auto-Captions</h4>'
                '<p>Transcribes speech into a ready-to-import .srt file using OpenAI Whisper (runs offline).</p></div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Upload video(s)", type=["mp4", "mov"], key="caption_upload", accept_multiple_files=True)
    hint("The first run downloads the AI model (~140MB) — after that it works fully offline.")
    model_size = st.selectbox("Model size", ["tiny", "base", "small"], index=1,
                               help="Bigger = more accurate but slower")
    hint("\"Tiny\" is fastest for quick drafts; \"small\" gives noticeably better accuracy for accents or noisy audio.")

    if files and st.button("Generate Captions", key="btn_captions"):
        try:
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
        except Exception as e:
            st.markdown(f'<div class="error-card">{icon("alert-circle", 16)} <b>Something went wrong while processing.</b><br>This usually means the uploaded file format wasn\'t readable, or a required tool (ffmpeg) is missing.</div>', unsafe_allow_html=True)
            with st.expander("Show technical details"):
                st.exception(e)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="editflow-footer">
  🎬 <b>EditFlow</b> — Batch video-editing automation, built by <b>Noor Ahmed Khan</b>
</div>
""", unsafe_allow_html=True)
