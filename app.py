import os
import sys
import datetime
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ==========================================
# Streamlit Page Config
# ==========================================
st.set_page_config(
    page_title="Stock Analyst Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# Theme & Custom CSS Setup
# ==========================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# Theme Colors CSS injection
theme_css = f"""
<style>
:root {{
    --bg: {"#09090b" if IS_DARK else "#ffffff"};
    --bg-subtle: {"#0c0c0f" if IS_DARK else "#f9fafb"};
    --card: {"#0c0c0f" if IS_DARK else "#ffffff"};
    --card-hover: {"#131316" if IS_DARK else "#f4f4f5"};
    --border: {"#1e1e24" if IS_DARK else "#e4e4e7"};
    --border-subtle: {"#16161a" if IS_DARK else "#f0f0f2"};
    --text: {"#fafafa" if IS_DARK else "#09090b"};
    --text-muted: #71717a;
    --text-dim: {"#52525b" if IS_DARK else "#a1a1aa"};
    --accent: #2563eb;
    --accent-muted: #1d4ed8;
    --green: {"#22c55e" if IS_DARK else "#16a34a"};
    --green-muted: {"rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"};
    --red: {"#ef4444" if IS_DARK else "#dc2626"};
    --red-muted: {"rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"};
    --amber: {"#f59e0b" if IS_DARK else "#d97706"};
    --amber-muted: {"rgba(245,158,11,0.12)" if IS_DARK else "rgba(217,119,6,0.08)"};
    --shadow: {"none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"};
    --radius: 10px;
}}

/* Hide Streamlit chrome */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Global App Styling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}
.block-container {{
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1360px !important;
}}

/* Horizontal spacing */
[data-testid="stHorizontalBlock"] {{ gap: 1.25rem !important; }}
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stHorizontalBlock"]) {{
    margin-bottom: 0.5rem !important;
}}

/* Metric Card */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.4rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    height: 100%;
}}
.metric-label {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
    margin-bottom: 0.2rem;
}}
.metric-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.03em;
    line-height: 1.2;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.4rem;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    align-self: flex-start;
}}
.delta-up {{ color: var(--green); background: var(--green-muted); }}
.delta-down {{ color: var(--red); background: var(--red-muted); }}
.delta-warn {{ color: var(--amber); background: var(--amber-muted); }}

/* Chart Container */
.chart-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    box-shadow: var(--shadow);
    margin-bottom: 1.25rem;
}}
.chart-title {{
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
}}
.chart-subtitle {{
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-bottom: 0.8rem;
}}

/* Custom Tabs */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.835rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
    border: 1px solid transparent !important;
    border-radius: 7px !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card) !important;
    border-color: var(--border) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 3px;
    margin-bottom: 1rem;
}}

/* Custom markdown tables */
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.8rem;
    margin-top: 0.5rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.6rem 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg-subtle);
}}
.data-table td {{
    padding: 0.65rem 0.8rem;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}

/* Badges */
.badge {{
    display: inline-block;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
}}
.badge-green {{ color: var(--green); background: var(--green-muted); }}
.badge-red {{ color: var(--red); background: var(--red-muted); }}
.badge-amber {{ color: var(--amber); background: var(--amber-muted); }}
.badge-blue {{ color: var(--accent); background: rgba(37,99,235,0.1); }}

/* Card layout wrapper */
.card-content {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1.25rem;
}}

/* Button styling overrides to ensure text visibility */
div.stButton > button, div.stFormSubmitButton > button, button[key="api_key_dialog_btn"], button[key="theme_toggle_btn"] {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease-in-out !important;
}}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
    background-color: var(--card-hover) !important;
    border-color: var(--accent) !important;
    color: var(--text) !important;
}}
/* Ensure form submit button stands out with accent color and white text */
div.stFormSubmitButton > button {{
    background-color: var(--accent) !important;
    color: #ffffff !important;
    border: 1px solid var(--accent-muted) !important;
}}
div.stFormSubmitButton > button:hover {{
    background-color: var(--accent-muted) !important;
    color: #ffffff !important;
}}
/* Text Input legibility overrides */
div[data-testid="stTextInput"] input {{
    background-color: var(--bg-subtle) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}}
div[data-testid="stTextInput"] input:focus {{
    border-color: var(--accent) !important;
}}
/* Selectbox legibility overrides */
div[data-testid="stSelectbox"] > div {{
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] {{
    background-color: var(--card) !important;
    color: var(--text) !important;
}}
div[data-testid="stSelectbox"] div[role="button"] {{
    color: var(--text) !important;
}}

/* Global Dialog Theme Overrides */
div[data-testid="stDialog"] [role="dialog"], div[data-testid="stDialog"] > div {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}}
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] h4, div[data-testid="stDialog"] p, div[data-testid="stDialog"] span, div[data-testid="stDialog"] label, div[data-testid="stDialog"] li, div[data-testid="stDialog"] code, div[data-testid="stDialog"] button {{
    color: var(--text) !important;
}}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=40, r=10, t=20, b=30),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a"),
    ),
)

# Helper for metric cards
def metric_card(label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else "→")
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# Gemini API Key Setup & Dual-Key Config
# ==========================================
# Helper to get secrets from st.secrets (Streamlit Cloud) or os.getenv (.env)
def get_secret(key_name, default=""):
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return str(st.secrets[key_name])
    except Exception:
        pass
    return os.getenv(key_name, default)

key1 = get_secret("GEMINI_API_KEY_1", get_secret("GEMINI_API_KEY", ""))
key2 = get_secret("GEMINI_API_KEY_2", "")
usage1 = int(get_secret("GEMINI_API_KEY_1_USAGE", "0"))
usage2 = int(get_secret("GEMINI_API_KEY_2_USAGE", "0"))
selected_key = get_secret("GEMINI_API_KEY_SELECTED", "1")

if "api_key_1" not in st.session_state:
    st.session_state.api_key_1 = key1
if "api_key_2" not in st.session_state:
    st.session_state.api_key_2 = key2
if "api_key_1_usage" not in st.session_state:
    st.session_state.api_key_1_usage = usage1
if "api_key_2_usage" not in st.session_state:
    st.session_state.api_key_2_usage = usage2
if "api_key_selected" not in st.session_state:
    st.session_state.api_key_selected = selected_key

# Active key resolution
active_key = st.session_state.api_key_1 if st.session_state.api_key_selected == "1" else st.session_state.api_key_2

# ==========================================
# Gemini API Key Dialog & Persistence
# ==========================================
def save_api_keys_to_env(k1, k2, u1, u2, sel):
    env_file = ".env"
    lines = []
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            pass
            
    configs = {
        "GEMINI_API_KEY_1": k1,
        "GEMINI_API_KEY_2": k2,
        "GEMINI_API_KEY_1_USAGE": str(u1),
        "GEMINI_API_KEY_2_USAGE": str(u2),
        "GEMINI_API_KEY_SELECTED": sel
    }
    
    new_lines = []
    written_keys = set()
    
    for line in lines:
        stripped = line.strip()
        matched = False
        for cfg_key in configs:
            if stripped.startswith(f"{cfg_key}="):
                new_lines.append(f"{cfg_key}={configs[cfg_key]}\n")
                written_keys.add(cfg_key)
                matched = True
                break
        if not matched:
            if stripped.startswith("GEMINI_API_KEY="):
                active = k1 if sel == "1" else k2
                new_lines.append(f"GEMINI_API_KEY={active}\n")
            else:
                new_lines.append(line)
                
    for cfg_key in configs:
        if cfg_key not in written_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(f"{cfg_key}={configs[cfg_key]}\n")
            
    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass

@st.dialog("Gemini API Key 설정 (듀얼 키 관리)")
def set_api_key_dialog():
    st.markdown("분석에 사용할 두 개의 **Gemini API Key**를 관리하고 선택할 수 있습니다.")
    
    selected_idx = st.radio(
        "사용할 API Key 선택", 
        options=["1", "2"], 
        format_func=lambda x: f"API Key {x}", 
        index=0 if st.session_state.api_key_selected == "1" else 1,
        key="dialog_key_choice"
    )
    
    st.markdown("---")
    st.markdown(f"**🔑 API Key 1** (현재 사용 횟수: `{st.session_state.api_key_1_usage}` 회)")
    new_key1 = st.text_input("API Key 1 입력", value=st.session_state.api_key_1, type="password", placeholder="AIzaSy...", key="input_key1")
    
    st.markdown("---")
    st.markdown(f"**🔑 API Key 2** (현재 사용 횟수: `{st.session_state.api_key_2_usage}` 회)")
    new_key2 = st.text_input("API Key 2 입력", value=st.session_state.api_key_2, type="password", placeholder="AIzaSy...", key="input_key2")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1.5, 1.5, 1])
    with col1:
        if st.button("저장 & 적용", use_container_width=True, key="save_key_btn"):
            st.session_state.api_key_1 = new_key1
            st.session_state.api_key_2 = new_key2
            st.session_state.api_key_selected = selected_idx
            save_api_keys_to_env(new_key1, new_key2, st.session_state.api_key_1_usage, st.session_state.api_key_2_usage, selected_idx)
            st.success("설정이 저장되었습니다!")
            st.rerun()
    with col2:
        if st.button("사용 횟수 초기화", use_container_width=True, key="reset_usage_btn"):
            st.session_state.api_key_1_usage = 0
            st.session_state.api_key_2_usage = 0
            save_api_keys_to_env(st.session_state.api_key_1, st.session_state.api_key_2, 0, 0, st.session_state.api_key_selected)
            st.warning("사용 횟수가 초기화되었습니다!")
            st.rerun()
    with col3:
        if st.button("취소", use_container_width=True, key="cancel_key_btn"):
            st.rerun()

# Text highlighting function to colorize the markdown content beautifully
def get_colorful_report(text):
    import re
    replacements = {
        r'(\*\*보유\(Hold\)\*\*)': r'<span style="color: #f59e0b; font-weight: bold; background: rgba(245,158,11,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        r'(\*\*Hold\*\*)': r'<span style="color: #f59e0b; font-weight: bold; background: rgba(245,158,11,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        r'(\*\*매수\(Buy\)\*\*)': r'<span style="color: #22c55e; font-weight: bold; background: rgba(34,197,94,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        r'(\*\*Buy\*\*)': r'<span style="color: #22c55e; font-weight: bold; background: rgba(34,197,94,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        r'(\*\*매도\(Sell\)\*\*)': r'<span style="color: #ef4444; font-weight: bold; background: rgba(239,68,68,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        r'(\*\*Sell\*\*)': r'<span style="color: #ef4444; font-weight: bold; background: rgba(239,68,68,0.12); padding: 2px 6px; border-radius: 4px;">\1</span>',
        
        r'(\*\*긍정적 촉매\*\*)': r'<span style="color: #22c55e; font-weight: bold;">\1</span>',
        r'(\*\*주요 위험\*\*)': r'<span style="color: #ef4444; font-weight: bold;">\1</span>',
        r'(\*\*리스크 요인\*\*)': r'<span style="color: #ef4444; font-weight: bold;">\1</span>',
        r'(\*\*목표 주가\*\*)': r'<span style="color: #2563eb; font-weight: bold;">\1</span>',
        r'(\*\*상승\*\*)': r'<span style="color: #22c55e; font-weight: bold;">\1</span>',
        r'(\*\*하락\*\*)': r'<span style="color: #ef4444; font-weight: bold;">\1</span>',
        r'(\*\*영업이익\*\*)': r'<span style="color: #2563eb; font-weight: bold;">\1</span>',
        r'(\*\*매출액\*\*)': r'<span style="color: #2563eb; font-weight: bold;">\1</span>',
        r'(\*\*잉여현금흐름\*\*)': r'<span style="color: #22c55e; font-weight: bold;">\1</span>',
    }
    
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    return text

@st.dialog("📋 투자 분석 보고서 뷰어", width="large")
def open_report_viewer_dialog(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        colorful_content = get_colorful_report(content)
        
        # Hardcode color parameters based on IS_DARK to bypass Streamlit dialog theme isolation
        txt_color = "#fafafa" if IS_DARK else "#09090b"
        bg_color = "#0c0c0f" if IS_DARK else "#ffffff"
        border_color = "#1e1e24" if IS_DARK else "#e4e4e7"
        bg_subtle_color = "#16161a" if IS_DARK else "#f9fafb"
        accent_color = "#2563eb"
        
        st.markdown(f"""
        <div style="font-size: 0.82rem; color: #71717a; margin-bottom: 0.8rem; padding: 4px 8px; background: {bg_subtle_color}; border-radius: 6px; border: 1px solid {border_color};">
            📄 열린 파일: <code>{filepath}</code>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <style>
        /* Force dialog box main wrapper backgrounds and foregrounds */
        div[data-testid="stDialog"] [role="dialog"], div[data-testid="stDialog"] > div {{
            background-color: {bg_color} !important;
            color: {txt_color} !important;
            border: 1px solid {border_color} !important;
        }}
        div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] h4, div[data-testid="stDialog"] p, div[data-testid="stDialog"] span, div[data-testid="stDialog"] label, div[data-testid="stDialog"] li, div[data-testid="stDialog"] code {{
            color: {txt_color} !important;
        }}
        
        /* Report text styles */
        .report-viewer-text {{
            color: {txt_color} !important;
        }}
        .report-viewer-text h1, .report-viewer-text h2, .report-viewer-text h3 {{
            color: {accent_color} !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.8rem !important;
            font-weight: 700 !important;
        }}
        .report-viewer-text h2 {{
            border-bottom: 2px solid {border_color};
            padding-bottom: 0.4rem;
        }}
        .report-viewer-text h3 {{
            border-bottom: 1px solid {border_color};
            padding-bottom: 0.2rem;
            color: #60a5fa !important;
        }}
        .report-viewer-text table {{
            width: 100% !important;
            margin: 1rem 0 !important;
            border-collapse: collapse !important;
        }}
        .report-viewer-text th {{
            background-color: {bg_subtle_color} !important;
            color: {accent_color} !important;
            font-weight: bold !important;
            border: 1px solid {border_color} !important;
            padding: 8px !important;
        }}
        .report-viewer-text td {{
            border: 1px solid {border_color} !important;
            padding: 8px !important;
            color: {txt_color} !important;
            background-color: {bg_color} !important;
        }}
        .report-viewer-text ul, .report-viewer-text ol {{
            padding-left: 1.5rem !important;
            margin-bottom: 1rem !important;
        }}
        .report-viewer-text li {{
            margin-bottom: 0.4rem !important;
            color: {txt_color} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="report-viewer-text">{colorful_content}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col_dlg1, col_dlg2 = st.columns([1, 1])
        with col_dlg1:
            st.download_button("📥 파일 다운로드 (.md)", data=content, file_name=os.path.basename(filepath), mime="text/markdown", use_container_width=True, key="download_viewer_dialog_btn")
        with col_dlg2:
            if st.button("닫기", use_container_width=True, key="close_viewer_dialog"):
                st.rerun()
    except Exception as e:
        st.error(f"보고서를 읽는 중 에러가 발생했습니다: {str(e)}")

# ==========================================
# Header Configuration
# ==========================================
head_left, head_api, head_right = st.columns([7.2, 1.4, 1.4])
with head_left:
    st.markdown("""
    <div style='display:flex; align-items:center; gap: 8px; margin-bottom: 1.5rem;'>
        <span style='font-size: 1.8rem; font-weight: 700; color: var(--text); letter-spacing: -0.04em;'>◆ Stock Analyst Dashboard</span>
        <span style='font-size: 0.72rem; padding: 2px 8px; background: var(--accent); color: white; border-radius: 6px; font-weight: 600;'>LIVE</span>
    </div>
    """, unsafe_allow_html=True)
with head_api:
    if st.button("🔑 API Key 설정", use_container_width=True, key="api_key_dialog_btn"):
        set_api_key_dialog()
with head_right:
    theme_label = "☀️ Light" if IS_DARK else "🌙 Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True, key="theme_toggle_btn")

# ==========================================
# Core Analysis Logic Functions (Cached)
# ==========================================
@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_data
def get_stock_ticker(stock_name, _client):
    import re
    # If the input itself looks like a ticker (e.g., letters, numbers, dot, hyphen, e.g. AAPL, 005930.KS, TSLA, 000660.KS)
    # check if yfinance can retrieve price data directly to bypass the LLM lookup.
    if re.match(r'^[A-Za-z0-9\.\-]+$', stock_name):
        try:
            ticker_obj = yf.Ticker(stock_name)
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                return stock_name.upper()
        except Exception:
            pass

    prompt = f"""
    Please search and return the Yahoo Finance ticker symbol for the company or stock named '{stock_name}'.
    Respond with ONLY the exact ticker symbol (e.g. AAPL, 005930.KS, TSLA, 000660.KS, NVDA, 1810.HK) and nothing else.
    If the stock is listed on a specific market, make sure the suffix is correct (e.g., .KS for KOSPI, .KQ for KOSDAQ, .T for Tokyo, etc.).
    Do not write any markdown blocks, quotes, or additional text. Just return the ticker string.
    """
    import time
    max_retries = 3
    last_err = None
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip().replace("`", "").replace("'", "").replace('"', '').strip()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
    
    if last_err:
        raise last_err
    return None

@st.cache_data
def analyze_price_and_financials(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period="5d")
        
        # Price movement
        direction, pct_change, last_close = "보합", 0.0, 0.0
        if not history.empty:
            last_close = history['Close'].iloc[-1]
            if len(history) >= 2:
                prev_close = history['Close'].iloc[-2]
                diff = last_close - prev_close
                pct_change = (diff / prev_close) * 100
                direction = "상승" if diff >= 0 else "하락"
                
        # Financials
        info = stock.info
        company_name = info.get('longName') or info.get('shortName') or ticker_symbol
        currency = info.get('currency', 'USD')
        
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        q_financials = stock.quarterly_financials
        q_cashflow = stock.quarterly_cashflow
        
        valuation_metrics = {
            'Current Price': info.get('currentPrice') or last_close,
            'Market Cap': info.get('marketCap'),
            'Trailing P/E': info.get('trailingPE'),
            'Forward P/E': info.get('forwardPE'),
            'P/S (Trailing)': info.get('priceToSalesTrailing12Months'),
            'P/B': info.get('priceToBook'),
            'EV/EBITDA': info.get('enterpriseToEbitda'),
            'Currency': currency
        }
        
        raw_data = f"""
        Company Name: {company_name}
        Ticker: {ticker_symbol}
        Currency: {currency}
        [Valuation Metrics] {valuation_metrics}
        [Financials (Annual)] {financials.to_string() if not financials.empty else 'N/A'}
        [Balance Sheet (Annual)] {balance_sheet.to_string() if not balance_sheet.empty else 'N/A'}
        [Cash Flow (Annual)] {cashflow.to_string() if not cashflow.empty else 'N/A'}
        """
        
        # Format df for dynamic Plotly visualization
        chart_data = {}
        if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
            chart_data['FCF'] = cashflow.loc['Free Cash Flow']
        elif not cashflow.empty and 'Operating Cash Flow' in cashflow.index and 'Capital Expenditure' in cashflow.index:
            chart_data['FCF'] = cashflow.loc['Operating Cash Flow'] + cashflow.loc['Capital Expenditure'] # Capex is negative in yfinance
            
        if not financials.empty and 'Total Revenue' in financials.index:
            chart_data['Revenue'] = financials.loc['Total Revenue']
        if not financials.empty and 'Operating Income' in financials.index:
            chart_data['Operating Income'] = financials.loc['Operating Income']
            
        return company_name, raw_data, valuation_metrics, direction, pct_change, last_close, chart_data, financials, balance_sheet, cashflow
    except Exception as e:
        return ticker_symbol, f"yfinance data fetch failed: {str(e)}", {}, "알수없음", 0.0, 0.0, {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data
def fetch_analysis_report(stock_name, ticker, direction, pct_change, last_close, company_name, raw_financials, _client):
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2
    )
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
    당신은 글로벌 투자은행의 수석 주식 애널리스트이자 포트폴리오 매니저입니다.
    다음 주식에 대해 실시간 뉴스 검색 및 수집된 재무제표 데이터를 결합하여 최고 품질의 한국어 종합 투자 분석 보고서를 작성해 주세요.
    보고서는 상세하고 객관적이며 데이터 기반(지난 5개년 회계연도 및 TTM 기준)이어야 합니다.
    
    [분석 대상 종목 정보]
    - 입력된 종목명: {stock_name}
    - Yahoo Finance 티커: {ticker}
    - 기업명: {company_name}
    - 최근 종가: {last_close}
    - 최근 2거래일 대비 주가 변동: {direction} ({pct_change:+.2f}%)
    - 현재 분석 기준 시간: {current_time}
    
    [yfinance 수집 원본 재무 데이터]
    {raw_financials}
    
    --------------------------------------------------
    [작성 요구사항]
    
    1. 최신 뉴스 실시간 검색 및 요약:
       - Google Search를 사용하여 해당 종목의 최신 뉴스(실시간)를 검색하세요.
       - 주가가 최근 {direction}한 원인(상승 이유 또는 하락 이유)을 분석하여 요약해 주세요.
       - 최근 뉴스들을 날짜별로 명확하게 요약하여 출력해 주세요.
       
    2. 아래 구조를 따르는 상세 "분석 보고서"를 작성해 주세요:
       
       요약:
       - 주요 긍정적 촉매(Positive Catalysts)와 주요 위험(Key Risks) 요약.
       
       1. 재무 성과 및 건전성:
          - 손익계산서 분석: 지난 5년 + TTM 동안의 매출 성장, 매출 총이익률, 영업 이익률 및 순이익률 추세를 분석합니다. (yfinance 데이터에 5개년 미만인 경우, 실시간 검색을 활용하여 지난 5개년 수치를 최대한 보완해 주세요.)
          - 대차대조표 분석: 회사의 부채 수준, 부채 대 자기자본 비율(D/E), 유동 비율(Current Ratio) 및 현금 포지션을 평가하고, 대차대조표가 종합적으로 강한지 약한지 결론을 내립니다.
          - 현금 흐름 분석: 영업 현금 흐름, 자본 지출(CapEx) 및 잉여 현금 흐름(FCF) 발생을 분석합니다. 회사가 지속적으로 FCF가 긍정적인지 평가합니다.
          
       2. 가치 평가 (Valuation):
          - 배수 분석: 회사의 현재 P/E, P/S, P/B 및 EV/EBITDA 비율을 다음 세 가지와 정량적으로 비교 분석합니다:
            (a) 회사의 자체 5년 평균 배수
            (b) 해당 업계 평균 배수
            (c) 상위 3개 직접 경쟁사(예: [Competitor A], [Competitor B], [Competitor C])의 배수
            (경쟁사 3곳을 직접 찾아서 구체적인 티커 및 배수를 비교해 주세요. yfinance에 없는 과거 평균이나 경쟁사 배수 등은 구글 검색을 활용하십시오.)
          - 결론: 이 분석을 바탕으로 주식이 현재 과대 평가(Overvalued), 과소 평가(Undervalued) 또는 적정 가격(Fairly valued)인지 결론을 내립니다.
          
       3. 비즈니스 모델 및 경쟁 우위:
          - 사업 부문: 회사의 핵심 사업 부문과 매출에 대한 각 부문의 기여도를 간략하게 설명합니다.
          - 경제적 해자(Moat): 경쟁 우위의 원천(예: 브랜드, 특허, 네트워크 효과, 원가 경쟁력)을 식별하고 설명합니다. 이 해자의 지속성과 강점을 평가합니다.
          
       4. 성장 전략 및 미래 전망:
          - 성장 동력: 미래 성장을 촉진할 것으로 예상되는 주요 촉매(예: 신제품, 시장 확장, 산업 동향)를 식별합니다.
          - market 기회: 총 유효 시장(TAM)과 회사가 더 큰 시장 점유율을 확보할 수 있는 잠재력을 분석합니다.
          
       5. 경영진 및 거버넌스:
          - 리더십: CEO 및 수석 경영진에 대한 간략한 개요를 제공합니다. 재임 기간과 실적에 대해 언급합니다.
          - 자본 배분: 자본 배분에 대한 경영진의 효율성을 평가합니다. 배당, 자사주 매입 및 M&A 활동과 관련된 정책을 검토합니다.
          - 내부자 소유: 내부자 소유(Insider Ownership) 수준을 기록 및 평가합니다.
          
       6. 위험 분석:
          - 특이적 위험(Idiosyncratic Risks): 회사와 관련된 상위 3가지 위험은 무엇입니까(예: 제품 실패, 핵심 인물 위험, 소송)?
          - 체계적 위험(Systematic Risks): 상위 3가지 외부 위험은 무엇입니까(예: 경기 침체, 금리/규제 변경, 경쟁적 혼란)?
          
       7. ETF 및 매크로 분석:
          - 시장 및 산업 분야의 중장기 변화 정보를 기술하십시오. 최신 자료 기반 매크로(금리, 물가, 고용, 정책, 지정학)의 변화, 섹터(반도체, 금융, 에너지 등 구조 변화)의 움직임을 고려합니다.
          
       8. 최종 권장 사항:
          - 위의 모든 사항을 최종 투자 결론으로 종합합니다. 현재 가격에서 기회와 위험의 균형을 바탕으로 간결한 정당성과 함께 매수(Buy)/보유(Hold)/매도(Sell) 등급을 명확히 명시해 주세요.
          
    3. 종합 요약 개요 및 투자 테제 (보고서 가장 위에 위치하거나 아래의 지정된 양식으로 제공해 주세요):
       - 보고서 전면에 회사의 사업에 대한 간략한 개요를 제공합니다.
       - 전반적인 투자 테제(Thesis)를 2~3문장으로 명확히 진술합니다.
       - 현재 가치 평가 대비 매수(Buy), 보유(Hold) 또는 매도(Sell) 의견과 적정 목표가(또는 상승 여력)에 대한 최종 결론을 1개의 문장으로 정리하십시오.
 
    출력되는 마크다운의 퀄리티가 매우 높아야 하며, 구글 검색을 통한 정확한 실시간 출처 정보를 기반으로 작성되어야 합니다.
    """
    
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 3) # 3초, 6초 지수 대기
            else:
                return f"Gemini 분석 보고서 생성 실패: {str(e)}\n\n(참고: 구글 제미나이 서버 부하가 높습니다. 10~20초 후에 다시 '실시간 분석 실행'을 클릭해 주세요.)"

# ==========================================
# Report Viewer Section
# ==========================================
st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
st.markdown("""
<div class="card-content" style="margin-top: 0rem; margin-bottom: 1rem;">
    <div style="font-size: 1.05rem; font-weight: 700; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 0.8rem; display:flex; align-items:center; gap: 8px;">
        <span>📁 생성된 분석 보고서 뷰어 (Report Viewer)</span>
    </div>
""", unsafe_allow_html=True)

import glob
report_files = sorted(glob.glob("*_investment_report_*.md"), reverse=True)
legacy_files = sorted(glob.glob("*_investment_report.md"), reverse=True)
all_report_files = report_files + legacy_files

if all_report_files:
    col_sel, col_open_btn, col_del_btn = st.columns([6.0, 2.3, 1.7])
    with col_sel:
        selected_file = st.selectbox("불러올 보고서 선택", all_report_files, key="viewer_file_selectbox", label_visibility="collapsed")
    with col_open_btn:
        if st.button("📄 열기", use_container_width=True, key="open_report_dialog_btn"):
            if selected_file:
                open_report_viewer_dialog(selected_file)
    with col_del_btn:
        if st.button("🗑️ 삭제", use_container_width=True, key="delete_report_btn"):
            if selected_file and os.path.exists(selected_file):
                try:
                    os.remove(selected_file)
                    st.toast(f"보고서가 삭제되었습니다: {selected_file}")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {str(e)}")
else:
    st.info("현재 디렉토리에 생성된 투자 분석 보고서(*_investment_report*.md)가 없습니다. 상단에서 종목 분석을 먼저 실행해 보세요.")
st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# UI Layout: User Input Controller
# ==========================================
st.markdown("""
<div class="card-content" style="margin-bottom: 1.5rem;">
    <div style="font-size: 0.85rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem;">📈 분석할 주식 종목 검색</div>
</div>
""", unsafe_allow_html=True)

# Form to input and run analysis
with st.form("search_form"):
    col_stock, col_btn = st.columns([8.2, 1.8])
    with col_stock:
        stock_input = st.text_input("종목명 입력", placeholder="예: 삼성전자, 애플, NVIDIA, Tesla...", label_visibility="collapsed")
    with col_btn:
        submit_btn = st.form_submit_button("실시간 분석 실행", use_container_width=True)

# Main Processing Flow
if submit_btn and stock_input:
    if not active_key:
        st.error("❌ Gemini API Key가 설정되지 않았습니다. 우측 상단의 '🔑 API Key 설정' 버튼을 눌러 키를 설정해 주세요.")
    else:
        client = get_gemini_client(active_key)
        
        try:
            # 1. Fetch Ticker
            ticker = get_stock_ticker(stock_input, client)
            if not ticker:
                st.error(f"❌ '{stock_input}'에 대한 야후 파이낸스 티커를 찾지 못했습니다. 올바른 이름이나 영문 명칭을 입력해 보세요.")
            else:
                st.session_state.current_ticker = ticker
                st.session_state.stock_name = stock_input
                
                # 2. Fetch yfinance data
                with st.spinner("야후 파이낸스에서 재무 정보를 실시간으로 수집하고 있습니다..."):
                    company_name, raw_financials, valuation_metrics, direction, pct_change, last_close, chart_data, financials, balance, cashflow = analyze_price_and_financials(ticker)
                    
                    st.session_state.company_name = company_name
                    st.session_state.valuation_metrics = valuation_metrics
                    st.session_state.direction = direction
                    st.session_state.pct_change = pct_change
                    st.session_state.last_close = last_close
                    st.session_state.chart_data = chart_data
                    st.session_state.financials_df = financials
                    st.session_state.balance_df = balance
                    st.session_state.cashflow_df = cashflow
                    
                # 3. Fetch Gemini Analysis Report
                with st.spinner("Gemini 2.5 Flash가 실시간 뉴스 및 매크로 시장 동향을 검색하여 보고서를 작성하는 중입니다..."):
                    report = fetch_analysis_report(stock_input, ticker, direction, pct_change, last_close, company_name, raw_financials, client)
                    st.session_state.report_content = report
                    
                    # Increment usage count for active key
                    if st.session_state.api_key_selected == "1":
                        st.session_state.api_key_1_usage += 1
                    else:
                        st.session_state.api_key_2_usage += 1
                    save_api_keys_to_env(
                        st.session_state.api_key_1,
                        st.session_state.api_key_2,
                        st.session_state.api_key_1_usage,
                        st.session_state.api_key_2_usage,
                        st.session_state.api_key_selected
                    )
        except Exception as e:
            # Clear state keys on failure to prevent displaying stale/mismatched data
            for key in ["current_ticker", "stock_name", "company_name", "valuation_metrics", "direction", "pct_change", "last_close", "chart_data", "report_content"]:
                if key in st.session_state:
                    del st.session_state[key]
            err_msg = str(e)
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                st.error(f"❌ Gemini API 호출 한도가 초과되었습니다 (RESOURCE_EXHAUSTED). 사용 중인 API 키의 무료 할당량(하루 20회 또는 분당 제한)이 소진되었습니다. 다른 API 키로 변경하시거나, 유료 결제 계정의 키를 사용해주세요. (상세 오류: {err_msg})")
            elif "API_KEY_INVALID" in err_msg or "invalid" in err_msg.lower():
                st.error(f"❌ 입력하신 Gemini API Key가 올바르지 않거나 유효하지 않습니다. 올바른 API 키를 입력해 주세요. (상세 오류: {err_msg})")
            else:
                st.error(f"❌ 종목 분석 중 오류가 발생했습니다: {err_msg}")

# Check if data exists in state
if "current_ticker" in st.session_state and "report_content" in st.session_state:
    ticker = st.session_state.current_ticker
    stock_name = st.session_state.stock_name
    company_name = st.session_state.company_name
    valuation_metrics = st.session_state.valuation_metrics
    direction = st.session_state.direction
    pct_change = st.session_state.pct_change
    last_close = st.session_state.last_close
    chart_data = st.session_state.chart_data
    report_content = st.session_state.report_content
    
    # Save Report File locally
    import datetime
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    output_filename = f"{ticker.replace('.', '_')}_investment_report_{today_str}.md"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report_content)
    except Exception:
        pass

    # ==========================================
    # KPI Metrics Cards (Row of 4)
    # ==========================================
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta_label = f"{direction} ({pct_change:+.2f}%)"
        delta_type = "up" if direction == "상승" else ("down" if direction == "하락" else "warn")
        metric_card("현재 주가", f"{last_close:,.2f} {valuation_metrics.get('Currency', 'USD')}", delta=delta_label, delta_type=delta_type)
    with c2:
        market_cap_val = valuation_metrics.get('Market Cap')
        market_cap_str = f"{market_cap_val / 1e12:,.2f}T" if market_cap_val else "N/A"
        metric_card("시가 총액", market_cap_str)
    with c3:
        pe_val = valuation_metrics.get('Trailing P/E') or valuation_metrics.get('Forward P/E')
        pe_str = f"{pe_val:,.2f}x" if pe_val else "N/A"
        metric_card("P/E Ratio", pe_str)
    with c4:
        pb_val = valuation_metrics.get('P/B')
        pb_str = f"{pb_val:,.2f}x" if pb_val else "N/A"
        metric_card("P/B Ratio", pb_str)
        
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # Plotly Charts Row
    # ==========================================
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">연간 매출 & 영업이익 추세</div>
            <div class="chart-subtitle">yfinance 기반 수집된 최근 연도별 추이 (십만/백만 단위)</div>
        """, unsafe_allow_html=True)
        
        if 'Revenue' in chart_data and 'Operating Income' in chart_data:
            rev = chart_data['Revenue'].dropna().iloc[::-1] # Reverse for chronological order
            op = chart_data['Operating Income'].dropna().iloc[::-1]
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=rev.index.map(lambda x: str(x)[:4] if hasattr(x, 'year') else str(x)),
                y=rev.values,
                name="매출액",
                marker_color="#2563eb",
                opacity=0.85
            ))
            fig1.add_trace(go.Scatter(
                x=op.index.map(lambda x: str(x)[:4] if hasattr(x, 'year') else str(x)),
                y=op.values,
                name="영업이익",
                line=dict(color="#22c55e", width=3),
                mode='lines+markers'
            ))
            fig1.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("매출 및 영업이익 차트를 그리기 위한 연간 데이터가 충분하지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_c2:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">연간 잉여현금흐름(FCF) 추세</div>
            <div class="chart-subtitle">영업현금흐름에서 Capex를 제하고 남은 잉여현금흐름</div>
        """, unsafe_allow_html=True)
        
        if 'FCF' in chart_data:
            fcf = chart_data['FCF'].dropna().iloc[::-1]
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=fcf.index.map(lambda x: str(x)[:4] if hasattr(x, 'year') else str(x)),
                y=fcf.values,
                name="잉여현금흐름(FCF)",
                marker_color=["#ef4444" if x < 0 else "#22c55e" for x in fcf.values],
                opacity=0.85
            ))
            fig2.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("잉여현금흐름 차트를 그리기 위한 FCF 데이터가 충분하지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # Full Investment Report Markdown
    # ==========================================
    col_rep_title, col_rep_dl = st.columns([7.5, 2.5])
    with col_rep_title:
        st.markdown("""
        <div style="font-size: 1.05rem; font-weight: 700; color: var(--text); padding-top: 4px;">
            📋 애널리스트 종합 투자 분석 보고서
        </div>
        """, unsafe_allow_html=True)
    with col_rep_dl:
        st.download_button(
            label="📥 보고서 파일 다운로드",
            data=report_content,
            file_name=output_filename,
            mime="text/markdown",
            use_container_width=True,
            key="download_main_report_btn"
        )
    st.markdown("<div style='border-bottom: 1px solid var(--border); margin-bottom: 1rem; margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    
    st.markdown(report_content)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    # Default State Message
    st.markdown(f"""
    <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; padding: 4rem; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); text-align:center;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>📈</div>
        <div style='font-size: 1.15rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem;'>대시보드를 활성화하기 위해 종목 분석을 실행해 주세요</div>
        <div style='font-size: 0.8rem; color: var(--text-muted); max-width: 500px;'>
            상단의 입력 폼에 분석하고자 하는 주식 종목명(예: 삼성전자, 애플, NVIDIA 등)을 기재하고 <b>"실시간 분석 실행"</b> 버튼을 누르면 정밀 재무 분석 차트와 요약 뉴스가 오픈됩니다.
        </div>
    </div>
    """, unsafe_allow_html=True)


