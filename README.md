# BijliBuddy — AI-Powered Hyperlocal Electrician Marketplace

**BijliBuddy** connects Delhi households with independent local electricians through AI-powered issue classification, immediate electrical hazard warnings, transparent INR baseline price estimation, explainable hyperlocal matching, and reliability scoring.

> **Transparency Notice:** All starter ML training datasets (`synthetic_issue_dataset.csv`, `synthetic_pricing_dataset.csv`), demonstration accounts (`*.demo`), and sandbox payment records (`is_sandbox=true`) are explicitly labeled **synthetic demonstration data** and do not represent real-world customer logs or live payment transactions.

---

## Architecture Overview

```text
┌──────────────────────────────┐        HTTPS / JSON + JWT        ┌────────────────────────────────────┐
│  React + Vite + Tailwind     │ ───────────────────────────────▶ │  FastAPI Backend (backend/app)     │
│  • Leaflet + OpenStreetMap   │                                  │  • JWT + bcrypt Auth & RBAC        │
│  • Recharts Dashboards       │ ◀─────────────────────────────── │  • 11-Table SQLAlchemy ORM         │
│  • Polling & Notifications   │                                  │  • 5 Python AI/ML Modules          │
└──────────────────────────────┘                                  └─────────────────┬──────────────────┘
                                                                                    │
                                                                    ┌───────────────▼──────────────────┐
                                                                    │  PostgreSQL (Supabase) / SQLite  │
                                                                    └──────────────────────────────────┘
```

### Core AI/ML Modules (`backend/app/ml/`)
1. **Electrical Issue Classification (`issue_classifier.py`)**:
   - `TfidfVectorizer` (1–2 n-grams) + `LogisticRegression` classifying free-text issues into 8 categories (`Wiring`, `Switchboard`, `Fan installation/repair`, `Lighting`, `MCB/circuit breaker`, `Inverter`, `Electrical appliance connection`, `General electrical maintenance`).
   - Evaluated on a template-grouped held-out split (zero template leakage across train/test) and paired with non-diagnostic hazard keyword detection (`backend/app/services/safety.py`).
2. **Intelligent Electrician Matching Engine (`matching_engine.py`)**:
   - Exact **Haversine** great-circle distance (`km`), urgency-aware ETA, configurable normalized weights across distance, skill fit, rating, acceptance rate, completion rate, and ETA.
   - **Hard Availability Guarantee**: Unavailable electricians never rank above available candidates. Returns top 5 with human-readable explanations.
3. **ML Price Estimation (`price_estimator.py`)**:
   - `RandomForestRegressor` (140 trees + `OneHotEncoder`) trained on synthetic Delhi INR baseline data using category, repair complexity, Delhi zone, urgency, time slot, and duration.
   - Outputs `lower_estimate_inr`, `predicted_base_price_inr`, and `upper_estimate_inr`, clearly distinguished from the electrician's final quotation and excluding spare parts.
4. **Demand Analytics & Statistical Forecasting (`demand_analytics.py`)**:
   - Aggregates bookings by Delhi locality, weekday, time slot, and category.
   - Baseline statistical forecast combining recency-weighted moving averages, Laplace-smoothed day-of-week seasonal indices, and 90% Poisson prediction bounds, with explicit small-dataset limitations documented.
5. **Explainable Electrician Reliability Score (`reliability.py`)**:
   - Combines verified completed jobs, acceptance rate, completion discipline, customer ratings, on-time rate, and Admin credential verification using **Bayesian prior smoothing** so newcomer electricians are scored fairly without cold-start penalties.

### Safety & Trust Guardrails
- **Admin-Only Verification**: Newly registered electricians start as `pending` or `unverified` and only display `Admin Verified` after explicit Admin approval.
- **Hazard Detection & Emergency Instructions**: Reports mentioning sparks, exposed wires, burning smells, smoke, or shocks display critical alerts instructing users to stay clear, avoid DIY repairs on live circuits, and contact National Emergency (`112`), Fire (`101`), or Delhi DISCOM helplines (BSES Rajdhani `19123`, BSES Yamuna `19122`, Tata Power DDL `19124`).
- **Non-Diagnostic Photo Uploads**: Uploaded images are strictly for electrician visual reference — AI never claims to diagnose live electrical hazards from photos.

---

## Database Schema (11 Tables)
Defined in `backend/app/db/models.py` (compatible with both PostgreSQL/Supabase and SQLite):
- `users`, `customer_profiles`, `electrician_profiles`, `service_categories`, `electrician_skills`, `availability`, `service_requests`, `bookings`, `reviews`, `payments` (sandbox/demo only), `notifications`.

---

## Local Setup & Run Instructions

### 1. Backend (FastAPI + ML)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

# Train & evaluate ML models (optional: also auto-trains if artifacts missing)
python scripts/train_models.py

# Initialize & seed SQLite database (22 electricians, 8 categories, 68 bookings)
python scripts/init_db.py

# Start API server (Swagger docs at http://127.0.0.1:8000/docs)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (React + Vite + Tailwind)
```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```
Open **http://localhost:5173** in your browser.

### 3. Run Automated Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
Tests verify:
- TF-IDF + LogisticRegression issue classification & hazard warnings (`test_classification.py`)
- Haversine distance & strict availability ranking (`test_matching.py`)
- Random Forest price range scaling & disclaimers (`test_pricing.py`)
- Bayesian fairness for new electricians & demand forecasting (`test_reliability_and_demand.py`)
- Full 13-step end-to-end marketplace workflow + RBAC + Indian phone validation (`test_api_e2e.py`)

---

## Synthetic Demo Accounts
Password for all demonstration accounts: `Demo@1234`
- **Customer (Saket):** `ananya.sharma@bijlibuddy.demo`
- **Electrician (Saket, Verified):** `ramesh.verma@bijlibuddy.demo`
- **Admin:** `admin@bijlibuddy.demo`

*(One-click demo buttons are built into the Landing and Sign-In pages.)*

---

## Free-Tier Deployment Guide (Supabase + Render + Vercel)

### Step 1: Database on Supabase (Free Tier)
1. Create a new project in [Supabase](https://supabase.com).
2. Copy the PostgreSQL connection string (**Session Pooler** or direct URI) and format it as:
   `postgresql+psycopg://postgres.<PROJECT_REF>:<PASSWORD>@aws-0-<REGION>.pooler.supabase.com:5432/postgres?sslmode=require`

### Step 2: Backend on Render (Free Tier)
1. Push repository to GitHub.
2. Create a new **Web Service** on [Render](https://render.com) (or import `render.yaml` Blueprint):
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt && python scripts/train_models.py`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set Environment Variables:
   - `ENVIRONMENT=production`
   - `DATABASE_URL=<Your Supabase PostgreSQL URI>`
   - `JWT_SECRET_KEY=<Strong Random Secret>`
   - `CORS_ORIGINS=https://<your-vercel-app>.vercel.app`
   - `AUTO_SEED_ON_EMPTY=true`

### Step 3: Frontend on Vercel (Free Tier)
1. Import the repo into [Vercel](https://vercel.com) with **Root Directory** set to `frontend`.
2. Add Environment Variable:
   - `VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api`
3. Deploy (`frontend/vercel.json` handles client-side React Router rewrites).
