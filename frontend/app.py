import streamlit as st
import requests, time
import pandas as pd
import plotly.graph_objects as go

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SmartHome Energy Management",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
[data-testid="stAppViewContainer"]{background:#0d1117;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#0d1117;border-right:1px solid #21262d;}
[data-testid="stSidebar"] *{color:#7d8590 !important;}
[data-testid="stSidebar"] .stRadio label{font-size:.88rem;padding:5px 0;color:#c9d1d9 !important;}
.block-container{padding:2rem 2.5rem;max-width:1400px;background:#0d1117;}
.page-header{border-bottom:1px solid #21262d;padding-bottom:14px;margin-bottom:24px;}
.page-header h2{font-size:1.45rem;font-weight:700;color:#e6edf3;margin:0;letter-spacing:-.02em;}
.page-header p{font-size:.82rem;color:#7d8590;margin:5px 0 0 0;}
.section-title{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;
  color:#2dd4bf;margin:28px 0 12px 0;border-left:3px solid #2dd4bf;padding-left:8px;}
.floorplan-wrap{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:16px;}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.68rem;font-weight:700;letter-spacing:.04em;}
.badge-on{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.3);}
.badge-off{background:rgba(248,81,73,.12);color:#f85149;border:1px solid rgba(248,81,73,.3);}
.alert-box{border-radius:8px;padding:14px 18px;font-size:.84rem;font-weight:500;margin-top:8px;line-height:1.5;}
.alert-danger{background:rgba(248,81,73,.1);border:1px solid rgba(248,81,73,.35);color:#ffa198;}
.alert-warning{background:rgba(210,153,34,.1);border:1px solid rgba(210,153,34,.35);color:#e3b341;}
.alert-info{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.3);color:#2dd4bf;}
.alert-success{background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.3);color:#3fb950;}
.level-badge{display:inline-block;padding:6px 22px;border-radius:6px;font-size:.88rem;font-weight:700;letter-spacing:.06em;}
.level-low{background:rgba(63,185,80,.15);color:#3fb950;}
.level-normal{background:rgba(45,212,191,.12);color:#2dd4bf;}
.level-high{background:rgba(248,81,73,.15);color:#f85149;}
.auth-wrap{max-width:420px;margin:60px auto 0 auto;background:#161b22;border:1px solid #21262d;
  border-radius:14px;padding:36px 40px;box-shadow:0 8px 32px rgba(0,0,0,.4);}
.auth-title{font-size:1.35rem;font-weight:700;color:#e6edf3;text-align:center;margin-bottom:4px;}
.auth-sub{font-size:.8rem;color:#7d8590;text-align:center;margin-bottom:28px;}
.sidebar-brand{font-size:1rem;font-weight:700;color:#2dd4bf !important;letter-spacing:-.01em;padding:8px 0 2px 0;}
.sidebar-user{font-size:.75rem;color:#484f58 !important;margin-bottom:16px;}
.stButton>button{background:#0d9488;color:#fff;border:none;border-radius:7px;font-weight:600;font-size:.88rem;padding:10px 20px;transition:background .2s;}
.stButton>button:hover{background:#0f766e;}
div[data-testid="metric-container"]{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;box-shadow:0 2px 8px rgba(0,0,0,.3);}
[data-testid="stMetricLabel"]{font-size:.68rem !important;color:#7d8590 !important;font-weight:600 !important;text-transform:uppercase;letter-spacing:.08em;}
[data-testid="stMetricValue"]{font-size:1.5rem !important;color:#e6edf3 !important;font-weight:700 !important;}
.stDataFrame{border-radius:8px;overflow:hidden;}
.stExpander{background:#161b22 !important;border:1px solid #21262d !important;border-radius:8px !important;}
.stExpander summary{color:#c9d1d9 !important;font-weight:600;}
.stTabs [data-baseweb="tab"]{color:#7d8590 !important;}
.stTabs [aria-selected="true"]{color:#2dd4bf !important;border-bottom-color:#2dd4bf !important;}
input,textarea,select{background:#0d1117 !important;color:#e6edf3 !important;border-color:#21262d !important;}
.main .block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px;}
.panel-card{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:14px 16px;margin-bottom:12px;}
.metric-card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:10px 12px;text-align:center;min-height:96px;display:flex;flex-direction:column;justify-content:center;}
.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:10px;}
.kpi-card{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:10px 12px;text-align:center;}
.kpi-label{font-size:.62rem;color:#7d8590;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;}
.kpi-value{font-size:1.1rem;font-weight:700;color:#e6edf3;}
.floorplan-wrap{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:12px;overflow-x:auto;}
.control-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid #21262d;}
.control-row:last-child{border-bottom:none;}
</style>
"""

for key, val in [("logged_in",False),("username",""),("history",[]),("monthly_budget_kwh",300.0),("phone_number","")]:
    if key not in st.session_state:
        st.session_state[key] = val

def fetch_snapshot():
    try:
        r = requests.get(f"{API}/generate", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def power_color(w):
    if w > 6000: return "#f85149"
    if w > 3000: return "#d29922"
    return "#3fb950"

def temp_color(t):
    if t > 30: return "#f85149"
    if t > 27: return "#d29922"
    return "#3fb950"

def room_class(p):
    if p > 6000: return "alert"
    if p > 3000: return "warn"
    return ""

def inject_style():
    st.markdown(STYLE, unsafe_allow_html=True)

def page_header(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="page-header"><h2>{title}</h2>{sub}</div>', unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)

APP_ICONS = {
    "AC":              '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="10" rx="2"/><path d="M6 16v3M18 16v3M8 11h8"/></svg>',
    "TV":              '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 20h8M12 18v2"/></svg>',
    "Iron Box":        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17h18l-3-8H6L3 17z"/><path d="M6 17v2M18 17v2"/></svg>',
    "Lights":          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.5-1.3 4.7-3.3 6H8.3A7 7 0 0112 2z"/></svg>',
    "Fridge":          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M5 10h14M10 6v2M10 14v3"/></svg>',
    "Grinder":         '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><circle cx="12" cy="15" r="2"/></svg>',
    "Mixer":           '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3h8l2 6H6L8 3z"/><rect x="6" y="9" width="12" height="12" rx="2"/><path d="M9 15h6"/></svg>',
    "Microwave":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><rect x="5" y="8" width="11" height="8" rx="1"/><circle cx="19" cy="12" r="1"/></svg>',
    "Geyser":          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="7" y="2" width="10" height="16" rx="2"/><path d="M10 18v4M14 18v4M10 8a2 2 0 004 0"/></svg>',
    "Washing Machine": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="2" width="18" height="20" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M6 6h2"/></svg>',
}
DEFAULT_APP_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/></svg>'

def auth_page():
    inject_style()
    st.markdown('<div class="auth-wrap"><div class="auth-title">SmartHome Platform</div><div class="auth-sub">AI-Driven Energy Management &amp; Digital Twin</div></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username")
                pwd   = st.text_input("Password", type="password")
                sub   = st.form_submit_button("Sign In", use_container_width=True)
            if sub:
                if not uname or not pwd:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        r = requests.post(f"{API}/login", json={"username": uname, "password": pwd}, timeout=5)
                        if r.status_code == 200:
                            st.session_state.logged_in = True
                            st.session_state.username  = uname
                            st.rerun()
                        elif r.status_code == 401:
                            st.error("Invalid credentials. Please create an account if you are new.")
                        else:
                            st.error(r.json().get("detail", "Login failed."))
                    except Exception:
                        st.error("Cannot reach backend. Ensure the API server is running.")
        with tab_signup:
            with st.form("signup_form"):
                nu = st.text_input("Username")
                np = st.text_input("Password", type="password")
                np2= st.text_input("Confirm Password", type="password")
                sub2 = st.form_submit_button("Create Account", use_container_width=True)
            if sub2:
                if not nu or not np:
                    st.error("Please fill in all fields.")
                elif np != np2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        r = requests.post(f"{API}/signup", json={"username": nu, "password": np}, timeout=5)
                        if r.status_code == 200:
                            st.success("Account created. Please sign in.")
                        else:
                            st.error(r.json().get("detail", "Signup failed."))
                    except Exception:
                        st.error("Cannot reach backend.")


def page_digital_twin():
    inject_style()
    page_header("Digital Twin", "Real-time floor plan with live sensor data")
    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable. Start the FastAPI server and refresh.")
        return
    rooms = snap["rooms"]
    total = snap["total_power"]
    st.session_state.history.append(total)
    if len(st.session_state.history) > 60:
        st.session_state.history = st.session_state.history[-60:]

    apps_on    = sum(1 for r in rooms.values() for a in r["appliances"].values() if a["is_on"])
    total_apps = sum(len(r["appliances"]) for r in rooms.values())
    avg_temp   = round(sum(r["temperature"] for r in rooms.values()) / len(rooms), 1)

    metric_cols = st.columns(4)
    metric_items = [
        ("Total Power", f"{total:.0f} W", "#2dd4bf"),
        ("Avg Temperature", f"{avg_temp} C", "#d29922"),
        ("Appliances Active", f"{apps_on} / {total_apps}", "#3fb950"),
        ("User", st.session_state.username, "#c9d1d9"),
    ]
    for col, (label, value, color) in zip(metric_cols, metric_items):
        with col:
            st.markdown(f'<div class="metric-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:{color}">{value}</div></div>', unsafe_allow_html=True)

    left, center, right = st.columns([1.1, 2.4, 1.1])

    with left:
        section("IOT SENSORS")
        lr = rooms["Living Room"]
        sensors = [
            ("Temperature", f"{lr['temperature']} C", lr['temperature'] / 40),
            ("CO2 Level",   "118 ppm",                0.12),
            ("Humidity",    "58%",                    0.58),
            ("Motion",      "Detected",               1.0),
            ("Total Power", f"{total:.0f} W",         min(total/8000, 1)),
        ]
        s_html = ""
        for lbl, val, pct in sensors:
            bar_col = "#2dd4bf"
            s_html += f"""<div style="padding:6px 0;border-bottom:1px solid #21262d;">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                <span style="font-size:.72rem;color:#7d8590;">{lbl}</span>
                <span style="font-size:.75rem;font-weight:700;color:#e6edf3;">{val}</span>
              </div>
              <div style="background:#21262d;border-radius:2px;height:3px;">
                <div style="width:{int(pct*100)}%;height:3px;background:{bar_col};border-radius:2px;"></div>
              </div></div>"""
        st.markdown(s_html, unsafe_allow_html=True)

        section("APPLIANCE CONTROL")
        for rname, rdata in rooms.items():
            for app_name, adata in rdata["appliances"].items():
                is_on   = adata["is_on"]
                ic      = APP_ICONS.get(app_name, DEFAULT_APP_ICON)
                ic_col  = "#2dd4bf" if is_on else "#484f58"
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;
                      padding:5px 6px;background:#0d1117;border:1px solid #21262d;
                      border-radius:6px;margin-bottom:3px;">
                      <div style="color:{ic_col}">{ic}</div>
                      <div>
                        <div style="font-size:.72rem;font-weight:600;color:#e6edf3;">{app_name}</div>
                        <div style="font-size:.62rem;color:#7d8590;">{adata['power_w']:.0f}W</div>
                      </div></div>""", unsafe_allow_html=True)
                with col_b:
                    if st.button("ON" if is_on else "OFF", key=f"dt_{rname}_{app_name}", use_container_width=True):
                        try:
                            requests.post(f"{API}/toggle", json={"room": rname, "appliance": app_name, "is_on": not is_on}, timeout=5)
                            st.rerun()
                        except Exception:
                            pass

    with center:
        section("FLOOR PLAN")
        def dot_row(rname):
            dots = ""
            for app, adata in rooms[rname]["appliances"].items():
                c = "#3fb950" if adata["is_on"] else "#21262d"
                dots += f'<circle r="4" cx="{len(dots)//50*10}" cy="0" fill="{c}"/>'
            return dots

        lr  = rooms["Living Room"];  lr_pc  = power_color(lr["total_power"])
        kit = rooms["Kitchen"];      kit_pc = power_color(kit["total_power"])
        b1  = rooms["Bedroom 1"];    b1_pc  = power_color(b1["total_power"])
        b2  = rooms["Bedroom 2"];    b2_pc  = power_color(b2["total_power"])
        wsh = rooms["Washroom"];     wsh_pc = power_color(wsh["total_power"])
        utl = rooms["Utility"];      utl_pc = power_color(utl["total_power"])

        def room_fill(rname):
            p = rooms[rname]["total_power"]
            if p > 6000: return "rgba(248,81,73,0.18)"
            if p > 3000: return "rgba(210,153,34,0.15)"
            return "rgba(63,185,80,0.08)"

        def app_dots(rname):
            dots = ""
            x = 0
            for app, adata in rooms[rname]["appliances"].items():
                c = "#3fb950" if adata["is_on"] else "#30363d"
                dots += f'<circle cx="{x}" cy="0" r="4" fill="{c}"><title>{app}</title></circle>'
                x += 12
            return dots

        svg = f"""<div class="floorplan-wrap">
<svg viewBox="0 0 620 420" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">
  <defs>
    <style>
      .pf{{stroke-dasharray:6,4;animation:dash 2s linear infinite;}}
      @keyframes dash{{to{{stroke-dashoffset:-20;}}}}
    </style>
  </defs>
  <rect width="620" height="420" fill="#0d1117"/>
  <rect x="10" y="10" width="600" height="400" rx="8" fill="#0d1117" stroke="#21262d" stroke-width="2"/>
  <text x="310" y="28" text-anchor="middle" font-size="9" fill="#7d8590" font-family="monospace" letter-spacing="3">N (ENTRANCE)</text>
  <line x1="310" y1="30" x2="310" y2="42" stroke="#2dd4bf" stroke-width="1.5"/>
  <polygon points="310,30 306,38 310,36 314,38" fill="#2dd4bf"/>

  <!-- LIVING ROOM -->
  <rect x="20" y="50" width="290" height="160" rx="4" fill="{room_fill('Living Room')}" stroke="{lr_pc}" stroke-width="1.5"/>
  <text x="35" y="70" font-size="9" fill="#7d8590" font-family="monospace" font-weight="600">LIVING ROOM</text>
  <text x="35" y="88" font-size="13" fill="{temp_color(lr['temperature'])}" font-weight="700">{lr['temperature']}C</text>
  <text x="35" y="104" font-size="11" fill="{lr_pc}">{lr['total_power']:.0f} W</text>
  <g transform="translate(35,116)">{app_dots('Living Room')}</g>
  <text x="165" y="195" text-anchor="middle" font-size="13" fill="#c9d1d9" font-weight="700">Living Room</text>

  <!-- KITCHEN -->
  <rect x="320" y="50" width="290" height="160" rx="4" fill="{room_fill('Kitchen')}" stroke="{kit_pc}" stroke-width="1.5"/>
  <text x="335" y="70" font-size="9" fill="#7d8590" font-family="monospace" font-weight="600">KITCHEN</text>
  <text x="335" y="88" font-size="13" fill="{temp_color(kit['temperature'])}" font-weight="700">{kit['temperature']}C</text>
  <text x="335" y="104" font-size="11" fill="{kit_pc}">{kit['total_power']:.0f} W</text>
  <g transform="translate(335,116)">{app_dots('Kitchen')}</g>
  <text x="465" y="195" text-anchor="middle" font-size="13" fill="#c9d1d9" font-weight="700">Kitchen</text>

  <!-- DIVIDER WALL -->
  <rect x="308" y="50" width="12" height="160" fill="#0d1117" stroke="#21262d" stroke-width="1"/>
  <rect x="308" y="110" width="12" height="40" fill="rgba(255,184,0,0.06)" stroke="#d29922" stroke-width="1"/>

  <!-- HORIZONTAL WALL -->
  <rect x="20" y="218" width="590" height="10" fill="#0d1117" stroke="#21262d" stroke-width="1"/>
  <rect x="80" y="218" width="50" height="10" fill="rgba(255,184,0,0.06)" stroke="#d29922" stroke-width="1"/>
  <rect x="430" y="218" width="50" height="10" fill="rgba(255,184,0,0.06)" stroke="#d29922" stroke-width="1"/>

  <!-- BEDROOM 1 -->
  <rect x="20" y="228" width="145" height="170" rx="4" fill="{room_fill('Bedroom 1')}" stroke="{b1_pc}" stroke-width="1.5"/>
  <text x="30" y="246" font-size="8" fill="#7d8590" font-family="monospace">BEDROOM 1</text>
  <text x="30" y="262" font-size="11" fill="{temp_color(b1['temperature'])}" font-weight="700">{b1['temperature']}C</text>
  <text x="30" y="276" font-size="10" fill="{b1_pc}">{b1['total_power']:.0f} W</text>
  <g transform="translate(30,286)">{app_dots('Bedroom 1')}</g>
  <text x="92" y="385" text-anchor="middle" font-size="11" fill="#c9d1d9" font-weight="700">Bedroom 1</text>

  <!-- BEDROOM 2 -->
  <rect x="175" y="228" width="145" height="170" rx="4" fill="{room_fill('Bedroom 2')}" stroke="{b2_pc}" stroke-width="1.5"/>
  <text x="185" y="246" font-size="8" fill="#7d8590" font-family="monospace">BEDROOM 2</text>
  <text x="185" y="262" font-size="11" fill="{temp_color(b2['temperature'])}" font-weight="700">{b2['temperature']}C</text>
  <text x="185" y="276" font-size="10" fill="{b2_pc}">{b2['total_power']:.0f} W</text>
  <g transform="translate(185,286)">{app_dots('Bedroom 2')}</g>
  <text x="247" y="385" text-anchor="middle" font-size="11" fill="#c9d1d9" font-weight="700">Bedroom 2</text>

  <!-- WASHROOM -->
  <rect x="330" y="228" width="130" height="170" rx="4" fill="{room_fill('Washroom')}" stroke="{wsh_pc}" stroke-width="1.5"/>
  <text x="340" y="246" font-size="8" fill="#7d8590" font-family="monospace">WASHROOM</text>
  <text x="340" y="262" font-size="11" fill="{temp_color(wsh['temperature'])}" font-weight="700">{wsh['temperature']}C</text>
  <text x="340" y="276" font-size="10" fill="{wsh_pc}">{wsh['total_power']:.0f} W</text>
  <g transform="translate(340,286)">{app_dots('Washroom')}</g>
  <text x="395" y="385" text-anchor="middle" font-size="11" fill="#c9d1d9" font-weight="700">Washroom</text>

  <!-- UTILITY -->
  <rect x="470" y="228" width="140" height="170" rx="4" fill="{room_fill('Utility')}" stroke="{utl_pc}" stroke-width="1.5"/>
  <text x="480" y="246" font-size="8" fill="#7d8590" font-family="monospace">UTILITY</text>
  <text x="480" y="262" font-size="11" fill="{temp_color(utl['temperature'])}" font-weight="700">{utl['temperature']}C</text>
  <text x="480" y="276" font-size="10" fill="{utl_pc}">{utl['total_power']:.0f} W</text>
  <g transform="translate(480,286)">{app_dots('Utility')}</g>
  <text x="540" y="385" text-anchor="middle" font-size="11" fill="#c9d1d9" font-weight="700">Utility</text>

  <!-- ENERGY METER -->
  <rect x="240" y="168" width="140" height="46" rx="6" fill="#161b22" stroke="#2dd4bf" stroke-width="1.5"/>
  <text x="310" y="186" text-anchor="middle" font-size="8" fill="#7d8590" font-family="monospace">ENERGY METER</text>
  <text x="310" y="202" text-anchor="middle" font-size="13" fill="#2dd4bf" font-weight="700">{total:.0f} W</text>

  <!-- POWER FLOW LINES -->
  <line x1="165" y1="210" x2="240" y2="191" stroke="#2dd4bf" stroke-width="1.2" class="pf"/>
  <line x1="465" y1="210" x2="380" y2="191" stroke="#2dd4bf" stroke-width="1.2" class="pf"/>
  <line x1="310" y1="214" x2="310" y2="228" stroke="#2dd4bf" stroke-width="1.2" class="pf"/>

  <!-- LEGEND -->
  <circle cx="25" cy="408" r="4" fill="#3fb950"/>
  <text x="33" y="412" font-size="8" fill="#7d8590">ON</text>
  <circle cx="55" cy="408" r="4" fill="#30363d" stroke="#7d8590" stroke-width="1"/>
  <text x="63" y="412" font-size="8" fill="#7d8590">OFF</text>
  <rect x="88" y="403" width="8" height="8" fill="rgba(248,81,73,0.3)" stroke="#f85149" stroke-width="1"/>
  <text x="100" y="412" font-size="8" fill="#7d8590">High</text>
  <rect x="128" y="403" width="8" height="8" fill="rgba(210,153,34,0.2)" stroke="#d29922" stroke-width="1"/>
  <text x="140" y="412" font-size="8" fill="#7d8590">Medium</text>
  <rect x="185" y="403" width="8" height="8" fill="rgba(63,185,80,0.15)" stroke="#3fb950" stroke-width="1"/>
  <text x="197" y="412" font-size="8" fill="#7d8590">Normal</text>
</svg></div>"""
        st.markdown(svg, unsafe_allow_html=True)

        if len(st.session_state.history) > 1:
            section("ENERGY HISTORY")
            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                y=st.session_state.history,
                marker_color=[power_color(v) for v in st.session_state.history],
                showlegend=False,
            ))
            fig_h.update_layout(
                paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
                margin=dict(l=0,r=0,t=0,b=0), height=80,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=True, gridcolor="#21262d", color="#7d8590", tickfont=dict(size=8)),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

    with right:
        section("OVERVIEW")
        kwh_today = round(total / 1000 * 8, 2)
        est_cost  = round(kwh_today * 7.5, 2)
        budget    = st.session_state.monthly_budget_kwh
        pct_used  = min(kwh_today * 30 / max(budget, 1) * 100, 100)
        pct_saved = max(0, round(100 - pct_used, 1))

        alerts_list = []
        for rn, rdata in rooms.items():
            if rdata["total_power"] > 6000:
                alerts_list.append(("danger", f"{rn}: Critical {rdata['total_power']:.0f}W"))
            elif rdata["total_power"] > 3000:
                alerts_list.append(("warning", f"{rn}: High {rdata['total_power']:.0f}W"))
            if rdata["temperature"] > 30:
                alerts_list.append(("danger", f"{rn}: Overheat {rdata['temperature']}C"))

        st.markdown(f"""
        <div class="metric-grid">
          <div class="kpi-card"><div class="kpi-label">kWh Today</div><div class="kpi-value" style="color:#2dd4bf">{kwh_today}</div></div>
          <div class="kpi-card"><div class="kpi-label">Est Cost</div><div class="kpi-value" style="color:#d29922">Rs{est_cost}</div></div>
          <div class="kpi-card"><div class="kpi-label">Saved</div><div class="kpi-value" style="color:#3fb950">{pct_saved}%</div></div>
          <div class="kpi-card"><div class="kpi-label">Alerts</div><div class="kpi-value" style="color:{'#f85149' if alerts_list else '#3fb950'}">{len(alerts_list)}</div></div>
        </div>""", unsafe_allow_html=True)

        section("LIVE ALERTS")
        if not alerts_list:
            st.markdown('<div class="alert-box alert-success">All systems normal</div>', unsafe_allow_html=True)
        else:
            for kind, msg in alerts_list[:5]:
                st.markdown(f'<div class="alert-box alert-{kind}">{msg}</div>', unsafe_allow_html=True)

        section("ENERGY FORECAST")
        room_powers = {rn: rd["total_power"] for rn, rd in rooms.items()}
        max_p = max(room_powers.values()) if room_powers else 1
        for rn, pw in room_powers.items():
            pct = int(pw / max(max_p, 1) * 100)
            col = power_color(pw)
            st.markdown(f"""
            <div style="margin-bottom:6px;">
              <div style="display:flex;justify-content:space-between;font-size:.7rem;color:#7d8590;margin-bottom:2px;">
                <span>{rn}</span><span style="color:{col}">{pct}%</span>
              </div>
              <div style="background:#21262d;border-radius:3px;height:4px;">
                <div style="width:{pct}%;background:{col};height:4px;border-radius:3px;"></div>
              </div>
            </div>""", unsafe_allow_html=True)


def page_appliance_monitoring():
    inject_style()
    page_header("Appliance Monitoring", "Visual appliance controls with ON/OFF toggles")
    snap = fetch_snapshot()
    if not snap:
        st.error("Backend unreachable.")
        return
    rooms = snap["rooms"]
    total = snap["total_power"]
    apps_on    = sum(1 for r in rooms.values() for a in r["appliances"].values() if a["is_on"])
    total_apps = sum(len(r["appliances"]) for r in rooms.values())
    monthly_kwh = round(total / 1000 * 8 * 30, 1)
    status = "High Load" if total > 6000 else "Normal" if total > 2000 else "Low Load"
    metric_cols = st.columns(4)
    metric_items = [
        ("Total Power", f"{total:.0f} W", "#2dd4bf"),
        ("Appliances Running", f"{apps_on}/{total_apps}", "#3fb950"),
        ("Load Status", status, "#d29922"),
        ("Est. Monthly", f"{monthly_kwh} kWh", "#c9d1d9"),
    ]
    for col, (label, value, color) in zip(metric_cols, metric_items):
        with col:
            st.markdown(f'<div class="metric-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:{color}">{value}</div></div>', unsafe_allow_html=True)

    section("SMS ALERT SETTINGS")
    ph_c1, ph_c2, ph_c3 = st.columns([2,1,1])
    with ph_c1:
        phone = st.text_input("Mobile number (E.164)", value=st.session_state.phone_number, placeholder="+919876543210")
        st.session_state.phone_number = phone
    with ph_c2:
        if st.button("Send Test SMS", use_container_width=True):
            if not phone:
                st.error("Enter a number first.")
            else:
                try:
                    r = requests.post(f"{API}/notify/test", json={"phone_number": phone}, timeout=10)
                    res = r.json()
                    if res.get("status") == "sent":
                        st.success("Test SMS sent!")
                    elif res.get("status") == "skipped":
                        st.warning("Twilio not configured. Fill backend/.env")
                    else:
                        st.error(res.get("reason","Failed"))
                except Exception as e:
                    st.error(str(e))
    with ph_c3:
        if st.button("Check & Alert Now", use_container_width=True):
            if not phone:
                st.error("Enter a number first.")
            else:
                try:
                    r = requests.post(f"{API}/notify/check", json={"phone_number": phone}, timeout=10)
                    res = r.json()
                    n = res.get("alerts_triggered", 0)
                    if n == 0:
                        st.success("No alerts — all normal.")
                    else:
                        st.warning(f"{n} alert(s) sent to {phone}")
                except Exception as e:
                    st.error(str(e))
    try:
        sr = requests.get(f"{API}/notify/status", timeout=3)
        if sr.status_code == 200:
            cfg = sr.json()
            if cfg["configured"]:
                st.markdown(f'<div class="alert-box alert-success">Twilio configured — from {cfg["from_number"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-box alert-warning">Twilio not configured. Open backend/.env and fill credentials.</div>', unsafe_allow_html=True)
    except Exception:
        pass

    section("LIVE NOTIFICATIONS")
    alerts = []
    for rname, rdata in rooms.items():
        if rdata["temperature"] > 30:
            alerts.append(("danger", f"OVERHEAT — {rname}: {rdata['temperature']}C"))
        elif rdata["temperature"] > 27:
            alerts.append(("warning", f"HIGH TEMP — {rname}: {rdata['temperature']}C"))
        if rdata["total_power"] > 6000:
            alerts.append(("danger", f"OVERLOAD — {rname}: {rdata['total_power']:.0f} W"))
        for app, adata in rdata["appliances"].items():
            if adata["is_on"] and adata["type"] == "occasional":
                alerts.append(("warning", f"LEFT ON — {app} in {rname} ({adata['power_w']:.0f} W)"))
    if not alerts:
        st.markdown('<div class="alert-box alert-success">All systems normal. No alerts.</div>', unsafe_allow_html=True)
    else:
        for atype, msg in alerts[:6]:
            st.markdown(f'<div class="alert-box alert-{atype}">{msg}</div>', unsafe_allow_html=True)

    section("MONTHLY ENERGY BUDGET")
    bc1, bc2 = st.columns([2,3])
    with bc1:
        budget = st.number_input("Budget (kWh/month)", min_value=50.0, max_value=2000.0,
                                  value=st.session_state.monthly_budget_kwh, step=10.0)
        st.session_state.monthly_budget_kwh = budget
    with bc2:
        pct = min(monthly_kwh / budget * 100, 100) if budget > 0 else 0
        bar_col = "#f85149" if pct > 90 else "#d29922" if pct > 70 else "#3fb950"
        st.markdown(f"""
        <div style="margin-top:8px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:.8rem;color:#7d8590;">Estimated usage</span>
            <span style="font-size:.8rem;font-weight:700;color:{bar_col}">{monthly_kwh} / {budget:.0f} kWh ({pct:.1f}%)</span>
          </div>
          <div style="background:#21262d;border-radius:6px;height:10px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{bar_col};border-radius:6px;"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    section("APPLIANCE CONTROLS")
    for rname, rdata in rooms.items():
        with st.container():
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;border-radius:12px;padding:14px 16px;margin-bottom:14px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div style="font-size:.95rem;font-weight:700;color:#e6edf3;">{rname}</div>
                <div style="font-size:.75rem;color:#7d8590;">{rdata['total_power']:.0f} W • {rdata['temperature']}C</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            appliance_items = list(rdata["appliances"].items())
            cols_per_row = 3
            for start in range(0, len(appliance_items), cols_per_row):
                row_items = appliance_items[start:start + cols_per_row]
                cols = st.columns(cols_per_row)
                for idx, (app_name, adata) in enumerate(row_items):
                    with cols[idx]:
                        is_on = adata["is_on"]
                        ic = APP_ICONS.get(app_name, DEFAULT_APP_ICON)
                        ic_col = "#2dd4bf" if is_on else "#7d8590"
                        bdr = "#2dd4bf44" if is_on else "#21262d"
                        pw_col = "#2dd4bf" if is_on else "#484f58"
                        st.markdown(f"""
                        <div style="background:#0d1117;border:1px solid {bdr};border-radius:10px;padding:10px 8px;text-align:center;margin-bottom:8px;min-height:120px;">
                          <div style="color:{ic_col};margin-bottom:6px;">{ic}</div>
                          <div style="font-size:.75rem;font-weight:600;color:#e6edf3;margin-bottom:4px;">{app_name}</div>
                          <div style="font-size:.82rem;font-weight:700;color:{pw_col};margin-bottom:2px;">{adata['power_w']:.0f} W</div>
                          <div style="font-size:.62rem;color:#484f58;">{adata['type'].capitalize()}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        btn_lbl = "Turn OFF" if is_on else "Turn ON"
                        if st.button(btn_lbl, key=f"mon_{rname}_{app_name}", use_container_width=True):
                            try:
                                requests.post(f"{API}/toggle", json={"room": rname, "appliance": app_name, "is_on": not is_on}, timeout=5)
                                st.rerun()
                            except Exception:
                                st.error("Could not reach backend.")


if not st.session_state.logged_in:
    auth_page()
else:
    st.sidebar.markdown(f"<div class='sidebar-brand'>SmartHome</div><div class='sidebar-user'>Signed in as {st.session_state.username}</div>", unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", ["Digital Twin", "Appliance Monitoring"], index=0)
    if page == "Digital Twin":
        page_digital_twin()
    else:
        page_appliance_monitoring()

