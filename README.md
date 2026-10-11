# ROIlytics
 
A full-stack web application for predicting influencer campaign ROI using a Scraped Indian Influencer Dataset and Machine Learning.

## Features

- **Curated Indian Influencer Dataset**: Over 190 verified and high-quality Indian creators across 10 categories (Fitness, Fashion, Tech, Food, Travel, Lifestyle, Beauty, Gaming, Finance, Education) with engagement metrics.
- **Brand Account Exclusion**: Brand accounts (e.g. Nike, Adidas, Zomato, Myntra, Mysmartprice, 91mobiles, Digit.in, Houseofmisu) are flagged (`is_brand=1`) and automatically excluded from creator rankings, top discovery, and analytics.
- **Dynamic ROI Prediction**: Predict Estimated ROI and Revenue on-the-fly for any creator or custom campaign budget using a trained Scikit-learn RandomForest model.
- **Public Web Lookup**: Fetch data for public Instagram profiles using Playwright with rate-limiting, circuit breakers, and manual snapshot fallback.
- **Fit Scoring & Campaign Matching**: Dynamic influencer scoring combining Engagement Rate vs. category benchmarks, follower tier fit, and predicted ROI.
- **Analytics Dashboard**: Real-time category distributions, benchmark averages, and model performance metrics.
- **Self-Healing SQLite Database**: If `data/influencers.db` is missing or empty, the backend automatically initializes and seeds it from `data/influencers_clean.csv` upon startup.

> **Note on ROI**: Social platforms provide no financial spend or revenue data. Spend and category are campaign inputs, and ROI is an **ML model estimate** based on historical performance patterns.

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind-free vanilla CSS, Recharts, Lucide React
- **Backend**: FastAPI, Pydantic, SQLite, Scikit-learn, Pandas, Joblib
- **Public Lookup**: Playwright Chromium (optional reader plugin architecture)

## Setup Instructions

### 1. Backend Setup

```bash
cd backend
python -m venv .venv312
.venv312\Scripts\activate  # On Linux/macOS: source .venv312/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` in the project root if customized configurations are required:

```env
# Optional MySQL configurations (falls back to SQLite automatically)
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=
# MYSQL_DATABASE=roilytics_db
```

Run the API:
```bash
python -m uvicorn backend.app.main:app --port 8000
```
On startup, `data/influencers.db` will be verified or automatically built from `data/influencers_clean.csv`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Testing

Backend unit and pipeline tests are written with `pytest`:

```bash
python -m pytest backend/tests -o pythonpath=backend
```

Build the frontend bundle:

```bash
cd frontend
npm run build
```

## Data Quality & Integrity

- **Quality Filters**: Influencers must have at least 3 usable post records and non-zero follower counts.
- **Engagement Rate Capping**: Unrealistic engagement rates (>50%) are capped to protect downstream ML features.
- **Brand Exclusions**: Brand/corporate handles are preserved in the database for auditing but excluded by default from influencer discovery (`/api/discover`), category rankings, and analytics.

