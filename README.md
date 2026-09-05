# ROIlytics — Influencer ROI Predictor

> Predict which influencers will deliver the highest return on investment using
> **real Instagram data** (Business Discovery API) merged with **campaign
> spend & conversion data** (Kaggle).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![XGBoost](https://img.shields.io/badge/XGBoost-Gradient%20Boosting-green)

---

## Architecture

```
┌──────────────────┐     ┌─────────────────────┐
│  Instagram API   │     │  Kaggle Dataset      │
│  (Business       │     │  (Campaign spend,    │
│   Discovery)     │     │   conversions, ROI)  │
└────────┬─────────┘     └──────────┬──────────┘
         │                          │
         ▼                          ▼
┌──────────────────┐     ┌─────────────────────┐
│ instagram_       │     │ kaggle_campaign_     │
│ profiles_raw.csv │     │ data.csv             │
└────────┬─────────┘     └──────────┬──────────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
         ┌─────────────────────┐
         │ Feature Engineering │
         │ (bucket-based merge │
         │  + derived features)│
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │  Model Training     │
         │  LR │ RF │ XGBoost  │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │  Streamlit Dashboard│
         │  (prediction + viz) │
         └─────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- An Instagram **Business or Creator** account linked to a Facebook Page
  (required only for live data collection — the pipeline can run with
  synthetic data for development/demo)
- A free [Kaggle](https://www.kaggle.com/) account (for downloading the
  campaign dataset)

### 1. Setup

```bash
# Clone the repo and create a virtual environment
git clone <repo-url> ROIlytics && cd ROIlytics
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
copy .env.example .env
# Edit .env with your Instagram API credentials:
#   IG_ACCESS_TOKEN=your_long_lived_token
#   IG_USER_ID=your_business_account_id
```

> **How to get these credentials:**
> 1. Create a [Meta Developer](https://developers.facebook.com/) account
> 2. Create a new App → type "Business"
> 3. Add the **Instagram Graph API** product
> 4. Convert your Instagram account to Business/Creator (Instagram app →
>    Settings → Account type), link it to a Facebook Page
> 5. Generate a long-lived User Access Token with scopes:
>    `instagram_basic`, `pages_show_list`, `instagram_manage_insights`
>    (Graph API Explorer works fine for class projects)
> 6. Note your linked IG Business Account ID and the access token

### 3. Collect Instagram data (optional — requires API credentials)

```bash
python src/instagram_collector.py --usernames usernames.txt --out data/instagram_profiles_raw.csv
```

Edit `usernames.txt` to list the Instagram Business/Creator usernames you want
to analyze (one per line, no `@` prefix).

### 4. Download Kaggle campaign data

Download one of these datasets and place the CSV at `data/kaggle_campaign_data.csv`:

| Dataset | Best for | Link |
|---|---|---|
| **Multi-Brand Marketing Campaign Performance** | Explicit spend/revenue/ROI columns | [Kaggle](https://www.kaggle.com/datasets/shriyaasrivastav/multi-brand-marketing-campaign-performance) |
| Influencer Marketing ROI Dataset | Influencer-specific niches | [Kaggle](https://www.kaggle.com/datasets/tfisthis/influencer-marketing-roi-dataset) |
| Marketing Campaign Performance & ROI | Large-scale (200K+ rows) | [Kaggle](https://www.kaggle.com/datasets/noorulain1/marketing-campaign-performance-roi-dataset) |

The feature engineering script auto-detects which dataset variant you're using.

### 5. Build features and train

```bash
# Feature engineering (merges Instagram + Kaggle data)
python src/feature_engineering.py

# Train and compare models
python src/train_model.py
```

> **No API credentials or Kaggle data?** No problem — if the input files are
> missing, synthetic demo data is generated automatically so you can run the
> full pipeline end-to-end.

### 6. Launch the Application

You can launch either the modern full-stack web application or the Streamlit dashboard:

#### Option A: Full-Stack Web App (FastAPI + React / Vite)

```bash
# Terminal 1: Backend API
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

#### Option B: Streamlit Dashboard

```bash
streamlit run app.py
```


---

## Project Structure

```
ROIlytics/
├── .env.example              # API credential template
├── .gitignore
├── requirements.txt          # Python dependencies
├── usernames.txt             # Instagram usernames to collect
├── README.md
├── app.py                    # Streamlit dashboard
├── data/
│   ├── instagram_profiles_raw.csv   # (generated by collector)
│   ├── kaggle_campaign_data.csv     # (manual download)
│   ├── features_merged.csv          # (generated by feature engineering)
│   └── demo_synthetic.csv           # (auto-generated fallback)
├── src/
│   ├── __init__.py
│   ├── instagram_collector.py       # Instagram Business Discovery API
│   ├── feature_engineering.py       # Merge + feature engineering
│   └── train_model.py              # Model training & comparison
└── models/
    ├── best_model.pkl               # (generated by training)
    ├── model_comparison.png         # (generated by training)
    └── feature_importance.png       # (generated by training)
```

---

## How the Merge Works

Exact 1:1 username matching between Instagram data and a Kaggle campaign
dataset is not realistic — these are two independent data sources. Instead, we
use **bucket-based matching**:

1. Each Instagram profile is assigned a **follower bucket** (Nano < 10K,
   Micro 10K–100K, Macro 100K–1M, Mega > 1M) and a **category** (inferred
   from bio keywords: Fitness, Fashion, Tech, Food, Travel, Lifestyle).
2. The Kaggle campaign data is aggregated by the same (bucket, category)
   dimensions.
3. Each Instagram profile receives the average spend/revenue/ROI from Kaggle
   campaigns in the matching bucket + category.

This transfers the historically observed relationship between influencer size,
niche, and ROI onto freshly collected real profiles — a standard approach in
influencer marketing analytics.

---

## Models

| Model | Purpose |
|---|---|
| **Linear Regression** | Baseline — interpretable coefficients |
| **Random Forest** | Non-linear relationships, feature importance |
| **XGBoost** | State-of-the-art gradient boosting, best accuracy |

All three are compared on R², MAE, and RMSE. The best model (by R²) is saved
and used in the Streamlit dashboard.

---

## Dashboard Features

| Tab | What it shows |
|---|---|
| 📈 Prediction | Enter influencer stats → predicted ROI, revenue, profit |
| 🏆 Model Comparison | Side-by-side R²/MAE/RMSE across all three models |
| 🔍 Feature Importance | Which features matter most for ROI prediction |
| 📊 Data Explorer | Browse training data, scatter plots, distributions |
| ℹ️ About | Methodology, limitations, data sources |

---

## Honest Limitations

> These make your project look **more credible**, not less — include them in
> your report/demo.

1. **Instagram data is real and live; spend/ROI is from a separate dataset.**
   The Kaggle campaign data is not causally linked to the specific influencers
   you queried. The merge is by follower-bucket + category, not by username.

2. **Reach and impressions for other people's posts are not obtainable** via
   any external API. Engagement rate (likes + comments / followers) is the
   closest legitimate public proxy — and it's the industry-standard metric
   used by real influencer marketing platforms.

3. **The model learns the historical relationship** between (followers,
   engagement, niche) → ROI from the Kaggle data, then applies it to your
   freshly collected real profiles. This is a standard transfer-learning
   approach — just be transparent about it.

---

## Tech Stack

| Component | Technology |
|---|---|
| Data Collection | Instagram Graph API (Business Discovery) |
| Data Processing | pandas, NumPy |
| Machine Learning | scikit-learn, XGBoost |
| Visualization | Matplotlib, Seaborn |
| Dashboard | Streamlit |
| Configuration | python-dotenv |

---

## License

This project is for educational purposes. The Instagram Graph API is subject
to [Meta's Platform Terms](https://developers.facebook.com/terms/). The Kaggle
dataset is subject to its own license on Kaggle.
