"""
Taxifare — Premium Streamlit prediction app v2
Real GPS routing via OSRM (public, free, no key needed).
Geocoding via geopy / Nominatim.
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_URL   = "https://taxifare.lewagon.ai/predict"   # ← your prediction API
OSRM_URL  = "http://router.project-osrm.org/route/v1/driving"  # free public OSRM

st.set_page_config(
    page_title="Taxifare",
    page_icon="🚕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #000000;
    color: #ece8df;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2.4rem; max-width: 760px; }

.logo-wrap {
    display: flex; align-items: center; gap: 16px; margin-bottom: 2px;
}
.logo-badge {
    background: #FF3E2B; border-radius: 12px;
    width: 52px; height: 52px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 0 24px rgba(255,62,43,0.5);
}
.logo-text {
    font-family: 'Syne', sans-serif;
    font-size: 2.5rem; font-weight: 800;
    letter-spacing: -0.03em; color: #fff;
}
.logo-text em { color: #FF3E2B; font-style: normal; }
.subtitle {
    color: #666; font-size: 0.95rem;
    margin: 2px 0 2rem 0; letter-spacing: 0.01em;
}
.slabel {
    font-family: 'Syne', sans-serif;
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #FF3E2B; margin-bottom: 8px;
}
hr.div { border: none; border-top: 1px solid #1a1a1a; margin: 1.8rem 0; }

.stTextInput input, .stNumberInput input {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 8px !important;
    color: #ece8df !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus {
    border-color: #FF3E2B !important;
    box-shadow: 0 0 0 2px rgba(255,62,43,0.12) !important;
}
.stSelectbox > div > div {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 8px !important;
    color: #ece8df !important;
}

/* Rainbow glow link button */
@keyframes rainbow-glow {
    0%   { box-shadow: 0 0 14px rgba(255,62,43,0.7); }
    25%  { box-shadow: 0 0 14px rgba(255,210,0,0.7); }
    50%  { box-shadow: 0 0 14px rgba(0,200,255,0.7); }
    75%  { box-shadow: 0 0 14px rgba(140,80,255,0.7); }
    100% { box-shadow: 0 0 14px rgba(255,62,43,0.7); }
}
.rainbow-link {
    display: inline-flex; align-items: center; gap: 8px;
    background: #0d0d0d; color: #ece8df !important;
    border: 1.5px solid #444; border-radius: 10px;
    padding: 9px 18px; font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem; text-decoration: none !important;
    margin-top: 10px; cursor: pointer;
    animation: rainbow-glow 3s linear infinite;
}

/* Predict button — green fire */
.predict-btn > div > button {
    background: linear-gradient(135deg, #009c3b, #00cc50) !important;
    color: #fff !important; border: none !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    letter-spacing: 0.05em !important; width: 100% !important;
    padding: 0.8rem 2rem !important;
    animation: green-fire 2s ease-in-out infinite !important;
    cursor: pointer !important;
}
@keyframes green-fire {
    0%,100% { box-shadow: 0 0 20px rgba(0,204,80,0.5), 0 0 50px rgba(0,204,80,0.15); }
    50%      { box-shadow: 0 0 34px rgba(0,204,80,0.85), 0 0 70px rgba(0,204,80,0.3); }
}

.result-card {
    background: linear-gradient(135deg, #0a160a, #0d1a0e);
    border: 1px solid #1a3020; border-radius: 16px;
    padding: 2rem 2.2rem; margin-top: 1.6rem;
}
.fare-big {
    font-family: 'Syne', sans-serif;
    font-size: 3.6rem; font-weight: 800;
    color: #00e05a; letter-spacing: -0.04em; line-height: 1;
    text-shadow: 0 0 32px rgba(0,224,90,0.45);
}
.fare-sub {
    font-size: 0.75rem; color: #3a7a4a;
    letter-spacing: 0.12em; text-transform: uppercase;
    font-weight: 600; margin: 4px 0 1.6rem;
}
.trip-box {
    background: #090e09; border-radius: 10px;
    padding: 1rem 1.2rem; font-size: 0.84rem;
    color: #7a9a7a; line-height: 2.1;
}
.trip-box b { color: #b8d8b8; font-weight: 500; }
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def geocode(address: str):
    """Return (lat, lon) or None via Nominatim."""
    try:
        geo = Nominatim(user_agent="taxifare_premium_v2", timeout=7)
        loc = geo.geocode(address)
        return (loc.latitude, loc.longitude) if loc else None
    except GeocoderTimedOut:
        return None


@st.cache_data(show_spinner=False, ttl=1800)
def get_osrm_route(plat, plon, dlat, dlon):
    """
    Real driving route from OSRM public API.
    Returns list of (lat, lon) or None on failure.
    OSRM expects lon,lat in URL path.
    """
    url = f"{OSRM_URL}/{plon},{plat};{dlon},{dlat}"
    try:
        r = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=8)
        r.raise_for_status()
        coords = r.json()["routes"][0]["geometry"]["coordinates"]
        return [(c[1], c[0]) for c in coords]  # flip to (lat, lon) for folium
    except Exception:
        return None  # caller will fall back to straight line


def build_map(pickup_coords=None, dropoff_coords=None, route=None):
    center = pickup_coords or dropoff_coords or (40.7128, -74.0060)
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB dark_matter")
    if pickup_coords:
        folium.Marker(pickup_coords, tooltip="📍 Pickup",
                      icon=folium.Icon(color="red", icon="circle", prefix="fa")).add_to(m)
    if dropoff_coords:
        folium.Marker(dropoff_coords, tooltip="🏁 Dropoff",
                      icon=folium.Icon(color="green", icon="flag", prefix="fa")).add_to(m)
    if route:
        folium.PolyLine(route, color="#FF3E2B", weight=3, opacity=0.85).add_to(m)
    elif pickup_coords and dropoff_coords:
        # Straight-line fallback if OSRM unavailable
        folium.PolyLine([pickup_coords, dropoff_coords],
                        color="#FF3E2B", weight=2, opacity=0.4, dash_array="6 4").add_to(m)
    if pickup_coords and dropoff_coords:
        m.fit_bounds([pickup_coords, dropoff_coords], padding=(40, 40))
    return m


def call_predict_api(ride_dt, plat, plon, dlat, dlon, pax):
    params = {
        "pickup_datetime":  ride_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_latitude":  plat,  "pickup_longitude": plon,
        "dropoff_latitude": dlat,  "dropoff_longitude": dlon,
        "passenger_count":  pax,
    }
    r = requests.get(API_URL, params=params, timeout=12)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "pickup_coords": None, "dropoff_coords": None,
    "pickup_addr": "",     "dropoff_addr": "",
    "route": None,         "prediction": None,
    "hour": datetime.now().hour, "minute": datetime.now().minute,
}.items():
    st.session_state.setdefault(k, v)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="logo-wrap">
  <div class="logo-badge">🚕</div>
  <div class="logo-text">Taxi<em>fare</em></div>
</div>
<p class="subtitle">Configure your ride &nbsp;·&nbsp; Instant fare estimate &nbsp;·&nbsp; No surprises.</p>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATE & TIME
# ─────────────────────────────────────────────
st.markdown('<p class="slabel">When are you riding?</p>', unsafe_allow_html=True)

col_d, col_h, col_m = st.columns([3, 1, 1])
with col_d:
    ride_date = st.date_input("Date", value=datetime.now().date(),
                               min_value=datetime.now().date(),
                               label_visibility="collapsed")
with col_h:
    hour = st.number_input("HH", 0, 23, st.session_state["hour"], step=1, format="%02d", label_visibility="collapsed")
with col_m:
    minute = st.number_input("MM", 0, 59, st.session_state["minute"], step=1, format="%02d", label_visibility="collapsed")

ride_dt = datetime.combine(ride_date, datetime.min.time()).replace(hour=int(hour), minute=int(minute))
dt_valid = ride_dt >= datetime.now()
if not dt_valid:
    st.warning("⏰ This datetime is in the past — please pick a future ride time.")

# "Travel to the future" — styled anchor button → lewagon.com
st.markdown(
    '<a class="rainbow-link" href="https://www.lewagon.com/" target="_blank">🔮 Travel to the future</a>',
    unsafe_allow_html=True,
)

st.markdown('<hr class="div">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOCATIONS
# ─────────────────────────────────────────────
st.markdown('<p class="slabel">Where are you going?</p>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    pickup_input = st.text_input("📍 Pickup", value=st.session_state["pickup_addr"],
                                  placeholder="e.g. La maison de Louis")
with col_b:
    dropoff_input = st.text_input("🏁 Dropoff", value=st.session_state["dropoff_addr"],
                                   placeholder="e.g. Le restaurant coreen de Pauline")

# Geocode on address change
if pickup_input != st.session_state["pickup_addr"]:
    st.session_state.update({"pickup_addr": pickup_input, "route": None})
    if pickup_input.strip():
        with st.spinner("Locating pickup…"):
            st.session_state["pickup_coords"] = geocode(pickup_input)
        if not st.session_state["pickup_coords"]:
            st.error("Pickup not found — try a more specific address.")
    else:
        st.session_state["pickup_coords"] = None

if dropoff_input != st.session_state["dropoff_addr"]:
    st.session_state.update({"dropoff_addr": dropoff_input, "route": None})
    if dropoff_input.strip():
        with st.spinner("Locating dropoff…"):
            st.session_state["dropoff_coords"] = geocode(dropoff_input)
        if not st.session_state["dropoff_coords"]:
            st.error("Dropoff not found — try a more specific address.")
    else:
        st.session_state["dropoff_coords"] = None

pc = st.session_state["pickup_coords"]
dc = st.session_state["dropoff_coords"]

# Fetch OSRM route when both coords available and not already fetched
if pc and dc and st.session_state["route"] is None:
    with st.spinner("Fetching driving route…"):
        route = get_osrm_route(pc[0], pc[1], dc[0], dc[1])
        st.session_state["route"] = route or []  # [] triggers straight-line fallback

m = build_map(pc, dc, st.session_state["route"] or None)
st_folium(m, width=None, height=300, returned_objects=[])

st.markdown('<hr class="div">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PASSENGERS
# ─────────────────────────────────────────────
st.subheader("Passengers")
passengers = st.selectbox(
    "Passengers", options=list(range(1, 9)),
    format_func=lambda x: f"{'👤' * min(x, 4)}  {x} passenger{'s' if x > 1 else ''}",
    label_visibility="collapsed",
)

st.markdown('<hr class="div">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PREDICT
# ─────────────────────────────────────────────
st.markdown('<div class="predict-btn">', unsafe_allow_html=True)
predict = st.button("⚡  Estimate my fare", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if predict:
    errors = []
    if not dt_valid:       errors.append("Datetime is in the past.")
    if not pc:             errors.append("Pickup address is missing or unresolved.")
    if not dc:             errors.append("Dropoff address is missing or unresolved.")
    if errors:
        for e in errors: st.error(f"❌ {e}")
    else:
        with st.spinner("Calling the fare oracle…"):
            try:
                data = call_predict_api(ride_dt, pc[0], pc[1], dc[0], dc[1], passengers)
                fare = data.get("fare") or data.get("prediction")
                st.session_state["prediction"] = {
                    "fare": float(fare), "datetime": ride_dt,
                    "pickup": pickup_input, "dropoff": dropoff_input, "pax": passengers,
                }
            except requests.exceptions.ConnectionError:
                st.error("🔌 Could not reach the API. Check API_URL.")
            except requests.exceptions.HTTPError as e:
                st.error(f"API error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")


# ─────────────────────────────────────────────
# RESULT
# ─────────────────────────────────────────────
pred = st.session_state.get("prediction")
if pred:
    dt_str = pred["datetime"].strftime("%A %d %b %Y · %H:%M")
    pax = pred["pax"]
    st.markdown(f"""
    <div class="result-card">
      <div class="fare-big">${pred['fare']:.2f}</div>
      <div class="fare-sub">Estimated fare · USD</div>
      <div class="trip-box">
        <b>🗓 When</b>&nbsp;&nbsp; {dt_str}<br>
        <b>📍 From</b>&nbsp;&nbsp; {pred['pickup']}<br>
        <b>🏁 To</b>&nbsp;&nbsp;&nbsp;&nbsp; {pred['dropoff']}<br>
        <b>👥 Pax</b>&nbsp;&nbsp;&nbsp; {pax} passenger{'s' if pax > 1 else ''}
      </div>
    </div>
    """, unsafe_allow_html=True)