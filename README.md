# 🚕 Taxifare

> Configure your ride · Instant fare estimate · No surprises.

A premium Streamlit web app that predicts New York taxi fares in real time. Type your pickup and dropoff addresses, select a date/time and passenger count, and get an instant fare estimate from a deployed ML API — with a real GPS driving route rendered on a dark map.

---

## Repository structure

```
taxifare-website/
├── app.py                  # Streamlit application (single file)
├── requirements.txt        # Python dependencies for Streamlit Cloud
├── Makefile                # Dev shortcuts
├── .python-version         # Python version pin (pyenv)
├── .gitignore
└── README.md
```

> No `src/`, no extra folders needed. Streamlit Cloud reads `app.py` + `requirements.txt` at the root.

---

## Local setup

### 1. Clone and enter the repo

```bash
git clone https://github.com/glenhellio-commits/taxifare-website.git
cd taxifare-website
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If `folium` or `streamlit-folium` fails:

```bash
pip install folium --upgrade
pip install streamlit-folium --upgrade
```

> Common cause of folium import errors: conflicting package versions from a previous `pip install` without a clean venv. Always install inside a fresh `.venv`.

### 4. Run locally

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Deploy to Streamlit Cloud

1. Push your repo to GitHub (already done — `taxifare-website` is public)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Fill in:
   - **Repository**: `glenhellio-commits/taxifare-website`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **Deploy** — done.

Streamlit Cloud reads `requirements.txt` automatically and installs all dependencies.

> No `Procfile`, no `setup.py`, no Docker needed.

---

## Configuration

The prediction API URL is set at the top of `app.py`:

```python
API_URL = "https://taxifare.lewagon.ai/predict"
```

To use a different API, update that variable before deploying.

If you need to store secrets (e.g. an API key), use Streamlit secrets:

```toml
# .streamlit/secrets.toml  ← never commit this file
API_KEY = "your-key-here"
```

Access in code via `st.secrets["API_KEY"]`. The `.gitignore` already excludes `secrets.toml`.

---

## API contract

`GET /predict` with query params:

| Parameter | Format | Example |
|---|---|---|
| `pickup_datetime` | `%Y-%m-%d %H:%M:%S` | `2026-03-10 14:30:00` |
| `pickup_latitude` | float | `40.6413` |
| `pickup_longitude` | float | `-73.7781` |
| `dropoff_latitude` | float | `40.7580` |
| `dropoff_longitude` | float | `-73.9855` |
| `passenger_count` | int (1–8) | `2` |

Expected response:

```json
{ "fare": 28.50 }
```

---

## Stack

| Layer | Tool |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Map | [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://folium.streamlit.app/) |
| Geocoding | [geopy](https://geopy.readthedocs.io/) / Nominatim (free, no key) |
| Routing | [OSRM public API](http://router.project-osrm.org) (free, no key) |
| Prediction | Custom ML API (GET `/predict`) |

---

## Known limitations

- **Nominatim rate limit** — 1 req/sec. Results are cached 1h via `@st.cache_data`.
- **OSRM availability** — public instance can be slow. App falls back to a dashed straight line automatically.
- **Date widget theming** — Streamlit's native date picker cannot be fully recolored; red accent is applied to surrounding elements only via CSS.

