import streamlit as st
import requests, time
import textwrap
import pandas as pd
import plotly.graph_objects as go

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SmartHome — Energy Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] * { color: #7d8590 !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.88rem; padding: 5px 0; color: #c9d1d9 !important;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #2dd4bf !important; }

.block-container { padding: 2rem 2.5rem; max-width: 1400px; background: #0d1117; }

.page-header { border-bottom: 1px solid #21262d; padding-bottom: 14px; margin-bottom: 24px; }
.page-header h2 { font-size: 1.45rem; font-weight: 700; color: #e6edf3; margin: 0; letter-spacing: -0.02em; }
.page-header p  { font-size: 0.82rem; color: #7d8590; margin: 5px 0 0 0; }

.section-title {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #2dd4bf; margin: 28px 0 12px 0;
    border-left: 3px solid #2dd4bf; padding-left: 8px;
}

.floorplan-wrap { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 24px; }
.compass { text-align: center; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.18em; color: #2dd4bf; margin-bottom: 8px; }
.wall { background: #30363d; }
.room-cell {
    background: #0d1117; border: 1.5px solid #21262d; padding: 12px 8px;
    text-align: center; min-height: 100px; display: flex; flex-direction: column;
    justify-content: center; gap: 4px; transition: border-color 0.2s, background 0.2s;
}
.room-cell:hover  { border-color: #2dd4bf; background: #0d1f1e; }
.room-cell.warn   { border-color: #d29922; background: #1a1500; }
.room-cell.alert  { border-color: #f85149; background: #1a0a0a; }
.room-cell.real   { border-color: #3fb950; background: #0a1a0d; }
.room-name  { font-size: 0.78rem; font-weight: 700; color: #e6edf3; }
.room-temp  { font-size: 0.72rem; color: #7d8590; }
.room-power { font-size: 0.72rem; font-weight: 600; }
.room-apps  { font-size: 0.65rem; color: #484f58; }
.entrance-gap { width: 56px; height: 5px; background: #0d1117; border-bottom: 2px dashed #2dd4bf; }

.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; }
.badge-on  { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.badge-off { background: rgba(248,81,73,0.12);  color: #f85149; border: 1px solid rgba(248,81,73,0.3); }

.alert-box { border-radius: 8px; padding: 14px 18px; font-size: 0.84rem; font-weight: 500; margin-top: 8px; line-height: 1.5; }
.alert-danger  { background: rgba(248,81,73,0.1);  border: 1px solid rgba(248,81,73,0.35);  color: #ffa198; }
.alert-warning { background: rgba(210,153,34,0.1); border: 1px solid rgba(210,153,34,0.35); color: #e3b341; }
.alert-info    { background: rgba(45,212,191,0.08);border: 1px solid rgba(45,212,191,0.3);  color: #2dd4bf; }
.alert-success { background: rgba(63,185,80,0.1);  border: 1px solid rgba(63,185,80,0.3);   color: #3fb950; }

.level-badge { display: inline-block; padding: 6px 22px; border-radius: 6px; font-size: 0.88rem; font-weight: 700; letter-spacing: 0.06em; }
.level-low    { background: rgba(63,185,80,0.15);  color: #3fb950; }
.level-normal { background: rgba(45,212,191,0.12); color: #2dd4bf; }
.level-high   { background: rgba(248,81,73,0.15);  color: #f85149; }

/* Authentication screen — clean product UI */
.auth-shell {
    max-width: 1180px;
    margin: 26px auto 0;
    padding: 8px 4px 16px;
}
.auth-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 42px;
    color: #f4f7fb;
    font-size: .94rem;
    font-weight: 700;
    letter-spacing: -.01em;
}
.auth-logo {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #111c2b;
    border: 1px solid #263447;
    color: #67e8d5;
    font-size: 1rem;
}
.auth-kicker {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 18px;
    color: #7dd3fc;
    font-size: .72rem;
    font-weight: 650;
    letter-spacing: .04em;
}
.auth-kicker::before {
    content: '';
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 0 4px rgba(52,211,153,.08);
}
.auth-hero-title {
    max-width: 680px;
    margin: 0 0 16px;
    color: #f7f9fc;
    font-size: clamp(2.25rem, 4vw, 3.75rem);
    line-height: 1.02;
    letter-spacing: -.055em;
    font-weight: 760;
}
.auth-hero-title span {
    color: #65e6d2;
    -webkit-text-fill-color: initial;
    background: none;
}
.auth-hero-sub {
    max-width: 590px;
    margin: 0 0 28px;
    color: #93a4b8;
    font-size: .94rem;
    line-height: 1.75;
}
.auth-detail-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    max-width: 620px;
}
.auth-detail {
    padding: 9px 12px;
    border-radius: 10px;
    background: #111820;
    border: 1px solid #202b38;
    color: #9fb0c2;
    font-size: .72rem;
}
.auth-detail strong {
    color: #dce6ef;
    font-weight: 650;
}
.auth-panel-title {
    color: #f5f7fa;
    font-size: 1.35rem;
    font-weight: 720;
    margin: 2px 0 5px;
    letter-spacing: -.025em;
}
.auth-panel-sub {
    color: #8293a7;
    font-size: .78rem;
    line-height: 1.55;
    margin-bottom: 16px;
}
.auth-security {
    margin-top: 14px;
    color: #647487;
    text-align: center;
    font-size: .66rem;
}
.auth-footer {
    margin-top: 34px;
    padding-top: 18px;
    border-top: 1px solid #1b2530;
    text-align: center;
    color: #566575;
    font-size: .66rem;
}
.auth-page-note {
    color: #8192a6;
    font-size: .72rem;
    margin: 2px 0 10px;
}

/* Auth card */
div[data-testid="stForm"] {
    background: #111820 !important;
    border: 1px solid #25303d !important;
    border-radius: 16px !important;
    padding: 20px 20px 16px !important;
    box-shadow: 0 18px 46px rgba(0,0,0,.22) !important;
}

/* Make auth inputs readable on the dark background */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p {
    color: #cbd5df !important;
    font-size: .76rem !important;
    font-weight: 600 !important;
}
div[data-testid="stTextInput"] input {
    background: #0c1219 !important;
    color: #f4f7fb !important;
    -webkit-text-fill-color: #f4f7fb !important;
    border: 1px solid #2a3745 !important;
    border-radius: 10px !important;
    min-height: 43px !important;
    caret-color: #67e8d5 !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #617184 !important;
    opacity: 1 !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #4fd1c5 !important;
    box-shadow: 0 0 0 1px #4fd1c5 !important;
}

/* Password eye/icon */
div[data-testid="stTextInput"] button,
div[data-testid="stTextInput"] svg {
    color: #8da0b4 !important;
    fill: #8da0b4 !important;
}

/* Auth tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #0c1219;
    border: 1px solid #202b38;
    border-radius: 11px;
    padding: 4px;
    margin-bottom: 14px;
}
.stTabs [data-baseweb="tab"] {
    height: 36px;
    border-radius: 8px;
    color: #7f91a4 !important;
    font-size: .76rem;
    font-weight: 600;
    padding: 0 14px;
}
.stTabs [aria-selected="true"] {
    color: #e7fbf8 !important;
    background: #172b2a !important;
    border-bottom-color: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Auth submit button */
div[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
    background: #23a89a !important;
    color: #ffffff !important;
    border: 1px solid #2cb7a8 !important;
    border-radius: 10px !important;
    min-height: 43px !important;
    font-weight: 650 !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover {
    background: #26978d !important;
    border-color: #3cc4b5 !important;
}

@media (max-width: 900px) {
    .auth-shell { margin-top: 10px; }
    .auth-brand { margin-bottom: 22px; }
    .auth-hero-title { font-size: 2.25rem; }
    .auth-detail-row { margin-bottom: 16px; }
}

.sidebar-brand { font-size: 1rem; font-weight: 700; color: #2dd4bf !important; letter-spacing: -0.01em; padding: 8px 0 2px 0; }
.sidebar-user  { font-size: 0.75rem; color: #484f58 !important; margin-bottom: 16px; }

.stButton > button { background: #0d9488; color: #fff; border: none; border-radius: 7px; font-weight: 600; font-size: 0.88rem; padding: 10px 20px; transition: background 0.2s; }
.stButton > button:hover { background: #0f766e; }

div[data-testid="metric-container"] { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 14px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
[data-testid="stMetricLabel"]  { font-size: 0.68rem !important; color: #7d8590 !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"]  { font-size: 1.5rem  !important; color: #e6edf3 !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"]  { font-size: 0.78rem !important; }

.stDataFrame { border-radius: 8px; overflow: hidden; }
.stDataFrame thead tr th { background: #161b22 !important; color: #7d8590 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
.stDataFrame tbody tr td { color: #c9d1d9 !important; font-size: 0.84rem !important; }
.stDataFrame tbody tr:hover td { background: #1c2128 !important; }

.stExpander { background: #161b22 !important; border: 1px solid #21262d !important; border-radius: 8px !important; }
.stExpander summary { color: #c9d1d9 !important; font-weight: 600; }

.stTabs [data-baseweb="tab"] { color: #7d8590 !important; }
.stTabs [aria-selected="true"] { color: #2dd4bf !important; border-bottom-color: #2dd4bf !important; }

.sensor-card { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 18px 16px; text-align: center; transition: border-color 0.2s; }
.sensor-card.smoke-alert { border-color: #f85149; background: #1a0a0a; }
.sensor-card.motion-on   { border-color: #d29922; background: #1a1500; }
.sensor-card.ok          { border-color: #3fb95044; }
.sensor-icon  { font-size: 2rem; margin-bottom: 6px; }
.sensor-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #7d8590; margin-bottom: 4px; }
.sensor-value { font-size: 1.3rem; font-weight: 700; color: #e6edf3; }
.sensor-sub   { font-size: 0.7rem; color: #484f58; margin-top: 3px; }
.sensor-pill  { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; margin-top: 8px; }
.pill-clear  { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.pill-smoke  { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid rgba(248,81,73,0.4); }
.pill-motion { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.4); }
.pill-idle   { background: rgba(72,79,88,0.3);    color: #7d8590; border: 1px solid #30363d; }
.pill-sim    { background: rgba(45,212,191,0.1);  color: #2dd4bf; border: 1px solid rgba(45,212,191,0.3); }
.pill-real   { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }

/* Bedroom 1 device card */
.device-card {
    background: #161b22; border: 1.5px solid #21262d; border-radius: 12px;
    padding: 20px 14px; text-align: center; transition: border-color 0.2s, background 0.2s;
}
.device-card.active { border-color: #3fb950; background: #0a1a0d; }
.device-name  { font-size: 0.82rem; font-weight: 700; color: #e6edf3; margin: 10px 0 6px; }
.device-pin   { font-size: 0.62rem; color: #484f58; margin-bottom: 8px; }

.event-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-bottom: 1px solid #21262d; font-size: 0.82rem; }
.event-row:last-child { border-bottom: none; }
.event-time { color: #484f58; font-size: 0.72rem; min-width: 80px; }
.event-icon { font-size: 1.1rem; }
.event-msg  { color: #c9d1d9; flex: 1; }
.event-room { color: #7d8590; font-size: 0.72rem; }


/* ===== FINAL UI POLISH — SMART HOME PRODUCT DASHBOARD ===== */
:root {
    --bg0: #08111f;
    --bg1: #0b1627;
    --surface: rgba(16, 30, 49, 0.72);
    --surface-strong: rgba(18, 35, 57, 0.92);
    --border: rgba(148, 163, 184, 0.14);
    --text: #edf6ff;
    --muted: #91a4ba;
    --accent: #5eead4;
    --accent2: #60a5fa;
    --success: #6ee7b7;
    --warning: #fbbf24;
    --danger: #fb7185;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background:
      radial-gradient(circle at 12% 8%, rgba(45, 212, 191, 0.11), transparent 31%),
      radial-gradient(circle at 86% 2%, rgba(96, 165, 250, 0.12), transparent 28%),
      linear-gradient(145deg, var(--bg0) 0%, #0a1423 50%, #07101c 100%);
    color: var(--text);
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image: linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 38px 38px;
    mask-image: linear-gradient(to bottom, rgba(0,0,0,.55), transparent 80%);
}
[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding: 2.1rem 2.7rem 3rem;
    max-width: 1480px;
    background: transparent;
}

[data-testid="stSidebar"] {
    background: rgba(7, 16, 29, 0.82);
    backdrop-filter: blur(18px);
    border-right: 1px solid var(--border);
    box-shadow: 12px 0 36px rgba(0,0,0,.18);
}
[data-testid="stSidebar"] * { color: #a8b8ca !important; }
.sidebar-brand {
    color: #f5fbff !important;
    font-size: 1.18rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    padding: 12px 0 4px;
}
.sidebar-user { color: #6f8297 !important; }
[data-testid="stSidebar"] .stRadio label {
    border-radius: 12px;
    padding: 9px 10px;
    transition: all .2s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #e7ffff !important;
    background: rgba(94,234,212,.07);
}

.page-header {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 24px 26px;
    margin-bottom: 26px;
    background: linear-gradient(135deg, rgba(23, 42, 66, .82), rgba(10, 25, 43, .58));
    box-shadow: 0 18px 50px rgba(0,0,0,.22);
    backdrop-filter: blur(16px);
}
.page-header::after {
    content:"";
    position:absolute;
    width:240px;
    height:240px;
    right:-90px;
    top:-130px;
    border-radius:50%;
    background: radial-gradient(circle, rgba(94,234,212,.18), transparent 68%);
}
.page-header h2 {
    position:relative;
    z-index:1;
    font-size: 1.85rem;
    font-weight: 800;
    color: #f5fbff;
    margin: 0;
    letter-spacing: -0.04em;
}
.page-header p {
    position:relative;
    z-index:1;
    font-size: .9rem;
    color: #9fb1c6;
    margin-top: 7px;
}

.section-title {
    font-size: .72rem;
    font-weight: 800;
    letter-spacing: .16em;
    color: #7dd3fc;
    margin: 30px 0 13px;
    border-left: none;
    padding-left: 0;
}
.section-title::after {
    content:"";
    display:inline-block;
    width:44px;
    height:1px;
    margin-left:12px;
    vertical-align:middle;
    background: linear-gradient(90deg, rgba(125,211,252,.8), transparent);
}

/* Metric tiles */
div[data-testid="metric-container"] {
    background: linear-gradient(145deg, rgba(19, 37, 60, .88), rgba(12, 27, 46, .72));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 17px 18px;
    box-shadow: 0 12px 32px rgba(0,0,0,.16), inset 0 1px 0 rgba(255,255,255,.025);
    backdrop-filter: blur(14px);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    border-color: rgba(94,234,212,.28);
    box-shadow: 0 16px 38px rgba(0,0,0,.22), 0 0 24px rgba(45,212,191,.04);
}
[data-testid="stMetricLabel"] {
    color: #8fa3b8 !important;
    font-size: .7rem !important;
    letter-spacing: .08em;
}
[data-testid="stMetricValue"] {
    color: #f4f9ff !important;
    font-size: 1.55rem !important;
}

/* Appliance cards */
.device-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, rgba(20, 39, 63, .88), rgba(11, 26, 44, .74));
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 23px 16px 20px;
    min-height: 168px;
    box-shadow: 0 14px 34px rgba(0,0,0,.17);
    backdrop-filter: blur(14px);
    transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.device-card::before {
    content:"";
    position:absolute;
    width:120px;
    height:120px;
    top:-65px;
    right:-55px;
    border-radius:50%;
    background: rgba(96,165,250,.07);
}
.device-card:hover {
    transform: translateY(-3px);
    border-color: rgba(125,211,252,.28);
    box-shadow: 0 20px 42px rgba(0,0,0,.22);
}
.device-card.active {
    border-color: rgba(110,231,183,.38);
    background: linear-gradient(145deg, rgba(16, 58, 60, .82), rgba(11, 35, 45, .76));
    box-shadow: 0 18px 42px rgba(16,185,129,.08);
}
.device-name {
    font-size: .94rem;
    font-weight: 800;
    color: #f5fbff;
    margin: 11px 0 5px;
}
.device-pin {
    font-size: .7rem;
    color: #8297ad;
    margin-bottom: 10px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0f9f91, #277fc2);
    color: white;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    font-weight: 700;
    font-size: .86rem;
    min-height: 42px;
    padding: 10px 18px;
    box-shadow: 0 8px 18px rgba(14,116,144,.15);
    transition: transform .16s ease, box-shadow .16s ease, filter .16s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #11a99b, #2b86ca);
    transform: translateY(-1px);
    box-shadow: 0 11px 24px rgba(14,116,144,.22);
    filter: brightness(1.04);
}
.stButton > button:active { transform: translateY(0); }

/* Alerts / status cards */
.alert-box {
    border-radius: 16px;
    padding: 15px 18px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 26px rgba(0,0,0,.12);
}
.alert-success { background: rgba(16,185,129,.09); border: 1px solid rgba(110,231,183,.22); color:#a7f3d0; }
.alert-warning { background: rgba(245,158,11,.09); border: 1px solid rgba(251,191,36,.23); color:#fde68a; }
.alert-danger  { background: rgba(244,63,94,.09); border: 1px solid rgba(251,113,133,.23); color:#fecdd3; }
.alert-info    { background: rgba(56,189,248,.08); border: 1px solid rgba(125,211,252,.22); color:#bae6fd; }

.sensor-card,
.floorplan-wrap,
.stExpander {
    background: linear-gradient(145deg, rgba(18, 35, 57, .82), rgba(11, 25, 43, .72)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: 0 12px 30px rgba(0,0,0,.14);
    backdrop-filter: blur(14px);
}
.sensor-card { padding: 20px 17px; }
.sensor-card:hover { border-color: rgba(94,234,212,.25) !important; }
.sensor-label { color:#8da2b8; }
.sensor-value { color:#f4f9ff; }
.sensor-sub { color:#688097; }

/* Inputs and sliders */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input {
    background: rgba(13, 28, 47, .82) !important;
    border-color: rgba(148,163,184,.16) !important;
    border-radius: 12px !important;
    color: #eef7ff !important;
}
[data-testid="stSlider"] { padding-top: 4px; }

/* Tabs, data tables and dividers */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    padding: 8px 14px;
}
.stTabs [aria-selected="true"] { color:#67e8f9 !important; }
hr { border-color: rgba(148,163,184,.11) !important; }
.stDataFrame { border-radius: 16px; overflow:hidden; border:1px solid var(--border); }

/* Responsive breathing room */
@media (max-width: 900px) {
    .block-container { padding: 1.3rem 1rem 2rem; }
    .page-header { padding: 20px; border-radius: 18px; }
    .page-header h2 { font-size: 1.5rem; }
}

</style>
"""

# ── Session state ──────────────────────────────────────────────────────────────
for key, val in [("logged_in", False), ("username", ""), ("history", [])]:
    if key not in st.session_state:
        st.session_state[key] = val


# ── API helpers ────────────────────────────────────────────────────────────────
def fetch_snapshot():
    try:
        r = requests.get(f"{API}/generate/live", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def fetch_environment():
    try:
        r = requests.get(f"{API}/sensor/environment", timeout=3)
        if r.status_code == 200:
            data = r.json()
            # backend now returns {"environment": {...}, "fridge_door_open": bool}
            env = data.get("environment", {})
            fridge_door = data.get("fridge_door_open", False)
            return env, fridge_door
    except Exception:
        pass
    return {}, False

def fetch_iot_events(limit: int = 30):
    try:
        r = requests.get(f"{API}/iot/events?limit={limit}", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def fetch_sensor_mode():
    try:
        r = requests.get(f"{API}/sensor/mode", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"mode": "simulation", "rooms_reporting": []}

def fetch_device_state():
    try:
        r = requests.get(f"{API}/device/state", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"lights_on": False, "ac_on": False, "geyser_on": False, "fridge_on": False, "servo_angle": 0}

def device_control(device: str, is_on: bool = None, angle: int = None) -> dict:
    """
    POST to /device/control and return the backend's confirmed state.
    Caller should update st.session_state with the returned values so the
    page re-renders with the fresh (never stale) state.
    """
    payload = {"room": "Bedroom 1", "device": device}
    if angle is not None:
        payload["angle"] = angle
    else:
        payload["is_on"] = is_on
    try:
        r = requests.post(f"{API}/device/control", json=payload, timeout=5)
        if r.status_code == 200:
            # Re-fetch confirmed state so toggle direction is always correct
            confirmed = requests.get(f"{API}/device/state", timeout=3)
            if confirmed.status_code == 200:
                return confirmed.json()
    except Exception:
        pass
    return {}

def power_color(w):
    if w > 6000: return "#f85149"
    if w > 3000: return "#d29922"
    return "#3fb950"

def temp_color(t):
    if t > 30: return "#f85149"
    if t > 27: return "#d29922"
    return "#3fb950"

def room_class(p, is_real=False):
    if is_real:   return "real"
    if p > 6000:  return "alert"
    if p > 3000:  return "warn"
    return ""

def inject_style():
    st.markdown(STYLE, unsafe_allow_html=True)

def page_header(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="page-header"><h2>{title}</h2>{sub}</div>', unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)

def _clean_html(html: str) -> str:
    """Flatten multiline HTML so Streamlit Markdown never treats nested lines as code blocks."""
    dedented = textwrap.dedent(html).strip()
    return " ".join(line.strip() for line in dedented.splitlines() if line.strip())


def render_html(html: str):
    """Render HTML/SVG reliably in Streamlit."""
    st.markdown(_clean_html(html), unsafe_allow_html=True)


def mhtml(html: str):
    """Alias for reliable multiline HTML/SVG rendering."""
    st.markdown(_clean_html(html), unsafe_allow_html=True)


# ── Auth ───────────────────────────────────────────────────────────────────────
def auth_page():
    inject_style()

    mhtml("""
    <div class="auth-shell">
      <div class="auth-brand">
        <span class="auth-logo">⌂</span>
        SmartHome Digital Twin
      </div>
    </div>
    """)

    left, gap, right = st.columns([1.45, 0.10, 0.88], vertical_alignment="center")

    with left:
        mhtml("""
        <div class="auth-kicker">System online · Bedroom 1 connected</div>
        <div class="auth-hero-title">A clearer view of your <span>smart home.</span></div>
        <div class="auth-hero-sub">
          One dashboard for live appliance control, room conditions, energy usage
          and hazard monitoring — built around your executable digital twin.
        </div>
        <div class="auth-detail-row">
          <div class="auth-detail"><strong>Live</strong> device control</div>
          <div class="auth-detail"><strong>24/7</strong> environment monitoring</div>
          <div class="auth-detail"><strong>Smart</strong> automation rules</div>
        </div>
        """)

    with right:
        mhtml("""
        <div class="auth-panel-title">Welcome back</div>
        <div class="auth-panel-sub">Use your account to continue to the control dashboard.</div>
        """)

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username", placeholder="Enter your username")
                pwd = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In →", use_container_width=True)

            if submitted:
                if not uname or not pwd:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        r = requests.post(
                            f"{API}/login",
                            json={"username": uname, "password": pwd},
                            timeout=5,
                        )
                        if r.status_code == 200:
                            st.session_state.logged_in = True
                            st.session_state.username = uname
                            st.rerun()
                        elif r.status_code == 401:
                            st.error("Invalid credentials.")
                        else:
                            st.error(r.json().get("detail", "Login failed."))
                    except Exception:
                        st.error("Cannot reach backend.")

        with tab_signup:
            mhtml('<div class="auth-page-note">Create an account to access the dashboard.</div>')
            with st.form("signup_form"):
                new_uname = st.text_input("Username", placeholder="Choose a username", key="signup_username")
                new_pwd = st.text_input("Password", type="password", placeholder="Create a password", key="signup_password")
                new_pwd2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="signup_password_confirm")
                submitted2 = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted2:
                if not new_uname or not new_pwd:
                    st.error("Please fill in all fields.")
                elif new_pwd != new_pwd2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        r = requests.post(
                            f"{API}/signup",
                            json={"username": new_uname, "password": new_pwd},
                            timeout=5,
                        )
                        if r.status_code == 200:
                            st.success("Account created. Please switch to Sign In.")
                        else:
                            st.error(r.json().get("detail", "Signup failed."))
                    except Exception:
                        st.error("Cannot reach backend.")

        mhtml("""
        <div class="auth-security">Secure local access · Your dashboard session stays protected</div>
        """)

    mhtml("""
    <div class="auth-footer">Executable Digital Twin · Energy Monitoring · Hazard Prediction</div>
    """)


# ── Page: Bedroom 1 Control ────────────────────────────────────────────────────
def page_bedroom1():
    inject_style()
    page_header(
        "🛏  Bedroom 1 — Live Control",
        "Real-time appliance control · room conditions · smart door & fridge monitoring"
    )

    mode = fetch_sensor_mode()
    is_real = "Bedroom 1" in mode.get("rooms_reporting", [])

    if is_real:
        st.markdown(
            '<div class="alert-box alert-success">● ESP32 connected — Bedroom 1 is live. '
            'Controls below send commands directly to the board.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="alert-box alert-info">◌ ESP32 not connected yet. '
            'Flash <code>esp32_smarthome/esp32_smarthome.ino</code> and power the board. '
            'Controls are still saved — they will apply the moment the board connects.</div>',
            unsafe_allow_html=True,
        )

    dev = fetch_device_state()
    # Bug 1 fix: if we have a freshly confirmed state from a recent button click,
    # use that instead of the potentially stale fetch result
    if "dev_state" in st.session_state:
        dev = st.session_state.pop("dev_state")
    env, fridge_door_open = fetch_environment()
    bedroom_env = env.get("Bedroom 1", {})

    # ── Live sensor readings ──────────────────────────────────────────────────
    section("COMFORT & SAFETY")
    temp_val    = bedroom_env.get("temp_c",      None)
    hum_val     = bedroom_env.get("humidity",    None)
    smoke_val   = bedroom_env.get("smoke_ppm",   None)
    smoke_alert = bedroom_env.get("smoke_alert", False)
    motion      = bedroom_env.get("motion",      False)

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("🌡 Temperature",  f"{temp_val:.1f} °C"  if temp_val  is not None else "—")
    s2.metric("💧 Humidity",     f"{hum_val:.0f} %"    if hum_val   is not None else "—")
    s3.metric("🔥 MQ2 (ADC)",    f"{smoke_val:.0f}"    if smoke_val is not None else "—")
    s4.metric("⚠ Smoke",         "ALERT" if smoke_alert else "Clear")
    s5.metric("👤 Motion",       "YES"   if motion      else "No")

    if smoke_alert:
        st.markdown(
            '<div class="alert-box alert-danger">🔥 Smoke / gas detected in Bedroom 1! '
            'Check for fire hazards immediately.</div>',
            unsafe_allow_html=True,
        )

    # ── Appliance Controls ─────────────────────────────────────────────────────
    section("APPLIANCES")

    DEVICES = [
        ("Lamp",   "lamp",   "💡", "Smart Lighting",  dev.get("lights_on", False)),
        ("AC",     "ac",     "❄️", "Climate Control", dev.get("ac_on",     False)),
        ("Geyser", "geyser", "🚿", "Water Heating",   dev.get("geyser_on", False)),
    ]

    col1, col2, col3 = st.columns(3)
    for col, (label, key, icon, pin, is_on) in zip([col1, col2, col3], DEVICES):
        with col:
            card_cls  = "device-card active" if is_on else "device-card"
            led_color = "#3fb950" if is_on else "#30363d"
            mhtml(textwrap.dedent(f"""
            <div class="{card_cls}">
              <div style="font-size:2rem">{icon}</div>
              <div class="device-name">{label}</div>
              <div class="device-pin">{pin}</div>
              <div style="display:flex;justify-content:center;gap:6px;margin-bottom:10px">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{led_color};
                             box-shadow:{'0 0 8px #3fb950' if is_on else 'none'};
                             margin-top:3px"></span>
                <span style="font-size:0.78rem;font-weight:700;
                             color:{'#3fb950' if is_on else '#484f58'}">
                  {'ON' if is_on else 'OFF'}
                </span>
              </div>
            </div>"""))

            btn_label = f"Turn {'OFF' if is_on else 'ON'} {label}"
            if st.button(btn_label, key=f"btn_{key}", use_container_width=True):
                new_state = device_control(key, is_on=not is_on)
                if new_state:
                    st.session_state["dev_state"] = new_state
                st.rerun()

    # ── Fridge Door (Reed Switch) status ──────────────────────────────────────
    section("REFRIGERATOR")

    door_cls = "alert-warning" if fridge_door_open else "alert-success"
    door_icon = "🔓" if fridge_door_open else "🔒"
    door_text = "FRIDGE DOOR OPEN — magnet not detected" if fridge_door_open \
                else "FRIDGE DOOR CLOSED — magnet detected"
    door_sub  = "Close the fridge door to save energy." if fridge_door_open \
                else "Door is properly shut."

    mhtml(textwrap.dedent(f"""
    <div class="alert-box {door_cls}" style="display:flex;align-items:center;gap:16px">
      <span style="font-size:2rem">{door_icon}</span>
      <div>
        <div style="font-weight:700;font-size:0.9rem">{door_text}</div>
        <div style="font-size:0.78rem;margin-top:4px;opacity:0.8">{door_sub}</div>
      </div>
    </div>"""))

    # Live fridge status — power control is independent of the reed-switch door sensor
    f1, f2, f3, f4 = st.columns(4)
    fridge_on = dev.get("fridge_on", False)
    door_light_on = fridge_door_open
    f1.metric("Power Status", "ON" if fridge_on else "OFF")
    f2.metric("Door Status", "OPEN" if fridge_door_open else "CLOSED")
    f3.metric("Interior Light", "ON" if door_light_on else "OFF")
    f4.metric("Door Sensor", "OPEN" if fridge_door_open else "CLOSED")

    fridge_btn_label = f"Turn {'OFF' if fridge_on else 'ON'} Fridge"
    if st.button(fridge_btn_label, key="btn_fridge_power", use_container_width=True):
        new_state = device_control("fridge", is_on=not fridge_on)
        if new_state:
            st.session_state["dev_state"] = new_state
        st.rerun()

    # ── Main Door Control ───────────────────────────────────────────────────────
    section("ENTRY CONTROL")

    current_angle = dev.get("servo_angle", 0)
    st.markdown(
        f'<div style="font-size:0.82rem;color:#7d8590;margin-bottom:8px">'
        f'Door position: <strong style="color:#e6edf3">{"OPEN" if current_angle >= 45 else "CLOSED"}</strong> &nbsp;·&nbsp; '
        f'0° = door closed &nbsp;·&nbsp; 90° = door open</div>',
        unsafe_allow_html=True,
    )

    sv_col1, sv_col2, sv_col3 = st.columns([3, 1, 1])
    with sv_col1:
        new_angle = st.slider(
            "Set door position",
            min_value=0, max_value=180, value=current_angle, step=5,
            label_visibility="collapsed",
        )
    with sv_col2:
        if st.button("Apply Position", use_container_width=True):
            new_state = device_control("servo", angle=new_angle)
            if new_state:
                st.session_state["dev_state"] = new_state
            st.rerun()
    with sv_col3:
        if st.button("Close Door", use_container_width=True):
            new_state = device_control("servo", angle=0)
            if new_state:
                st.session_state["dev_state"] = new_state
            st.rerun()

    # Quick presets — door only needs 2 positions
    st.markdown('<div style="margin-top:8px;font-size:0.72rem;color:#484f58">Quick controls:</div>', unsafe_allow_html=True)
    p1, p2, _, _ = st.columns(4)
    with p1:
        if st.button("Close Door", key="preset_0", use_container_width=True):
            new_state = device_control("servo", angle=0)
            if new_state:
                st.session_state["dev_state"] = new_state
            st.rerun()
    with p2:
        if st.button("Open Door", key="preset_90", use_container_width=True):
            new_state = device_control("servo", angle=90)
            if new_state:
                st.session_state["dev_state"] = new_state
            st.rerun()

    # Servo arc visualisation
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = current_angle,
        title = {"text": "Door Position", "font": {"color": "#7d8590", "size": 13}},
        number= {"suffix": "°", "font": {"color": "#e6edf3", "size": 26}},
        gauge = {
            "axis":        {"range": [0, 180], "tickcolor": "#484f58", "tickfont": {"color": "#484f58"}},
            "bar":         {"color": "#2dd4bf"},
            "bgcolor":     "#0d1117",
            "bordercolor": "#21262d",
            "steps": [
                {"range": [0,   60],  "color": "rgba(63,185,80,0.1)"},
                {"range": [60,  120], "color": "rgba(45,212,191,0.08)"},
                {"range": [120, 180], "color": "rgba(248,81,73,0.08)"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="#161b22", font=dict(family="Inter, sans-serif"),
        height=220, margin=dict(l=30, r=30, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Auto-rule status ──────────────────────────────────────────────────────
    section("SMART AUTOMATION")
    mhtml(textwrap.dedent("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px 20px">
      <div style="display:flex;flex-direction:column;gap:10px;font-size:0.83rem;color:#c9d1d9">
        <div>🔥 <strong style="color:#e6edf3">Smoke detected</strong>
             &nbsp;→&nbsp; AC turns ON automatically</div>
        <div>🌡 <strong style="color:#e6edf3">Temp &gt; 30 °C</strong>
             &nbsp;→&nbsp; AC turns ON automatically</div>
        <div>💡 <strong style="color:#e6edf3">Manual override always wins</strong>
             &nbsp;→&nbsp; Manual controls remain available at all times</div>
      </div>
    </div>"""))

    # ── Reset button ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Reset Sensor Mode to Simulation", use_container_width=False):
        try:
            requests.post(f"{API}/sensor/reset", timeout=5)
            st.success("Reset to simulation mode.")
            st.rerun()
        except Exception as e:
            st.error(str(e))


# ── Page: Digital Twin ─────────────────────────────────────────────────────────
def page_digital_twin():
    inject_style()
    page_header("Digital Twin", "Real-time floor plan · Bedroom 1 is live hardware, other rooms simulated")

    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable. Start the FastAPI server and refresh.")
        return

    rooms = snap["rooms"]
    total = snap["total_power"]
    st.session_state.history.append(total)
    if len(st.session_state.history) > 60:
        st.session_state.history = st.session_state.history[-60:]

    mode         = fetch_sensor_mode()
    real_rooms   = set(mode.get("rooms_reporting", []))

    c1, c2, c3, c4 = st.columns(4)
    b1_temp = rooms.get("Bedroom 1", {}).get("temperature", "—")
    apps_on = sum(1 for r in rooms.values() for a in r["appliances"].values() if a["is_on"])
    total_apps = sum(len(r["appliances"]) for r in rooms.values())
    c1.metric("Total Power",         f"{total:.0f} W")
    c2.metric("Bedroom 1 Temp (Live)", f"{b1_temp} °C")
    c3.metric("Appliances Active",   f"{apps_on} / {total_apps}")
    c4.metric("Logged In As",        st.session_state.username)

    mode_pill = (
        '<span class="sensor-pill pill-real">● REAL SENSORS ACTIVE</span>'
        if mode["mode"] == "real"
        else '<span class="sensor-pill pill-sim">◌ SIMULATION MODE</span>'
    )
    st.markdown(
        f'<div style="margin:12px 0 4px">{mode_pill}'
        + (f'&nbsp;&nbsp;<span style="font-size:0.72rem;color:#484f58">Live: {", ".join(real_rooms)}</span>' if real_rooms else "")
        + "</div>",
        unsafe_allow_html=True,
    )

    section("LIVE HOME MAP")

    ROOM_ICONS = {
        "Living Room": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="1.5"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><path d="M9 21V12h6v9"/></svg>',
        "Bedroom 1":   '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#3fb950" stroke-width="1.5"><path d="M2 9h20v11H2z"/><path d="M2 9V7a2 2 0 012-2h16a2 2 0 012 2v2"/><path d="M12 9V5"/><circle cx="7" cy="14" r="1.5"/><circle cx="17" cy="14" r="1.5"/></svg>',
        "Bedroom 2":   '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="1.5"><path d="M2 9h20v11H2z"/><path d="M2 9V7a2 2 0 012-2h16a2 2 0 012 2v2"/><path d="M12 9V5"/><circle cx="7" cy="14" r="1.5"/><circle cx="17" cy="14" r="1.5"/></svg>',
        "Kitchen":     '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="1.5"><rect x="2" y="3" width="20" height="18" rx="2"/><path d="M2 9h20"/><circle cx="7" cy="6" r="1"/><circle cx="12" cy="6" r="1"/></svg>',
        "Washroom":    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="1.5"><path d="M4 12h16v4a4 4 0 01-4 4H8a4 4 0 01-4-4v-4z"/><path d="M4 12V6a2 2 0 012-2h1a2 2 0 012 2v6"/><path d="M20 12V8"/></svg>',
        "Utility":     '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="12" cy="12" r="4"/><path d="M12 8v1M12 15v1M8 12h1M15 12h1"/></svg>',
    }

    def appliance_dots(appliances):
        return "".join(
            f'<span title="{app}" style="display:inline-block;width:7px;height:7px;border-radius:50%;'
            f'background:{"#3fb950" if a["is_on"] else "#30363d"};margin:1px"></span>'
            for app, a in appliances.items()
        )

    def room_cell(label, data):
        t   = data["temperature"]
        p   = data["total_power"]
        on  = sum(1 for a in data["appliances"].values() if a["is_on"])
        tot = len(data["appliances"])
        is_r = label in real_rooms
        rc   = room_class(p, is_real=is_r)
        tc   = temp_color(t)
        pc   = power_color(p)
        icon = ROOM_ICONS.get(label, "")
        dots = appliance_dots(data["appliances"])
        live = '<div style="font-size:0.58rem;color:#3fb950;font-weight:700">&#9679; LIVE</div>' if is_r else ""
        return (
            f'<div class="room-cell {rc}">'
            + live
            + f'<div style="margin-bottom:4px">{icon}</div>'
            + f'<div class="room-name">{label}</div>'
            + f'<div class="room-temp" style="color:{tc}">🌡 {t} °C</div>'
            + f'<div class="room-power" style="color:{pc}">⚡ {p:.0f} W</div>'
            + f'<div style="margin-top:5px">{dots}</div>'
            + f'<div class="room-apps">{on}/{tot} on</div>'
            + '</div>'
        )

    lr  = room_cell("Living Room", rooms["Living Room"])
    b1  = room_cell("Bedroom 1",   rooms["Bedroom 1"])
    b2  = room_cell("Bedroom 2",   rooms["Bedroom 2"])
    kit = room_cell("Kitchen",     rooms["Kitchen"])
    wsh = room_cell("Washroom",    rooms["Washroom"])
    utl = room_cell("Utility",     rooms["Utility"])
    W   = '<div style="width:5px" class="wall"></div>'
    fp  = (
        '<div class="floorplan-wrap">'
        '<div class="compass">N&nbsp;&nbsp;(ENTRANCE)</div>'
        '<div style="display:flex;align-items:center">'
        '<div style="flex:1;height:5px" class="wall"></div>'
        '<div class="entrance-gap"></div>'
        '<div style="flex:1;height:5px" class="wall"></div>'
        '</div>'
        '<div style="display:flex">' + W + '<div style="flex:1">' + lr + '</div>' + W + '</div>'
        '<div style="display:flex">' + W
        + '<div style="flex:2;height:5px" class="wall"></div>'
        + '<div style="width:40px;height:5px;background:#0d1117"></div>'
        + '<div style="flex:3;height:5px" class="wall"></div>' + W + '</div>'
        '<div style="display:flex">' + W
        + '<div style="flex:1">' + b1  + '</div>' + W
        + '<div style="flex:1">' + b2  + '</div>' + W
        + '<div style="flex:1">' + kit + '</div>' + W
        + '<div style="flex:1">' + wsh + '</div>' + W
        + '<div style="flex:1">' + utl + '</div>' + W
        + '</div>'
        '<div style="height:5px" class="wall"></div>'
        '<div class="compass" style="margin-top:6px">S</div>'
        '</div>'
    )
    render_html(fp)

    env, _ = fetch_environment()
    if env:
        section("BEDROOM 1 — LIVE CONDITIONS")
        cols = st.columns(min(len(env), 4))
        for i, (rname, edata) in enumerate(env.items()):
            temp_e      = edata.get("temp_c",      None)
            humidity    = edata.get("humidity",    None)
            smoke_ppm   = edata.get("smoke_ppm",   None)
            smoke_alert = edata.get("smoke_alert", False)
            motion      = edata.get("motion",      False)
            card_cls    = "smoke-alert" if smoke_alert else "motion-on" if motion else "ok"
            sp = '<span class="sensor-pill pill-smoke">&#9888; SMOKE</span>' if smoke_alert else '<span class="sensor-pill pill-clear">&#10003; Clear</span>'
            mp = '<span class="sensor-pill pill-motion">&#9685; Motion</span>' if motion else '<span class="sensor-pill pill-idle">&#9684; Idle</span>'
            with cols[i % len(cols)]:
                render_html(
                    f'<div class="sensor-card {card_cls}">'
                    f'<div style="font-size:0.78rem;font-weight:700;color:#e6edf3;margin-bottom:12px">{rname}</div>'
                    f'<div style="display:flex;justify-content:space-around;margin-bottom:10px">'
                    f'<div><div class="sensor-label">&#127777; Temp</div><div class="sensor-value">{f"{temp_e:.1f} &#176;C" if temp_e is not None else "&mdash;"}</div></div>'
                    f'<div><div class="sensor-label">&#128167; Humidity</div><div class="sensor-value">{f"{humidity:.0f} %" if humidity is not None else "&mdash;"}</div></div>'
                    f'<div><div class="sensor-label">&#128293; MQ2</div><div class="sensor-value">{f"{smoke_ppm:.0f}" if smoke_ppm is not None else "&mdash;"}</div></div>'
                    f'</div><div style="display:flex;justify-content:center;gap:8px">{sp}{mp}</div></div>'
                )
    else:
        st.markdown(
            '<div class="alert-box alert-info" style="margin-top:12px">'
            'No live ESP32 data yet. Go to <strong>Bedroom 1 Control</strong> for hardware setup.</div>',
            unsafe_allow_html=True)

    section("ROOM & APPLIANCE STATUS")
    APP_ICONS = {
        "AC": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="6" width="20" height="10" rx="2"/><path d="M6 16v3M18 16v3M8 11h8"/></svg>',
        "TV": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 20h8M12 18v2"/></svg>',
        "Fan": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 2a4 4 0 014 4c0 1.5-.8 2.8-2 3.5M12 22a4 4 0 01-4-4c0-1.5.8-2.8 2-3.5M2 12a4 4 0 014-4c1.5 0 2.8.8 3.5 2M22 12a4 4 0 01-4 4c-1.5 0-2.8-.8-3.5-2"/></svg>',
        "Iron Box": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 17h18l-3-8H6L3 17z"/><path d="M6 17v2M18 17v2"/></svg>',
        "Lights": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6H8.3A7 7 0 0112 2z"/></svg>',
        "Fridge": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M5 10h14M10 6v2M10 14v3"/></svg>',
        "Grinder": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><circle cx="12" cy="15" r="2"/></svg>',
        "Mixer": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><path d="M9 15h6"/></svg>',
        "Microwave": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="5" width="20" height="14" rx="2"/><rect x="5" y="8" width="11" height="8" rx="1"/><circle cx="19" cy="12" r="1"/></svg>',
        "Geyser": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="7" y="2" width="10" height="16" rx="2"/><path d="M10 18v4M14 18v4M10 8a2 2 0 004 0"/></svg>',
        "Washing Machine": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="2" width="18" height="20" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M6 6h2"/></svg>',
        "Lamp": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6H8.3A7 7 0 0112 2z"/></svg>',
    }
    DEFAULT_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/></svg>'

    for rname, rdata in rooms.items():
        label_suffix = " 🟢 LIVE" if rname in real_rooms else ""
        with st.expander(f"{rname}{label_suffix}  —  {rdata['total_power']:.0f} W  |  {rdata['temperature']} °C"):
            cols = st.columns(min(len(rdata["appliances"]), 5))
            for i, (app, adata) in enumerate(rdata["appliances"].items()):
                with cols[i % min(len(rdata["appliances"]), 5)]:
                    icon_svg  = APP_ICONS.get(app, DEFAULT_ICON)
                    ic        = "#2dd4bf" if adata["is_on"] else "#484f58"
                    bc        = "#2dd4bf44" if adata["is_on"] else "#21262d"
                    badge_cls = "badge-on" if adata["is_on"] else "badge-off"
                    render_html(f"""
                    <div style="background:#161b22;border:1px solid {bc};border-radius:10px;
                                padding:14px 10px;text-align:center;margin-bottom:6px">
                      <div style="color:{ic};margin-bottom:8px">{icon_svg}</div>
                      <div style="font-size:0.78rem;font-weight:600;color:#e6edf3;margin-bottom:6px">{app}</div>
                      <span class="badge {badge_cls}">{"ON" if adata["is_on"] else "OFF"}</span>
                      <div style="font-size:0.88rem;font-weight:700;color:{ic};margin-top:8px">{adata['power_w']:.0f} W</div>
                    </div>""")


# ── Page: Appliance Monitoring ─────────────────────────────────────────────────
def page_appliance_monitoring():
    inject_style()
    page_header("Appliance Monitoring", "Live appliance states, power usage and room-level control")

    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable.")
        return

    rooms = snap["rooms"]
    total = snap["total_power"]

    c1, c2, c3, c4 = st.columns(4)
    apps_on    = sum(1 for r in rooms.values() for a in r["appliances"].values() if a["is_on"])
    total_apps = sum(len(r["appliances"]) for r in rooms.values())
    monthly_kwh = round(total / 1000 * 8 * 30, 1)
    c1.metric("Total House Power",  f"{total:.0f} W")
    c2.metric("Appliances Running", f"{apps_on} / {total_apps}")
    c3.metric("Load Status",        "High Load" if total > 6000 else "Normal" if total > 2000 else "Low Load")
    c4.metric("Est. Monthly Usage", f"{monthly_kwh} kWh")

    section("SMS ALERT SETTINGS")
    if "phone_number" not in st.session_state:
        st.session_state.phone_number = ""
    ph1, ph2, ph3 = st.columns([2, 1, 1])
    with ph1:
        phone = st.text_input("Mobile number (E.164)", value=st.session_state.phone_number, placeholder="+919876543210")
        st.session_state.phone_number = phone
    with ph2:
        if st.button("Send Test SMS", use_container_width=True):
            if not phone:
                st.error("Enter a phone number first.")
            else:
                try:
                    r   = requests.post(f"{API}/notify/test", json={"phone_number": phone}, timeout=10)
                    res = r.json()
                    if res.get("status") == "sent":
                        st.success(f"Test SMS sent!")
                    elif res.get("status") == "skipped":
                        st.warning("Twilio not configured.")
                    else:
                        st.error(f"Failed: {res.get('reason', '')}")
                except Exception as e:
                    st.error(str(e))
    with ph3:
        if st.button("Check & Alert Now", use_container_width=True):
            if not phone:
                st.error("Enter a phone number first.")
            else:
                try:
                    r   = requests.post(f"{API}/notify/check", json={"phone_number": phone}, timeout=10)
                    res = r.json()
                    n   = res.get("alerts_triggered", 0)
                    st.success("No alerts.") if n == 0 else st.warning(f"{n} alert(s) sent to {phone}")
                except Exception as e:
                    st.error(str(e))

    try:
        sr  = requests.get(f"{API}/notify/status", timeout=3)
        cfg = sr.json()
        cls = "alert-success" if cfg["configured"] else "alert-warning"
        msg = (f"Twilio configured — sending from {cfg['from_number']}"
               if cfg["configured"]
               else "Twilio not configured. Fill in backend/.env")
        st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    except Exception:
        pass

    section("LIVE NOTIFICATIONS")
    alerts = []
    for rname, rdata in rooms.items():
        if rdata["temperature"] > 30:
            alerts.append(("danger",  f"OVERHEAT — {rname} at {rdata['temperature']} °C"))
        elif rdata["temperature"] > 27:
            alerts.append(("warning", f"HIGH TEMP — {rname} at {rdata['temperature']} °C"))
    if total > 6000:
        alerts.append(("danger",  f"OVERLOAD — {total:.0f} W exceeds safe limit (6000 W)"))
    elif total > 4000:
        alerts.append(("warning", f"HIGH LOAD — {total:.0f} W is elevated"))
    for rname, rdata in rooms.items():
        for app, adata in rdata["appliances"].items():
            if adata["is_on"] and adata["type"] == "occasional":
                alerts.append(("warning", f"LEFT ON — {app} in {rname} ({adata['power_w']:.0f} W)"))
    if not alerts:
        st.markdown('<div class="alert-box alert-success">All systems normal.</div>', unsafe_allow_html=True)
    else:
        for atype, msg in alerts[:6]:
            st.markdown(f'<div class="alert-box alert-{atype}">{msg}</div>', unsafe_allow_html=True)

    section("MONTHLY ENERGY BUDGET")
    if "monthly_budget_kwh" not in st.session_state:
        st.session_state.monthly_budget_kwh = 300.0
    cb1, cb2 = st.columns([2, 3])
    with cb1:
        budget = st.number_input("Monthly budget (kWh)", min_value=50.0, max_value=2000.0,
                                 value=st.session_state.monthly_budget_kwh, step=10.0)
        st.session_state.monthly_budget_kwh = budget
    with cb2:
        pct = min(monthly_kwh / budget * 100, 100) if budget > 0 else 0
        bar_color = "#f85149" if pct > 90 else "#d29922" if pct > 70 else "#3fb950"
        mhtml(textwrap.dedent(f"""
        <div style="margin-top:8px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px">
            <span style="font-size:0.8rem;color:#7d8590">Estimated this month</span>
            <span style="font-size:0.8rem;font-weight:700;color:{bar_color}">{monthly_kwh} / {budget:.0f} kWh ({pct:.1f}%)</span>
          </div>
          <div style="background:#21262d;border-radius:6px;height:10px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:6px"></div>
          </div>
          {'<div class="alert-box alert-danger" style="margin-top:10px">Budget exceeded!</div>' if pct >= 100 else
           '<div class="alert-box alert-warning" style="margin-top:10px">Approaching budget limit.</div>' if pct > 70 else
           '<div class="alert-box alert-success" style="margin-top:10px">Usage within budget.</div>'}
        </div>"""))

    section("APPLIANCES")
    APP_ICONS2 = {
        "AC": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="6" width="20" height="10" rx="2"/><path d="M6 16v3M18 16v3M8 11h8"/></svg>',
        "TV": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 20h8M12 18v2"/></svg>',
        "Fan": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 2a4 4 0 014 4c0 1.5-.8 2.8-2 3.5M12 22a4 4 0 01-4-4c0-1.5.8-2.8 2-3.5M2 12a4 4 0 014-4c1.5 0 2.8.8 3.5 2M22 12a4 4 0 01-4 4c-1.5 0-2.8-.8-3.5-2"/></svg>',
        "Iron Box": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 17h18l-3-8H6L3 17z"/><path d="M6 17v2M18 17v2"/></svg>',
        "Lights": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6H8.3A7 7 0 0112 2z"/></svg>',
        "Fridge": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M5 10h14M10 6v2M10 14v3"/></svg>',
        "Grinder": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><circle cx="12" cy="15" r="2"/></svg>',
        "Mixer": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><path d="M9 15h6"/></svg>',
        "Microwave": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="5" width="20" height="14" rx="2"/><rect x="5" y="8" width="11" height="8" rx="1"/><circle cx="19" cy="12" r="1"/></svg>',
        "Geyser": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="7" y="2" width="10" height="16" rx="2"/><path d="M10 18v4M14 18v4M10 8a2 2 0 004 0"/></svg>',
        "Washing Machine": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="2" width="18" height="20" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M6 6h2"/></svg>',
        "Lamp": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6H8.3A7 7 0 0112 2z"/></svg>',
    }
    DEFAULT_ICON2 = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 3"/></svg>'

    mode_info = fetch_sensor_mode()
    real_rooms_set = set(mode_info.get("rooms_reporting", []))

    for rname, rdata in rooms.items():
        is_real_room = rname in real_rooms_set
        room_label = f"{'🟢 ' if is_real_room else ''}{rname}"
        mhtml(textwrap.dedent(f"""
        <div style="background:#161b22;border:1px solid {'#3fb95033' if is_real_room else '#21262d'};
                    border-radius:12px;padding:18px 20px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
            <div style="font-size:0.95rem;font-weight:700;color:#e6edf3">{room_label}
              {'<span style="font-size:0.68rem;font-weight:700;color:#3fb950;margin-left:8px;padding:2px 8px;background:rgba(63,185,80,0.1);border-radius:10px">LIVE HARDWARE</span>' if is_real_room else ''}
            </div>
            <div style="font-size:0.78rem;color:#7d8590">{rdata["total_power"]:.0f} W · {rdata["temperature"]} °C</div>
          </div>
        </div>"""))

        n_apps = len(rdata["appliances"])
        cols   = st.columns(min(n_apps, 5))
        for i, (app_name, adata) in enumerate(rdata["appliances"].items()):
            with cols[i % min(n_apps, 5)]:
                is_on    = adata["is_on"]
                icon_svg = APP_ICONS2.get(app_name, DEFAULT_ICON2)
                ic       = "#2dd4bf" if is_on else "#484f58"
                bc       = "#2dd4bf44" if is_on else "#21262d"
                mhtml(textwrap.dedent(f"""
                <div style="background:#0d1117;border:1.5px solid {bc};border-radius:10px;
                            padding:14px 8px;text-align:center;margin-bottom:4px">
                  <div style="color:{ic};margin-bottom:8px">{icon_svg}</div>
                  <div style="font-size:0.78rem;font-weight:600;color:#e6edf3;margin-bottom:4px">{app_name}</div>
                  <div style="font-size:0.85rem;font-weight:700;color:{ic}">{adata["power_w"]:.0f} W</div>
                </div>"""))
                btn_label = f"Turn {'OFF' if is_on else 'ON'}"
                if st.button(btn_label, key=f"tog_{rname}_{app_name}", use_container_width=True):
                    try:
                        requests.post(f"{API}/toggle", json={"room": rname, "appliance": app_name, "is_on": not is_on}, timeout=5)
                        st.rerun()
                    except Exception:
                        st.error("Could not reach backend.")


# ── Page: Energy Analytics ─────────────────────────────────────────────────────
def page_energy_analytics():
    inject_style()
    page_header("Energy Analytics", "Live power trends, ML predictions from real sensor data")

    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable.")
        return

    total = snap["total_power"]
    st.session_state.history.append(total)
    if len(st.session_state.history) > 60:
        st.session_state.history = st.session_state.history[-60:]

    history = st.session_state.history
    times   = list(range(len(history)))

    section("TOTAL POWER — LIVE TREND")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=history, mode="lines",
                             line=dict(color="#2dd4bf", width=2.5), name="Total Power (W)",
                             fill="tozeroy", fillcolor="rgba(45,212,191,0.07)"))
    fig.add_hline(y=6000, line_dash="dot", line_color="#f85149", line_width=1.5,
                  annotation_text="High (6000 W)", annotation_font_color="#f85149")
    fig.add_hline(y=2000, line_dash="dot", line_color="#3fb950", line_width=1.5,
                  annotation_text="Low (2000 W)", annotation_font_color="#3fb950")
    fig.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
                      font=dict(color="#7d8590", family="Inter, sans-serif"),
                      xaxis=dict(title="Reading", gridcolor="#21262d", color="#7d8590"),
                      yaxis=dict(title="Power (W)", gridcolor="#21262d", color="#7d8590"),
                      margin=dict(l=50, r=20, t=20, b=50), height=320, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    section("PER-ROOM BREAKDOWN")
    rooms      = snap["rooms"]
    room_names = list(rooms.keys())
    room_pows  = [rooms[r]["total_power"] for r in room_names]
    fig2 = go.Figure(go.Bar(x=room_names, y=room_pows,
                            marker_color=[power_color(p) for p in room_pows],
                            text=[f"{p:.0f} W" for p in room_pows], textposition="outside"))
    fig2.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
                       font=dict(color="#7d8590", family="Inter, sans-serif"),
                       xaxis=dict(gridcolor="#21262d", color="#7d8590"),
                       yaxis=dict(title="Power (W)", gridcolor="#21262d", color="#7d8590"),
                       margin=dict(l=50, r=20, t=10, b=50), height=260, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    section("ML PREDICTION (trained on live DB data)")
    try:
        pr = requests.post(f"{API}/predict", json={"current_power": total}, timeout=5)
        if pr.status_code == 200:
            pd_data = pr.json()
            c1, c2  = st.columns(2)
            c1.metric("Predicted Next Reading", f"{pd_data['predicted_power']:.0f} W")
            c2.metric("Anomaly Status", "Anomaly Detected" if pd_data["is_anomaly"] else "Normal Pattern")
            if pd_data["is_anomaly"]:
                st.markdown('<div class="alert-box alert-warning">Unusual power pattern detected.</div>', unsafe_allow_html=True)
    except Exception:
        st.warning("ML prediction service unavailable.")

    section("RANDOM FOREST PREDICTION")
    try:
        import datetime as dt
        env, _   = fetch_environment()
        room_env = env.get("Bedroom 1", {})
        temp_val = room_env.get("temp_c",   28.0) or 28.0
        hum_val  = room_env.get("humidity", 65.0) or 65.0
        hour_val = dt.datetime.now().hour
        rf_r     = requests.post(f"{API}/predict/rf", json={
            "current_power": total, "temp_c": temp_val, "humidity": hum_val, "hour": hour_val,
        }, timeout=5)
        if rf_r.status_code == 200:
            rf = rf_r.json()
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("RF Predicted Power", f"{rf['predicted_power']:.0f} W")
            r2.metric("Temp Used",          f"{temp_val:.1f} °C")
            r3.metric("Humidity Used",      f"{hum_val:.0f} %")
            r4.metric("Hour of Day",        f"{hour_val}:00")
            cls = "alert-warning" if rf["is_anomaly"] else "alert-success"
            msg = "Anomaly detected by RF." if rf["is_anomaly"] else "RF: Normal pattern."
            st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    except Exception:
        st.warning("Random Forest prediction unavailable.")

    section("K-MEANS USAGE CLUSTERING")
    try:
        cl_r = requests.get(f"{API}/cluster?limit=100", timeout=5)
        if cl_r.status_code == 200:
            cl = cl_r.json()
            cluster_colors = {"Low": "#3fb950", "Normal": "#2dd4bf", "Peak": "#f85149"}
            current   = cl["current_cluster"]
            cur_color = cluster_colors.get(current, "#7d8590")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Current Cluster", current)
            k2.metric("Low Usage",       f"{cl['percentages']['Low']} %")
            k3.metric("Normal Usage",    f"{cl['percentages']['Normal']} %")
            k4.metric("Peak Usage",      f"{cl['percentages']['Peak']} %")
            st.markdown(f'<div class="alert-box alert-info" style="border-color:{cur_color}44;color:{cur_color}">{cl["advice"]}</div>', unsafe_allow_html=True)
            fig3 = go.Figure(go.Pie(labels=list(cl["counts"].keys()), values=list(cl["counts"].values()),
                                    marker_colors=["#3fb950", "#2dd4bf", "#f85149"], hole=0.5,
                                    textinfo="label+percent", textfont=dict(color="#e6edf3", size=13)))
            fig3.update_layout(paper_bgcolor="#161b22", font=dict(color="#7d8590", family="Inter, sans-serif"),
                               margin=dict(l=20, r=20, t=20, b=20), height=260, showlegend=True,
                               legend=dict(font=dict(color="#7d8590")))
            st.plotly_chart(fig3, use_container_width=True)
        elif cl_r.status_code == 400:
            st.info("Not enough data for clustering yet.")
    except Exception:
        st.warning("Clustering unavailable.")

    section("DECISION TREE — AUTOMATION ENGINE")
    try:
        import datetime as dt
        env, _   = fetch_environment()
        room_env = env.get("Bedroom 1", {})
        temp_dt  = room_env.get("temp_c",      28.0)  or 28.0
        motion   = room_env.get("motion",      False) or False
        smoke    = room_env.get("smoke_alert", False) or False
        hour_dt  = dt.datetime.now().hour
        at_r     = requests.post(f"{API}/automate", json={
            "temp_c": temp_dt, "motion": motion, "power_w": total,
            "hour": hour_dt, "smoke_alert": smoke,
        }, timeout=5)
        if at_r.status_code == 200:
            at = at_r.json()
            color_map = {"success": "#3fb950", "info": "#2dd4bf", "warning": "#d29922", "danger": "#f85149"}
            col = color_map.get(at["color"], "#2dd4bf")
            a1, a2 = st.columns([3, 1])
            with a1:
                mhtml(textwrap.dedent(f"""
                <div style="background:#161b22;border:2px solid {col}44;border-radius:12px;padding:20px">
                  <div style="font-size:0.72rem;color:#7d8590;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Recommended Action</div>
                  <div style="font-size:1.1rem;font-weight:700;color:{col}">{at["action"]}</div>
                  <div style="margin-top:12px;display:flex;gap:20px;font-size:0.78rem;color:#7d8590">
                    <span>Temp: <strong style="color:#e6edf3">{temp_dt:.1f} °C</strong></span>
                    <span>Motion: <strong style="color:#e6edf3">{"Yes" if motion else "No"}</strong></span>
                    <span>Power: <strong style="color:#e6edf3">{total:.0f} W</strong></span>
                    <span>Smoke: <strong style="color:#e6edf3">{"Yes" if smoke else "No"}</strong></span>
                  </div>
                </div>"""))
            with a2:
                mhtml(textwrap.dedent(f"""
                <div style="background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px;text-align:center">
                  <div style="font-size:0.72rem;color:#7d8590;margin-bottom:8px">Confidence</div>
                  <div style="font-size:2rem;font-weight:700;color:{col}">{at["confidence"]}%</div>
                </div>"""))
    except Exception:
        st.warning("Automation engine unavailable.")


# ── Page: Simulation & Hazard ──────────────────────────────────────────────────
def page_simulation():
    inject_style()
    page_header("Simulation & Hazard Prediction", "What-if analysis, load advisory, and risk detection")

    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable.")
        return

    current_power = snap["total_power"]
    c1, c2 = st.columns(2)
    c1.metric("Current Total Power", f"{current_power:.0f} W")
    c2.metric("Baseline Status", "High" if current_power > 6000 else "Normal" if current_power > 2000 else "Low")

    section("WHAT-IF SIMULATION")
    EXTRA_OPTIONS = ["Iron Box", "Washing Machine", "Microwave", "Geyser", "Grinder", "Mixer", "Extra AC", "Extra Heater"]
    selected = st.multiselect("Add appliances to simulate:", EXTRA_OPTIONS)

    if st.button("Run Simulation"):
        try:
            r = requests.post(f"{API}/simulate",
                              json={"current_power": current_power, "extra_appliances": selected}, timeout=5)
            if r.status_code == 200:
                res = r.json()
                section("SIMULATION RESULTS")
                r1, r2, r3 = st.columns(3)
                r1.metric("Simulated Total", f"{res['total_power']:.0f} W")
                r2.metric("Additional Load",  f"{res['extra_power']:.0f} W")
                level_cls = {"LOW": "level-low", "NORMAL": "level-normal", "HIGH": "level-high"}
                r3.markdown(f'<div style="padding-top:8px"><span class="level-badge {level_cls.get(res["level"], "level-normal")}">{res["level"]}</span></div>', unsafe_allow_html=True)

                section("ADVISORY")
                advice_cls = "alert-danger" if res["level"] == "HIGH" else "alert-info" if res["level"] == "NORMAL" else "alert-success"
                st.markdown(f'<div class="alert-box {advice_cls}">{res["advice"]}</div>', unsafe_allow_html=True)

                section("HAZARD & ANOMALY DETECTION")
                h1, h2, h3 = st.columns(3)
                with h1:
                    cls = "alert-danger" if res["hazard_risk"] else "alert-success"
                    msg = "<strong>Overload Risk</strong><br>Reduce load immediately." if res["hazard_risk"] else "No overload risk."
                    st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
                with h2:
                    cls = "alert-warning" if res["anomaly"] else "alert-success"
                    msg = "<strong>Anomaly Detected</strong><br>Unusual power pattern." if res["anomaly"] else "No anomaly detected."
                    st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
                with h3:
                    cls = "alert-danger" if res["fire_risk"] else "alert-success"
                    msg = "<strong>Fire / Overheat Risk</strong><br>Inspect appliances now." if res["fire_risk"] else "No fire risk."
                    st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)

                section("POWER GAUGE")
                lc_hex = {"LOW": "#3fb950", "NORMAL": "#2dd4bf", "HIGH": "#f85149"}.get(res["level"], "#2dd4bf")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=res["total_power"],
                    title={"text": "Simulated Load (W)", "font": {"color": "#7d8590", "size": 14}},
                    gauge={"axis": {"range": [0, 10000]}, "bar": {"color": lc_hex}, "bgcolor": "#0d1117",
                           "bordercolor": "#21262d",
                           "steps": [{"range": [0, 2000], "color": "rgba(63,185,80,0.12)"},
                                     {"range": [2000, 6000], "color": "rgba(45,212,191,0.08)"},
                                     {"range": [6000, 10000], "color": "rgba(248,81,73,0.12)"}],
                           "threshold": {"line": {"color": "#f85149", "width": 3}, "value": 8000}},
                    number={"font": {"color": "#e6edf3", "size": 28}},
                ))
                fig.update_layout(paper_bgcolor="#161b22", font=dict(family="Inter, sans-serif"),
                                  height=260, margin=dict(l=20, r=20, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Simulation error: {e}")

    section("MODEL MANAGEMENT")
    st.markdown(
        '<div class="alert-box alert-info">Models are trained on live sensor data from the database. '
        'Run <code>python notebooks/model_training.py</code> for full offline retraining.</div>',
        unsafe_allow_html=True,
    )
    if st.button("Retrain ML Models with Latest Live Data"):
        try:
            r = requests.post(f"{API}/retrain", timeout=10)
            if r.status_code == 200:
                d = r.json()
                st.success(f"Models retrained on {d.get('samples', '?')} samples.")
            else:
                st.error(r.json().get("detail", "Retrain failed."))
        except Exception as e:
            st.error(str(e))


# ── Page: IoT Sensors ──────────────────────────────────────────────────────────
def page_iot_sensors():
    inject_style()
    page_header("Smart Sensors", "Live room conditions, occupancy and safety monitoring")

    mode = fetch_sensor_mode()
    if mode["mode"] == "real":
        st.markdown(
            f'<div class="alert-box alert-success">● Real sensor data active — '
            f'receiving from: <strong>{", ".join(mode["rooms_reporting"]) or "—"}</strong></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="alert-box alert-info">◌ Simulation mode — ESP32 not connected yet. '
            'Flash the sketch and power the board.</div>',
            unsafe_allow_html=True,
        )

    env, fridge_door_open = fetch_environment()
    section("ROOM SAFETY & ENVIRONMENT STATUS")

    if not env:
        st.markdown('<div style="color:#484f58;font-size:0.88rem;padding:20px 0">No sensor data yet.</div>', unsafe_allow_html=True)
    else:
        any_smoke  = any(v.get("smoke_alert", False) for v in env.values())
        any_motion = any(v.get("motion",      False) for v in env.values())
        avg_temp   = sum(v["temp_c"]   for v in env.values() if v.get("temp_c")   is not None) / max(len(env), 1)
        avg_hum    = sum(v["humidity"] for v in env.values() if v.get("humidity") is not None) / max(len(env), 1)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rooms Reporting", len(env))
        k2.metric("Avg Temperature", f"{avg_temp:.1f} °C")
        k3.metric("Avg Humidity",    f"{avg_hum:.0f} %")
        k4.metric("Smoke Alert",     "⚠ YES" if any_smoke else "✓ Clear")

        if any_smoke:
            smoke_rooms = [r for r, v in env.items() if v.get("smoke_alert")]
            st.markdown(f'<div class="alert-box alert-danger">🔥 SMOKE in: <strong>{", ".join(smoke_rooms)}</strong>. Check immediately!</div>', unsafe_allow_html=True)
        if any_motion:
            motion_rooms = [r for r, v in env.items() if v.get("motion")]
            st.markdown(f'<div class="alert-box alert-warning">◉ Motion in: <strong>{", ".join(motion_rooms)}</strong>.</div>', unsafe_allow_html=True)

        # Fridge door status from reed switch
        fd_cls  = "alert-warning" if fridge_door_open else "alert-success"
        fd_icon = "🔓" if fridge_door_open else "🔒"
        fd_text = "Fridge door OPEN" if fridge_door_open else "Fridge door CLOSED"
        st.markdown(
            f'<div class="alert-box {fd_cls}" style="margin-top:8px">'
            f'{fd_icon} &nbsp;<strong>{fd_text}</strong> — Door sensor</div>',
            unsafe_allow_html=True,
        )

        room_list = list(env.items())
        for row_start in range(0, len(room_list), 2):
            cols = st.columns(2)
            for col_idx, (rname, edata) in enumerate(room_list[row_start: row_start + 2]):
                temp_e      = edata.get("temp_c",      None)
                humidity    = edata.get("humidity",    None)
                smoke_ppm   = edata.get("smoke_ppm",   None)
                smoke_alert = edata.get("smoke_alert", False)
                motion      = edata.get("motion",      False)
                card_cls    = "smoke-alert" if smoke_alert else "motion-on" if motion else "ok"
                with cols[col_idx]:
                    mhtml(textwrap.dedent(f"""
                    <div class="sensor-card {card_cls}" style="text-align:left;padding:20px">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                        <div style="font-size:0.95rem;font-weight:700;color:#e6edf3">{rname}</div>
                        <div style="display:flex;gap:6px">
                          {"<span class='sensor-pill pill-smoke'>⚠ SMOKE</span>"   if smoke_alert else "<span class='sensor-pill pill-clear'>✓ Air Clear</span>"}
                          {"<span class='sensor-pill pill-motion'>◉ Motion</span>" if motion      else "<span class='sensor-pill pill-idle'>◎ No Motion</span>"}
                        </div>
                      </div>
                      <div style="display:flex;gap:20px">
                        <div style="flex:1;background:#0d1117;border-radius:8px;padding:12px;text-align:center">
                          <div style="font-size:1.6rem;margin-bottom:4px">🌡</div>
                          <div class="sensor-label">Temperature</div>
                          <div class="sensor-value" style="font-size:1.5rem;color:{'#f85149' if temp_e and temp_e>30 else '#d29922' if temp_e and temp_e>27 else '#3fb950'}">
                            {f"{temp_e:.1f} °C" if temp_e is not None else "—"}
                          </div>
                        </div>
                        <div style="flex:1;background:#0d1117;border-radius:8px;padding:12px;text-align:center">
                          <div style="font-size:1.6rem;margin-bottom:4px">💧</div>
                          <div class="sensor-label">Humidity</div>
                          <div class="sensor-value" style="font-size:1.5rem;color:#2dd4bf">
                            {f"{humidity:.0f} %" if humidity is not None else "—"}
                          </div>
                        </div>
                        <div style="flex:1;background:#0d1117;border-radius:8px;padding:12px;text-align:center">
                          <div style="font-size:1.6rem;margin-bottom:4px">🔥</div>
                          <div class="sensor-label">MQ2 (ADC)</div>
                          <div class="sensor-value" style="font-size:1.5rem;color:{'#f85149' if smoke_alert else '#3fb950'}">
                            {f"{smoke_ppm:.0f}" if smoke_ppm is not None else "—"}
                          </div>
                          <div class="sensor-sub">threshold: 3000</div>
                        </div>
                      </div>
                    </div>"""))

    section("SENSOR MODE CONTROL")
    sc1, sc2 = st.columns([2, 1])
    with sc1:
        st.markdown('<div style="font-size:0.84rem;color:#7d8590;padding-top:8px">Reset to simulation mode to disconnect real sensors.</div>', unsafe_allow_html=True)
    with sc2:
        if st.button("Reset to Simulation Mode", use_container_width=True):
            try:
                r = requests.post(f"{API}/sensor/reset", timeout=5)
                if r.status_code == 200:
                    st.success("Reset done.")
                    st.rerun()
            except Exception as e:
                st.error(str(e))

    section("IOT EVENT LOG")
    events = fetch_iot_events(50)
    if not events:
        st.markdown('<div style="color:#484f58;font-size:0.84rem;padding:12px 0">No events recorded yet.</div>', unsafe_allow_html=True)
    else:
        EVENT_ICONS = {"smoke": "🔥", "motion": "👤", "clear_smoke": "✅", "clear_motion": "✅"}
        rows_html = ""
        for ev in reversed(events[-30:]):
            ts_raw  = ev.get("timestamp", "")
            ts_disp = ts_raw[11:19] if len(ts_raw) >= 19 else ts_raw
            icon    = EVENT_ICONS.get(ev.get("event_type", ""), "📡")
            msg     = ev.get("message", ev.get("event_type", ""))
            room    = ev.get("room", "")
            rows_html += f'<div class="event-row"><span class="event-time">{ts_disp}</span><span class="event-icon">{icon}</span><span class="event-msg">{msg}</span><span class="event-room">{room}</span></div>'
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;overflow:hidden;max-height:400px;overflow-y:auto">{rows_html}</div>',
            unsafe_allow_html=True,
        )


# ── Main router ────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        auth_page()
        return

    inject_style()

    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🏠 SmartHome</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-user">Signed in as {st.session_state.username}</div>', unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio(
            "Navigation",
            [
                "🛏  Bedroom 1 Control",
                "Digital Twin",
                "Appliance Monitoring",
                "Energy Analytics",
                "Simulation & Hazard",
                "IoT Sensors",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        auto_refresh = st.checkbox("Live updates", value=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.session_state.history   = []
            st.rerun()

    if   page == "🛏  Bedroom 1 Control":   page_bedroom1()
    elif page == "Digital Twin":             page_digital_twin()
    elif page == "Appliance Monitoring":     page_appliance_monitoring()
    elif page == "Energy Analytics":         page_energy_analytics()
    elif page == "Simulation & Hazard":      page_simulation()
    elif page == "IoT Sensors":              page_iot_sensors()

    if auto_refresh and page not in ("Simulation & Hazard", "IoT Sensors"):
        time.sleep(2)
        st.rerun()


if __name__ == "__main__":
    main()
