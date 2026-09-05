"""
Generate a realistic 10,000+ Instagram influencer dataset.
Run: .\\venv\\Scripts\\python.exe src/generate_influencer_dataset.py
"""
import pandas as pd
import numpy as np
import sqlite3
import os
import random
import string

np.random.seed(42)
random.seed(42)

N = 10500  # total records

# ── Categories & sub-niches ────────────────────────────────────────────────────
CATEGORIES = {
    "Fitness":   ["Yoga", "Weightlifting", "Running", "CrossFit", "Nutrition", "Pilates", "Cycling", "HIIT"],
    "Fashion":   ["Streetwear", "Luxury", "Sustainable Fashion", "Menswear", "Womenswear", "Vintage", "Athleisure"],
    "Tech":      ["Gadgets", "Software", "AI & ML", "Gaming Tech", "Smartphones", "Cybersecurity", "Startups"],
    "Food":      ["Vegan", "Baking", "BBQ & Grilling", "Fine Dining", "Street Food", "Healthy Eating", "Cocktails"],
    "Travel":    ["Backpacking", "Luxury Travel", "Adventure", "Solo Travel", "Family Travel", "Photography Travel"],
    "Lifestyle": ["Minimalism", "Home Decor", "Productivity", "Mental Health", "Self-Care", "Parenting"],
    "Beauty":    ["Skincare", "Makeup", "Haircare", "Nail Art", "Fragrance", "Natural Beauty"],
    "Gaming":    ["PC Gaming", "Console", "Mobile Games", "Esports", "Game Reviews", "Streaming"],
    "Finance":   ["Investing", "Crypto", "Personal Finance", "Real Estate", "Side Hustles", "Frugal Living"],
    "Education": ["Science", "History", "Languages", "Mathematics", "Coding", "Art & Design", "Philosophy"],
}

COUNTRIES = {
    "US": 30, "IN": 18, "BR": 10, "GB": 7, "DE": 5,
    "FR": 5,  "CA": 4,  "AU": 4,  "MX": 3, "ID": 3,
    "JP": 2,  "KR": 2,  "IT": 2,  "ES": 2, "NL": 1,
    "SG": 1,  "UAE": 1,
}

FIRST_NAMES = [
    "Emma","Olivia","Ava","Isabella","Sophia","Mia","Charlotte","Amelia","Harper","Evelyn",
    "Liam","Noah","Oliver","Elijah","James","William","Benjamin","Lucas","Henry","Alexander",
    "Aisha","Priya","Ananya","Divya","Neha","Riya","Pooja","Shreya","Kavya","Meera",
    "Carlos","Miguel","Luis","Diego","Mateo","Alejandro","Sebastián","Ricardo","Fernando","Andrés",
    "Yuna","Sakura","Hana","Yuki","Airi","Nana","Rin","Mei","Saki","Yui",
    "Zara","Fatima","Layla","Nour","Yasmin","Sara","Dina","Lina","Rania","Hana",
    "Jack","Tom","Sam","Jake","Ryan","Max","Alex","Jordan","Taylor","Morgan",
    "Sofia","Luna","Valentina","Camila","Martina","Paula","Lucia","Elena","Maria","Ana",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Anderson",
    "Taylor","Thomas","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris",
    "Sharma","Patel","Singh","Kumar","Gupta","Shah","Mehta","Joshi","Verma","Yadav",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Torres","Ramirez","Flores","Rivera","Cruz",
    "Tanaka","Yamamoto","Watanabe","Ito","Nakamura","Kobayashi","Sato","Suzuki","Saito","Kato",
    "Kim","Lee","Park","Choi","Jung","Kang","Cho","Yoon","Jang","Lim",
    "Chen","Wang","Zhang","Liu","Yang","Huang","Zhao","Wu","Zhou","Xu",
    "Müller","Schmidt","Schneider","Fischer","Weber","Meyer","Wagner","Becker","Schulz","Hoffmann",
]

BIO_TEMPLATES = {
    "Fitness":   [
        "💪 {sub} coach | Helping you crush your goals | DM for collabs",
        "🏋️ {sub} enthusiast | {followers_k}K community | Free workout plans 👇",
        "🔥 Certified {sub} trainer | Transformation specialist | Link in bio",
        "✨ {sub} & wellness | Science-based approach | Let's get stronger together",
    ],
    "Fashion":   [
        "👗 {sub} creator | Personal stylist | Outfit inspo daily",
        "✨ {sub} addict | Fashion weeks 🌍 | Collab: email in bio",
        "🛍️ {sub} curator | Making fashion accessible | Shop my looks 👇",
        "💫 {sub} | Style guide | Helping you dress with confidence",
    ],
    "Tech":      [
        "📱 {sub} reviewer | Honest opinions | New video every week",
        "💻 {sub} builder | Sharing what I learn | Follow for daily tips",
        "🚀 {sub} enthusiast | {followers_k}K techies | Newsletter 👇",
        "⚡ {sub} | Breaking down complex topics simply | Let's geek out",
    ],
    "Food":      [
        "🍕 {sub} creator | Recipes that actually work | New post every day",
        "👨‍🍳 {sub} chef | Home cooking made easy | Join {followers_k}K foodies",
        "🌿 {sub} advocate | Sharing delicious eats | Recipe book out now",
        "🍽️ {sub} lover | Restaurant reviews & recipes | Link in bio",
    ],
    "Travel":    [
        "✈️ {sub} traveler | {countries} countries | New destination weekly",
        "🌍 {sub} explorer | Living out of a suitcase | Travel guides 👇",
        "📸 {sub} photographer | Capturing the world | Collab: DM me",
        "🗺️ Full-time {sub} | Budget tips & hidden gems | Join {followers_k}K explorers",
    ],
    "Lifestyle": [
        "🌿 {sub} advocate | Slow living | Inspiring intentional choices",
        "✨ {sub} creator | Morning routines & life hacks | Follow for inspo",
        "💫 {sub} | {followers_k}K community | Newsletter every Sunday",
        "🏠 {sub} enthusiast | Sharing my everyday life | Link in bio",
    ],
    "Beauty":    [
        "💄 {sub} artist | Tutorials every week | Products I actually use",
        "✨ {sub} lover | Honest reviews | {followers_k}K beauty community",
        "💅 {sub} creator | From beginner to pro | DM for collaborations",
        "🌸 {sub} enthusiast | Clean beauty | Empowering your glow-up",
    ],
    "Gaming":    [
        "🎮 {sub} streamer | Live daily | Join {followers_k}K gamers",
        "⚡ {sub} player | Reviews & gameplay | New content every day",
        "🏆 {sub} competitor | Tips & tricks | Discord link in bio",
        "🎯 {sub} creator | Unfiltered gaming content | Let's play",
    ],
    "Finance":   [
        "📈 {sub} educator | Making money simple | Free guide 👇",
        "💰 {sub} coach | Helped {followers_k}K+ reach financial freedom",
        "🏦 {sub} expert | Daily tips to grow your wealth | Newsletter",
        "💡 {sub} simplified | No jargon | Your money, your future",
    ],
    "Education": [
        "📚 {sub} teacher | Learning made fun | {followers_k}K students",
        "🎓 {sub} educator | Daily facts & insights | Free resources 👇",
        "🧠 {sub} enthusiast | Curiosity-driven content | Ask me anything",
        "✏️ {sub} simplified | Complex ideas, simple words | Join the community",
    ],
}

def fake_username(first, last, idx):
    styles = [
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()}_{last.lower()}",
        f"the{first.lower()}{last.lower()[:3]}",
        f"{first.lower()}{last.lower()}{random.randint(1,99)}",
        f"{first.lower()}_{random.choice(['official','real','tv','world','gram'])}",
        f"{first.lower()}{random.randint(100,999)}",
    ]
    return random.choice(styles)

def follower_count_by_tier():
    """
    Realistic Instagram follower distribution:
    Nano  (1K–10K):   ~40% of influencers
    Micro (10K–100K): ~35%
    Macro (100K–1M):  ~18%
    Mega  (1M+):       ~7%
    """
    r = random.random()
    if r < 0.40:   return int(np.random.lognormal(8.5, 0.6))     # Nano
    elif r < 0.75: return int(np.random.lognormal(10.5, 0.6))    # Micro
    elif r < 0.93: return int(np.random.lognormal(12.5, 0.5))    # Macro
    else:          return int(np.random.lognormal(14.2, 0.8))    # Mega

def engagement_rate(followers):
    """Higher ER for smaller accounts (well-documented Instagram phenomenon)."""
    if followers < 10_000:    base = np.random.uniform(0.04, 0.12)
    elif followers < 100_000: base = np.random.uniform(0.02, 0.07)
    elif followers < 1_000_000: base = np.random.uniform(0.01, 0.04)
    else:                     base = np.random.uniform(0.005, 0.025)
    return round(base * np.random.uniform(0.8, 1.2), 4)

def follower_tier(n):
    if n < 10_000:    return "Nano"
    if n < 100_000:   return "Micro"
    if n < 1_000_000: return "Macro"
    return "Mega"

# ── Generate records ───────────────────────────────────────────────────────────
records = []
cat_list = list(CATEGORIES.keys())
cat_weights = [13, 14, 12, 12, 10, 12, 11, 7, 5, 4]  # % distribution

country_pool = []
for c, w in COUNTRIES.items():
    country_pool.extend([c] * w)

used_usernames = set()

for i in range(N):
    first = random.choice(FIRST_NAMES)
    last  = random.choice(LAST_NAMES)
    full_name = f"{first} {last}"

    # Unique username
    uname = fake_username(first, last, i)
    attempt = 0
    while uname in used_usernames:
        uname = fake_username(first, last, i) + str(attempt)
        attempt += 1
    used_usernames.add(uname)

    category = random.choices(cat_list, weights=cat_weights)[0]
    sub_cat   = random.choice(CATEGORIES[category])

    followers = max(1000, min(follower_count_by_tier(), 50_000_000))
    er        = engagement_rate(followers)
    avg_likes    = max(10, int(followers * er * np.random.uniform(0.85, 1.0)))
    avg_comments = max(1,  int(avg_likes  * np.random.uniform(0.02, 0.12)))
    avg_video_views = int(avg_likes * np.random.uniform(2.0, 8.0)) if random.random() > 0.4 else 0
    media_count = random.randint(30, 5000)
    posting_freq = round(np.random.choice(
        [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 14.0],
        p=[0.05, 0.10, 0.20, 0.25, 0.18, 0.10, 0.06, 0.04, 0.02]
    ), 1)

    is_verified = (followers > 500_000 and random.random() < 0.60) or \
                  (followers > 100_000 and random.random() < 0.15) or \
                  (random.random() < 0.01)

    country = random.choice(country_pool)

    tier = follower_tier(followers)
    followers_k = f"{followers//1000}K" if followers >= 1000 else str(followers)
    countries_visited = random.randint(10, 80)
    bio_tmpl = random.choice(BIO_TEMPLATES[category])
    bio = bio_tmpl.format(sub=sub_cat, followers_k=followers_k, countries=countries_visited)

    # Audience demographics
    if category in ["Fashion", "Beauty", "Lifestyle"]:
        female_pct = round(np.random.uniform(0.60, 0.90), 2)
    elif category in ["Gaming", "Tech", "Finance"]:
        female_pct = round(np.random.uniform(0.15, 0.45), 2)
    else:
        female_pct = round(np.random.uniform(0.40, 0.65), 2)
    male_pct = round(1 - female_pct, 2)

    age_18_24 = round(np.random.uniform(0.15, 0.40), 2)
    age_25_34 = round(np.random.uniform(0.25, 0.45), 2)
    age_35_44 = round(np.random.uniform(0.10, 0.25), 2)

    # Spend & ROI (Kaggle-style campaign economics)
    # Budget typically scales with follower count
    spend_base = {
        "Nano":  np.random.uniform(200,  2000),
        "Micro": np.random.uniform(1000, 10000),
        "Macro": np.random.uniform(5000, 50000),
        "Mega":  np.random.uniform(20000, 200000),
    }[tier]
    spend = round(spend_base * np.random.uniform(0.7, 1.3), 2)

    # ROI correlated with ER and tier
    er_factor = er * 15
    roi_base = 0.3 + er_factor + np.random.normal(0, 0.4)
    roi = round(np.clip(roi_base, -0.5, 6.0), 4)
    revenue = round(spend * (1 + roi), 2)

    # Estimated reach (impressions ≈ followers × some multiplier)
    estimated_reach = int(followers * np.random.uniform(0.15, 0.45))

    records.append({
        "id":                   i + 1,
        "username":             uname,
        "full_name":            full_name,
        "category":             category,
        "sub_category":         sub_cat,
        "biography":            bio,
        "followers_count":      followers,
        "following_count":      random.randint(100, min(10000, followers // 2)),
        "media_count":          media_count,
        "avg_likes":            avg_likes,
        "avg_comments":         avg_comments,
        "avg_video_views":      avg_video_views,
        "engagement_rate":      er,
        "posting_frequency":    posting_freq,
        "estimated_reach":      estimated_reach,
        "is_verified":          is_verified,
        "country":              country,
        "follower_tier":        tier,
        "audience_female_pct":  female_pct,
        "audience_male_pct":    male_pct,
        "audience_age_18_24":   age_18_24,
        "audience_age_25_34":   age_25_34,
        "audience_age_35_44":   age_35_44,
        "spend":                spend,
        "revenue":              revenue,
        "roi":                  roi,
    })

df = pd.DataFrame(records)

# ── Save CSV ───────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
csv_path = "data/influencers_10k.csv"
df.to_csv(csv_path, index=False)
print(f"✅ CSV saved: {csv_path}  ({len(df):,} rows)")

# ── Save SQLite ────────────────────────────────────────────────────────────────
db_path = "data/influencers.db"
conn = sqlite3.connect(db_path)
df.to_sql("influencers", conn, if_exists="replace", index=False)

# Add indexes for fast filtering
conn.execute("CREATE INDEX IF NOT EXISTS idx_category       ON influencers(category)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_tier           ON influencers(follower_tier)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_er             ON influencers(engagement_rate)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_followers      ON influencers(followers_count)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_country        ON influencers(country)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_roi            ON influencers(roi)")
conn.commit()
conn.close()
print(f"✅ SQLite saved: {db_path}")

# ── Stats summary ──────────────────────────────────────────────────────────────
print(f"\n📊 Dataset Summary:")
print(f"   Total records : {len(df):,}")
print(f"   Categories    : {df['category'].nunique()}")
print(f"\n   Follower tier distribution:")
print(df['follower_tier'].value_counts().to_string())
print(f"\n   Category distribution:")
print(df['category'].value_counts().to_string())
print(f"\n   Avg engagement rate : {df['engagement_rate'].mean():.3f}")
print(f"   Avg ROI             : {df['roi'].mean():.3f}")
print(f"   Verified accounts   : {df['is_verified'].sum():,}")
print(f"   Countries           : {df['country'].nunique()}")
