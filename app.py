import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import random
import sqlite3
import hashlib

# ─────────────────────────────
# DATABASE
# ─────────────────────────────
def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit(); conn.close()

def make_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def add_user(u, pw):
    try:
        conn = sqlite3.connect('users.db')
        conn.execute('INSERT INTO users VALUES (?,?)', (u, make_hash(pw)))
        conn.commit(); conn.close(); return True
    except: return False

def login_user(u, pw):
    conn = sqlite3.connect('users.db')
    r = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (u, make_hash(pw))).fetchall()
    conn.close(); return r

def db_audit():
    """Print all registered users to the terminal."""
    conn = sqlite3.connect('users.db')
    rows = conn.execute('SELECT username, password FROM users').fetchall()
    conn.close()
    print("\n" + "="*55)
    print("  [DB AUDIT] AstraRoute Navigator — Registered Users")
    print("="*55)
    if rows:
        for i, (uname, phash) in enumerate(rows, 1):
            print(f"  {i}. Username : {uname}")
            print(f"     Hash     : {phash[:20]}...")
    else:
        print("  No users registered yet.")
    print("="*55 + "\n")

# ─────────────────────────────
# SETUP
# ─────────────────────────────
st.set_page_config(page_title="AstraRoute Navigator", page_icon="🚕", layout="wide")
init_db()

# ─────────────────────────────
# GRAPH
# ─────────────────────────────
LOCS = {
    "Vasant Kunj": (28.53, 77.15), "Connaught Place": (28.63, 77.21),
    "India Gate":  (28.61, 77.22), "Hauz Khas":      (28.55, 77.19),
    "IG Airport":  (28.55, 77.08), "Cyber City":      (28.49, 77.08),
    "Saket":       (28.52, 77.21), "Lotus Temple":    (28.55, 77.25),
    "Dwarka":      (28.58, 77.06), "Rohini":          (28.71, 77.11),
    "New Delhi Stn":(28.64,77.22), "Akshardham":     (28.61, 77.27)
}

@st.cache_resource
def build_graph():
    G = nx.Graph()
    for n, p in LOCS.items(): G.add_node(n, pos=p)
    random.seed(42)
    for src in LOCS:
        nbrs = sorted([(math.dist(LOCS[src], LOCS[d]), d) for d in LOCS if d != src])
        for _, dst in nbrs[:4]:
            dist = round(math.dist(LOCS[src], LOCS[dst]) * 111, 2)
            G.add_edge(src, dst, dist=dist)
    return G

G = build_graph()

# ─────────────────────────────
# SESSION STATE
# ─────────────────────────────
if 'logged' not in st.session_state: st.session_state.logged = False
if 'mode'   not in st.session_state: st.session_state.mode   = 'login'

# ─────────────────────────────
# AUTH PAGE
# ─────────────────────────────
def render_auth():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Spectral:ital,wght@0,400;0,600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: #fdfdfb !important;
        overflow: hidden !important;
        height: 100vh !important;
    }
    .main .block-container {
        padding-top: 8vh !important;
        padding-bottom: 0 !important;
        overflow: hidden !important;
        max-width: 100% !important;
    }
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    footer { display: none !important; }

    /* ── Title box ── */
    .astr-title {
        font-family: 'Cinzel', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #b8860b;
        letter-spacing: 6px;
        text-transform: uppercase;
        text-align: center;
        padding: 10px 60px;
        border: 2px solid #d4af37;
        border-radius: 12px;
        background: #fff;
        box-shadow: 0 4px 18px rgba(184,134,11,.12);
        margin-bottom: 22px;
    }

    /* ── Mode heading ── */
    .astr-mode {
        font-family: 'Cinzel', serif;
        font-size: 1.35rem;
        color: #3d2b1f;
        text-align: left;
        margin-bottom: 6px;
    }

    /* ── Input labels ── */
    .stTextInput > label,
    div[data-testid="stTextInput"] > label {
        color: #2c1810 !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }

    /* ── Input boxes ── */
    .stTextInput input {
        border: 2px solid #e0d5b3 !important;
        border-radius: 10px !important;
        background: #fff !important;
        color: #1a0f0a !important;
    }
    .stTextInput input:focus { border-color: #d4af37 !important; }

    /* ── All buttons: gold pill ── */
    div.stButton > button {
        height: 46px !important;
        background: linear-gradient(135deg, #b8860b, #d4af37) !important;
        color: #fff !important;
        border-radius: 50px !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(184,134,11,.25) !important;
        width: 100% !important;
    }

    /* ── "Link" button override ── */
    div[data-testid="stButton"].link-btn > button {
        background: transparent !important;
        color: #b8860b !important;
        box-shadow: none !important;
        text-decoration: underline !important;
        font-size: 0.88rem !important;
        height: 36px !important;
    }

    ::-webkit-scrollbar { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Spacer + centered columns ──
    _, centre, _ = st.columns([1, 1.1, 1])
    with centre:
        # Title box rendered inside the column so it always shows
        st.markdown("<div class='astr-title'>AstraRoute</div>", unsafe_allow_html=True)

        mode  = st.session_state.mode
        label = "LOGIN" if mode == 'login' else "SIGN UP"
        st.markdown(f"<div class='astr-mode'>{label}</div>", unsafe_allow_html=True)

        u = st.text_input("USERNAME", placeholder="Enter your identity", key="auth_u")
        p = st.text_input("PASSWORD", type='password', placeholder="Enter your key", key="auth_p")

        st.write("")
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button(label, key="auth_submit", use_container_width=True):
                if mode == 'login':
                    if login_user(u, p):
                        print(f"\n[LOGIN SUCCESS] User '{u}' authenticated at {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        db_audit()
                        st.session_state.logged = True
                        st.session_state.user   = u
                        st.rerun()
                    else:
                        print(f"[LOGIN FAILED]  Attempt with username='{u}' — wrong credentials.")
                        st.error("Access refused — incorrect credentials.")
                else:
                    if add_user(u, p):
                        print(f"\n[SIGNUP SUCCESS] New user '{u}' registered at {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        db_audit()
                        st.success("Account created! Please log in.")
                        st.session_state.mode = 'login'
                        st.rerun()
                    else:
                        print(f"[SIGNUP FAILED]  Username '{u}' already exists.")
                        st.error("Username already taken.")

        st.write("")
        link_text = "Don't have an account? Sign Up" if mode == 'login' else "Already registered? Login"
        _, lnk_col, _ = st.columns([0.3, 3, 0.3])
        with lnk_col:
            if st.button(link_text, key="auth_switch", use_container_width=True):
                st.session_state.mode = 'signup' if mode == 'login' else 'login'
                st.rerun()


# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
def render_dash():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Spectral:wght@400;600&display=swap');
    [data-testid="stAppViewContainer"] { background:#fdfdfb !important; overflow:hidden; height:100vh; }
    [data-testid="stHeader"] { visibility:hidden; }
    .block-container { padding:1.2rem 2rem !important; overflow:hidden; height:100vh; }
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0d1117 0%, #1a1f2e 60%, #0d1117 100%) !important;
        border-right: 2.5px solid #d4af37 !important;
        box-shadow: 4px 0 20px rgba(0,0,0,0.4);
    }
    /* Sidebar text overrides for dark bg */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stCaption { color: #c8b87a !important; }
    [data-testid="stSidebar"] hr { border-color: #2e3650 !important; }
    .dash-title { font-family:'Cinzel',serif; font-size:1.9rem; color:#b8860b; text-align:center; margin-top:-30px; margin-bottom:12px; font-weight:700; letter-spacing:2px; }
    .metric-card { background:#fff; border:1px solid #e0d5b3; border-radius:10px; padding:10px 14px; margin-bottom:10px; }
    .metric-title { font-family:'Cinzel',serif; font-size:0.9rem; color:#5d4037; border-bottom:1px solid #d4af37; padding-bottom:3px; margin-bottom:8px; }
    .stSelectbox label { color:#d4af37 !important; font-family:'Cinzel',serif !important; font-weight:700 !important; font-size:0.82rem !important; }
    div.stButton > button { width:100% !important; font-family:'Cinzel',serif !important; font-weight:700 !important; border-radius:50px !important; }
    .sb-summon > div.stButton > button { background:linear-gradient(135deg,#b8860b,#d4af37) !important; color:#fff !important; }
    .sb-terminate > div.stButton > button { background:linear-gradient(135deg,#111,#3d2b1f) !important; color:#f7f3e9 !important; border:1px solid #d4af37 !important; margin-top:8px !important; }
    ::-webkit-scrollbar { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div style='text-align:center; padding: 8px 0 4px 0;'>
                <img src='https://cdn-icons-png.flaticon.com/512/2972/2972185.png'
                     width='48' style='margin-bottom:6px;'/><br>
                <span style='font-family:Cinzel,serif; font-size:1.6rem;
                             font-weight:700; color:#d4af37;
                             letter-spacing:3px;'>AstraRoute</span>
            </div>
        """, unsafe_allow_html=True)
        st.caption(f"🛡️ Operator: **{st.session_state.user.upper()}**")
        st.divider()

        ori = st.selectbox("Pickup Location",   list(LOCS.keys()), index=4)
        dst = st.selectbox("Destination (Goal)",list(LOCS.keys()), index=1)

        st.markdown("<div class='sb-summon'>", unsafe_allow_html=True)
        if st.button("🚀 SUMMON CAR", use_container_width=True):
            pq = [(0, [ori])]; visited = {}
            while pq:
                cost, path = heapq.heappop(pq)
                curr = path[-1]
                if curr == dst:
                    st.session_state.route = {
                        'path': path,
                        'dist': sum(G[path[i]][path[i+1]]['dist'] for i in range(len(path)-1))
                    }
                    break
                if curr in visited: continue
                visited[curr] = cost
                for nb in G.neighbors(curr):
                    new_g = cost + G[curr][nb]['dist']
                    h     = math.dist(LOCS[nb], LOCS[dst]) * 111
                    heapq.heappush(pq, (new_g + h, path + [nb]))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sb-terminate'>", unsafe_allow_html=True)
        if st.button("🚪 TERMINATE SESSION", use_container_width=True):
            st.session_state.logged = False; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h1 class='dash-title'>A* CAB CONCIERGE | TRAFFIC ADAPTIVE</h1>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.8])
    with col_l:
        route = st.session_state.get('route')
        info  = f"🛣️ Distance: {route['dist']:.2f} km" if route else "Analysis standby…"
        st.markdown(f"<div class='metric-card'><div class='metric-title'>🚦 Intelligence Metrics</div>{info}</div>", unsafe_allow_html=True)

        st.markdown("<div class='metric-card'><div class='metric-title'>🧠 Algorithm Trace</div></div>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(5, 3.4), facecolor='#fdfdfb')
        pos = nx.get_node_attributes(G, 'pos')
        nx.draw(G, pos=pos, edge_color='#f1e7c0', node_size=18, node_color='#ddd', ax=ax)
        if route:
            p = route['path']
            nx.draw_networkx_nodes(G, pos=pos, nodelist=p, node_size=60, node_color='#b8860b', ax=ax)
            nx.draw_networkx_edges(G, pos=pos,
                edgelist=[(p[i], p[i+1]) for i in range(len(p)-1)],
                edge_color='#3498db', width=3, ax=ax)
        plt.axis('off')
        st.pyplot(fig)

    with col_r:
        st.markdown("<div class='metric-card'><div class='metric-title'>🗺️ Traffic-Flow Geospatial Map</div></div>", unsafe_allow_html=True)
        m = folium.Map(location=[28.6, 77.2], zoom_start=12, tiles='CartoDB voyager')
        if route:
            folium.PolyLine([LOCS[n] for n in route['path']], color="#3498db", weight=6).add_to(m)
            folium.Marker(LOCS[route['path'][0]],  icon=folium.Icon(color='blue')).add_to(m)
            folium.Marker(LOCS[route['path'][-1]], icon=folium.Icon(color='red')).add_to(m)
        st_folium(m, width="100%", height=450, key="final_map")

# ─────────────────────────────
# ENTRY POINT
# ─────────────────────────────
if st.session_state.logged:
    render_dash()
else:
    render_auth()