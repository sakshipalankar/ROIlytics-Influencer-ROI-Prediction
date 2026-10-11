"""Ingestion script for scraped Instagram data — ROIlytics.

Reads raw scraped profile and post JSONs from instagram_collector/data,
computes quality-controlled influencer metrics, runs ML prediction for ROI,
and outputs clean data to data/influencers_clean.csv and data/influencers.db.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import logging
import math
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants & Paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Tier-based campaign spend estimation formula (documented constants)
TIER_BASE_SPEND = {
    "Nano": 1500.0,      # <10K followers
    "Micro": 8000.0,     # <100K followers
    "Macro": 45000.0,    # <1M followers
    "Mega": 150000.0,    # >=1M followers
}

# Helpers
def parse_count(val: Any) -> Optional[int]:
    """Parse numeric count string handling K, M, B suffixes, commas, and floats."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val) if not math.isnan(val) else None
    s = str(val).strip().replace(",", "")
    if not s or s.lower() in ("none", "null", ""):
        return None
    # If string contains trailing words (e.g. "500 followers", "244K likes"), extract the token
    m = re.match(r"^([\d\.]+)([kKmMbB]?)(?:\s+.*)?$", s)
    if m:
        num_str, suffix = m.groups()
        multiplier = 1
        if suffix.upper() == "K":
            multiplier = 1_000
        elif suffix.upper() == "M":
            multiplier = 1_000_000
        elif suffix.upper() == "B":
            multiplier = 1_000_000_000
        try:
            return int(float(num_str) * multiplier)
        except Exception:
            return None

    s = s.upper()
    multiplier = 1
    if s.endswith("K"):
        multiplier = 1_000
        s = s[:-1]
    elif s.endswith("M"):
        multiplier = 1_000_000
        s = s[:-1]
    elif s.endswith("B"):
        multiplier = 1_000_000_000
        s = s[:-1]
    try:
        return int(float(s) * multiplier)
    except Exception:
        return None


def assign_bucket(followers: int) -> str:
    """Follower tier assignment matching predictor logic."""
    if followers < 10_000:
        return "Nano"
    if followers < 100_000:
        return "Micro"
    if followers < 1_000_000:
        return "Macro"
    return "Mega"


def estimate_spend(tier: str, followers: int) -> float:
    """Estimated campaign cost from documented tier-based rate formula."""
    base = TIER_BASE_SPEND.get(tier, 5000.0)
    # Scale slightly with followers within the tier
    if tier == "Nano":
        factor = max(1.0, followers / 5_000)
    elif tier == "Micro":
        factor = max(1.0, followers / 50_000)
    elif tier == "Macro":
        factor = max(1.0, followers / 500_000)
    else:
        factor = max(1.0, followers / 2_000_000)
    return round(base * min(factor, 2.0), 2)


def parse_post_timestamp(meta: str) -> Optional[datetime]:
    """Extract post timestamp from Instagram post meta description if present."""
    if not meta:
        return None
    m = re.search(r"on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", meta)
    if m:
        try:
            return datetime.strptime(m.group(1), "%B %d, %Y")
        except Exception:
            pass
    return None


def calculate_posting_frequency(timestamps: list[datetime]) -> float:
    """Calculate posts per week from post timestamps, falling back to 3.5."""
    if len(timestamps) < 2:
        return 3.5
    timestamps.sort()
    delta_days = (timestamps[-1] - timestamps[0]).days
    if delta_days <= 0:
        return 3.5
    weeks = delta_days / 7.0
    if weeks < 0.2:
        return 3.5
    freq = len(timestamps) / weeks
    return round(min(max(freq, 0.5), 14.0), 2)


def check_is_verified(html_path: Optional[str]) -> bool:
    """Detect verified badge from saved HTML if file exists."""
    if not html_path or not os.path.exists(html_path):
        return False
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(200_000)
            if '"is_verified":true' in content or 'aria-label="Verified"' in content:
                return True
    except Exception:
        pass
    return False


ORIGINAL_18_MAPPING: dict[str, tuple[str, str]] = {
    "rajshamani": ("Education", "Finance & Podcasting"),
    "beerbiceps": ("Fitness", "Health & Podcasts"),
    "the.rebel.kid": ("Travel", "Travel & Lifestyle"),
    "komalpandeyofficial": ("Fashion", "Fashion & Styling"),
    "kritikakhurana": ("Food", "Food & Lifestyle"),
    "barkhasingh0308": ("Lifestyle", "Acting & Lifestyle"),
    "aashnashroff": ("Beauty", "Beauty & Luxury"),
    "masoomminawala": ("Beauty", "Luxury & Beauty"),
    "shivesh17": ("Food", "Baking & Desserts"),
    "ranveer.brar": ("Food", "Culinary & Cooking"),
    "carryminati": ("Gaming", "Gaming & Comedy"),
    "bhuvan.bam22": ("Lifestyle", "Entertainment & Comedy"),
    "anubhavsinghbassi": ("Lifestyle", "Standup Comedy"),
    "ankurwarikoo": ("Finance", "Personal Finance & Career"),
    "sahil_khan": ("Fitness", "Bodybuilding & Fitness"),
    "namratapurohit": ("Fitness", "Pilates & Fitness"),
    "sejalkumar": ("Lifestyle", "Music & Lifestyle"),
    "radhikabangia": ("Lifestyle", "Dance & Lifestyle"),
}

VALID_CATEGORIES: set[str] = {
    "Fitness", "Fashion", "Tech", "Food", "Travel",
    "Lifestyle", "Beauty", "Gaming", "Finance", "Education"
}

BRAND_ACCOUNTS: set[str] = {
    "nike", "adidas", "myntra", "zomato",
    "mysmartprice", "91mobiles", "digit.in", "houseofmisu"
}

# Whole-word keyword regexes for heuristic fallback (only for usernames missing from 18 & CSV)
# Short/ambiguous tokens like ai, run, sir, play, look, model, class, eat, ca, dr are excluded
HEURISTIC_RULES: list[tuple[str, str, list[str]]] = [
    ("Gaming", "Gaming & Streaming", [r"\bgamer\b", r"\bgaming\b", r"\bgamers\b", r"\besports\b", r"\bgameplay\b"]),
    ("Fitness", "Fitness & Training", [r"\bfitness\b", r"\bworkout\b", r"\bgym\b", r"\byoga\b", r"\bpilates\b", r"\bbodybuilding\b"]),
    ("Tech", "Consumer Tech & Gadgets", [r"\btech\b", r"\bgadgets\b", r"\btechnology\b", r"\bmobiles\b"]),
    ("Food", "Recipes & Culinary", [r"\bkitchen\b", r"\brecipe\b", r"\brecipes\b", r"\bchef\b", r"\bfoodie\b", r"\bcooking\b", r"\bculinary\b"]),
    ("Travel", "Travel & Adventure", [r"\btravel\b", r"\btraveler\b", r"\btraveller\b", r"\bjourney\b", r"\bwanderlust\b"]),
    ("Finance", "Personal Finance & Wealth", [r"\bfinance\b", r"\bmoney\b", r"\bwealth\b", r"\binvesting\b", r"\btax\b"]),
    ("Beauty", "Beauty & Skincare", [r"\bbeauty\b", r"\bmakeup\b", r"\bskincare\b", r"\bcosmetics\b"]),
    ("Fashion", "Fashion & Styling", [r"\bfashion\b", r"\boutfit\b", r"\bstyle\b", r"\bstyling\b"]),
    ("Education", "Education & Learning", [r"\beducation\b", r"\bacademy\b", r"\btutorial\b", r"\bcoaching\b"]),
]


def resolve_category(
    username: str,
    csv_map: dict[str, tuple[str, str]],
    source_tracker: dict[str, str]
) -> tuple[str, str, str]:
    """
    Resolve category with priority:
    1. Original 18 manual mapping
    2. CSV from ROIlytics_282_new_Indian_influencers.csv
    3. Whole-word keyword heuristic fallback (missing -> Lifestyle)
    Returns: (category, sub_category, source)
    """
    u = username.lower().strip().lstrip("@")
    
    # Priority 1: Original 18
    if u in ORIGINAL_18_MAPPING:
        cat, sub_cat = ORIGINAL_18_MAPPING[u]
        source_tracker[u] = "original_18"
        return cat, sub_cat, "original_18"

    # Priority 2: CSV mapping
    if u in csv_map:
        cat, sub_cat = csv_map[u]
        if cat in VALID_CATEGORIES:
            source_tracker[u] = "csv"
            return cat, sub_cat, "csv"

    # Priority 3: Whole-word keyword regex heuristic
    for cat, sub_cat, patterns in HEURISTIC_RULES:
        for pat in patterns:
            if re.search(pat, u, re.IGNORECASE):
                source_tracker[u] = "heuristic"
                return cat, sub_cat, "heuristic"

    # Fallback to Lifestyle
    source_tracker[u] = "heuristic"
    return "Lifestyle", "General Lifestyle", "heuristic"


def load_csv_categories(csv_path: Path) -> dict[str, tuple[str, str]]:
    """Load categories from ROIlytics_282_new_Indian_influencers.csv."""
    mapping = {}
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                u = row.get("username", "").strip().lower().lstrip("@")
                c = row.get("category", "").strip()
                sc = row.get("sub_category", "").strip() or "General Lifestyle"
                if u and c:
                    mapping[u] = (c, sc)
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Ingest scraped Instagram data into ROIlytics")
    default_src = PROJECT_ROOT.parent / "instagram_collector" / "data"
    parser.add_argument("--src", type=str, default=str(default_src), help="Path to scraped data directory")
    args = parser.parse_args()

    src_dir = Path(args.src).resolve()
    if not src_dir.exists():
        logger.error(f"Source directory does not exist: {src_dir}")
        sys.exit(1)

    profiles_dir = src_dir / "profiles"
    posts_dir = src_dir / "posts"
    logger.info(f"Reading scraped data from {src_dir}")

    # Add backend to sys.path so we can import services
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from app.services.predictor import PredictorService

    predictor = PredictorService.get()
    logger.info("Initialized PredictorService for ROI calculation")

    # Load raw categories CSV
    raw_csv = PROJECT_ROOT / "data" / "ROIlytics_282_new_Indian_influencers.csv"
    csv_category_map = load_csv_categories(raw_csv)
    logger.info(f"Loaded {len(csv_category_map)} mappings from ROIlytics_282_new_Indian_influencers.csv")

    # Read profiles
    profile_files = glob.glob(str(profiles_dir / "*.json"))
    raw_post_files = glob.glob(str(posts_dir / "*.json"))
    total_accounts_scraped = len(profile_files)
    total_raw_post_records = len(raw_post_files)

    logger.info(f"Found {total_accounts_scraped} profile JSONs and {total_raw_post_records} post JSONs")

    # Prepare category source tracking and username_categories.csv
    category_source_tracker: dict[str, str] = {}
    resolved_category_map: dict[str, tuple[str, str]] = {}
    category_guessed_list: list[str] = []

    for p_file in profile_files:
        u = Path(p_file).stem.lower().strip()
        cat, sub_cat, src = resolve_category(u, csv_category_map, category_source_tracker)
        resolved_category_map[u] = (cat, sub_cat)
        if src == "heuristic":
            category_guessed_list.append(u)

    # Save data/username_categories.csv
    username_categories_path = PROJECT_ROOT / "data" / "username_categories.csv"
    with open(username_categories_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "category", "sub_category"])
        for u in sorted(resolved_category_map.keys()):
            writer.writerow([u, resolved_category_map[u][0], resolved_category_map[u][1]])
    logger.info(f"Saved {len(resolved_category_map)} rows to {username_categories_path}")

    clean_records: list[dict[str, Any]] = []
    dropped_records: list[dict[str, Any]] = []
    capped_records: list[dict[str, Any]] = []
    suspect_er_records: list[dict[str, Any]] = []

    for p_file in profile_files:
        try:
            with open(p_file, "r", encoding="utf-8") as f:
                p_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read {p_file}: {e}")
            continue

        username = (p_data.get("username") or Path(p_file).stem).lower().strip()
        profile_url = p_data.get("profile_url") or f"https://www.instagram.com/{username}/"
        title = p_data.get("title") or ""
        meta_desc = p_data.get("meta_description") or ""

        # Extract full_name from title e.g. "Lokesh jain (@8bit_goldy) • Instagram photos and videos"
        full_name = username
        if "(@" in title:
            full_name = title.split("(@")[0].strip()
        elif "•" in title:
            full_name = title.split("•")[0].strip()

        # Biography
        biography = ""
        if 'on Instagram: "' in meta_desc:
            biography = meta_desc.split('on Instagram: "')[-1].rstrip('"')
        elif meta_desc:
            biography = meta_desc

        # Followers, Following, Media Count
        followers_count = parse_count(p_data.get("followers"))
        if followers_count is None:
            m = re.search(r"([\d.,KMkm]+)\s*Followers", meta_desc, re.IGNORECASE)
            if m:
                followers_count = parse_count(m.group(1))

        following_count = parse_count(p_data.get("following"))
        if following_count is None:
            m = re.search(r"([\d.,KMkm]+)\s*Following", meta_desc, re.IGNORECASE)
            if m:
                following_count = parse_count(m.group(1))

        media_count = parse_count(p_data.get("posts_count"))
        if media_count is None:
            m = re.search(r"([\d.,KMkm]+)\s*Posts", meta_desc, re.IGNORECASE)
            if m:
                media_count = parse_count(m.group(1))

        # Join posts
        posts = p_data.get("posts") or []
        if not posts:
            user_post_files = glob.glob(str(posts_dir / f"{username}_post_*.json"))
            for upf in user_post_files:
                try:
                    with open(upf, "r", encoding="utf-8") as pf:
                        posts.append(json.load(pf))
                except Exception:
                    pass

        # Usable likes and comments
        likes_list: list[int] = []
        comments_list: list[int] = []
        post_timestamps: list[datetime] = []

        for post in posts:
            l = parse_count(post.get("likes"))
            c = parse_count(post.get("comments"))
            p_meta = post.get("meta_description") or post.get("og_description") or ""

            if l is None and p_meta:
                m_like = re.search(r"([\d.,KMkm]+)\s*likes", p_meta, re.IGNORECASE)
                if m_like:
                    l = parse_count(m_like.group(1))

            if c is None and p_meta:
                m_comm = re.search(r"([\d.,KMkm]+)\s*comments", p_meta, re.IGNORECASE)
                if m_comm:
                    c = parse_count(m_comm.group(1))

            # Exclude hidden likes (null) from likes average; never treat as zero
            if l is not None:
                likes_list.append(l)
            if c is not None:
                comments_list.append(c)

            ts = parse_post_timestamp(p_meta)
            if ts:
                post_timestamps.append(ts)

        posts_used = max(len(likes_list), len(comments_list))

        # Quality filter
        if followers_count is None or followers_count <= 0:
            dropped_records.append({
                "username": username,
                "reason": f"Missing or zero followers_count: {followers_count}",
            })
            continue

        if posts_used < 3:
            dropped_records.append({
                "username": username,
                "reason": f"posts_used ({posts_used}) < 3 required posts",
            })
            continue

        avg_likes = float(sum(likes_list) / len(likes_list)) if likes_list else 0.0
        avg_comments = float(sum(comments_list) / len(comments_list)) if comments_list else 0.0
        raw_er = (avg_likes + avg_comments) / float(followers_count)

        # Capping & er_suspect policy: if engagement_rate > 0.25, flag as suspect
        er_suspect = 1 if raw_er > 0.25 else 0
        if raw_er > 0.5:
            capped_records.append({
                "username": username,
                "raw_er": raw_er,
                "capped_er": 0.5,
                "reason": f"Extreme engagement rate ({raw_er:.4f} > 0.50); suspect data flagged"
            })
            engagement_rate = 0.5
        else:
            engagement_rate = round(raw_er, 6)

        if er_suspect == 1:
            suspect_er_records.append({
                "username": username,
                "raw_er": raw_er,
                "engagement_rate": engagement_rate,
                "followers_count": followers_count,
                "avg_likes": avg_likes,
                "avg_comments": avg_comments,
                "reason": f"Engagement rate ({raw_er:.4f}) exceeds 0.25 threshold"
            })

        follower_tier = assign_bucket(followers_count)
        estimated_reach = int(round(0.3 * followers_count))
        posting_frequency = calculate_posting_frequency(post_timestamps)
        is_verified = 1 if check_is_verified(p_data.get("profile_html")) else 0
        country = "IN"

        # Category mapping
        cat, sub_cat = resolved_category_map.get(username, ("Lifestyle", "General Lifestyle"))

        # ROI & Economics
        spend = estimate_spend(follower_tier, followers_count)
        try:
            pred = predictor.predict(
                followers_count=followers_count,
                media_count=media_count or 0,
                avg_likes=avg_likes,
                avg_comments=avg_comments,
                category=cat,
                posting_frequency=posting_frequency,
                spend=spend,
            )
            roi = round(float(pred["roi"]), 4)
        except Exception as e:
            logger.warning(f"Predict failed for @{username}: {e}; defaulting roi to 1.0")
            roi = 1.0

        revenue = round(spend * (1.0 + roi), 2)
        roi_source = "model_estimate"
        profile_screenshot = p_data.get("profile_screenshot") or ""
        collected_at = p_data.get("collected_at") or datetime.now().isoformat()

        # Brand account detection
        is_brand = 1 if username in BRAND_ACCOUNTS else 0

        clean_records.append({
            "id": len(clean_records) + 1,
            "username": username,
            "full_name": full_name or username,
            "category": cat,
            "sub_category": sub_cat,
            "biography": biography,
            "followers_count": followers_count,
            "following_count": following_count or 0,
            "media_count": media_count or 0,
            "avg_likes": round(avg_likes, 1),
            "avg_comments": round(avg_comments, 1),
            "avg_video_views": 0,
            "engagement_rate": engagement_rate,
            "posting_frequency": posting_frequency,
            "estimated_reach": estimated_reach,
            "is_verified": is_verified,
            "country": country,
            "follower_tier": follower_tier,
            "audience_female_pct": None,
            "audience_male_pct": None,
            "audience_age_18_24": None,
            "audience_age_25_34": None,
            "audience_age_35_44": None,
            "posts_used": posts_used,
            "spend": spend,
            "revenue": revenue,
            "roi": roi,
            "roi_source": roi_source,
            "is_brand": is_brand,
            "er_suspect": er_suspect,
            "profile_url": profile_url,
            "profile_screenshot": profile_screenshot,
            "collected_at": collected_at,
        })

    # Output directory
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write data/influencers_clean.csv
    csv_out = data_dir / "influencers_clean.csv"
    if clean_records:
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(clean_records[0].keys()))
            writer.writeheader()
            writer.writerows(clean_records)
        logger.info(f"Saved {len(clean_records)} clean records to {csv_out}")

    # Calculate usable post records belonging to retained influencers
    total_usable_post_records = sum(r.get("posts_used", 0) for r in clean_records)

    # Category source statistics across scraped accounts
    source_counts = {
        "original_18": sum(1 for src in category_source_tracker.values() if src == "original_18"),
        "csv": sum(1 for src in category_source_tracker.values() if src == "csv"),
        "heuristic": sum(1 for src in category_source_tracker.values() if src == "heuristic"),
    }

    # 2. Write data/ingest_report.json
    report_out = data_dir / "ingest_report.json"
    with open(report_out, "w", encoding="utf-8") as f:
        json.dump({
            "total_accounts_scraped": total_accounts_scraped,
            "total_raw_post_records": total_raw_post_records,
            "total_usable_post_records": total_usable_post_records,
            "total_clean_usable_records": len(clean_records),
            "category_sources": source_counts,
            "category_guessed": category_guessed_list,
            "dropped_count": len(dropped_records),
            "capped_count": len(capped_records),
            "suspect_er_count": len(suspect_er_records),
            "dropped_records": dropped_records,
            "capped_records": capped_records,
            "suspect_er_records": suspect_er_records,
        }, f, indent=2)
    logger.info(f"Saved ingest report to {report_out}")

    # 3. Rebuild data/influencers.db inside a transaction
    db_out = data_dir / "influencers.db"
    conn = sqlite3.connect(str(db_out))
    try:
        with conn:
            conn.execute("DROP TABLE IF EXISTS influencers")
            conn.execute("""
                CREATE TABLE influencers (
                    id                  INTEGER PRIMARY KEY,
                    username            TEXT NOT NULL,
                    full_name           TEXT,
                    category            TEXT,
                    sub_category        TEXT,
                    biography           TEXT,
                    followers_count     INTEGER,
                    following_count     INTEGER,
                    media_count         INTEGER,
                    avg_likes           REAL,
                    avg_comments        REAL,
                    avg_video_views     INTEGER DEFAULT 0,
                    engagement_rate     REAL,
                    posting_frequency   REAL,
                    estimated_reach     INTEGER,
                    is_verified         INTEGER DEFAULT 0,
                    country             TEXT DEFAULT 'IN',
                    follower_tier       TEXT,
                    audience_female_pct REAL,
                    audience_male_pct   REAL,
                    audience_age_18_24  REAL,
                    audience_age_25_34  REAL,
                    audience_age_35_44  REAL,
                    posts_used          INTEGER DEFAULT 0,
                    spend               REAL,
                    revenue             REAL,
                    roi                 REAL,
                    roi_source          TEXT DEFAULT 'model_estimate',
                    is_brand            INTEGER DEFAULT 0,
                    er_suspect          INTEGER DEFAULT 0,
                    profile_url         TEXT,
                    profile_screenshot  TEXT,
                    collected_at        TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_category ON influencers(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_tier ON influencers(follower_tier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_username ON influencers(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_is_brand ON influencers(is_brand)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_er_suspect ON influencers(er_suspect)")

            if clean_records:
                cols = list(clean_records[0].keys())
                placeholders = ":" + ", :".join(cols)
                sql = f"INSERT INTO influencers ({', '.join(cols)}) VALUES ({placeholders})"
                conn.executemany(sql, clean_records)
        logger.info(f"Successfully rebuilt {db_out} with {len(clean_records)} influencers")
    finally:
        conn.close()

    # Category and Tier breakdowns
    cat_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    for r in clean_records:
        c = r["category"]
        t = r["follower_tier"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
        tier_counts[t] = tier_counts.get(t, 0) + 1

    # Print summary
    print("\n" + "=" * 60)
    print("ROIlytics Scraped Data Ingestion Summary")
    print("=" * 60)
    print(f"Total accounts scraped:      {total_accounts_scraped}")
    print(f"Total raw post records:      {total_raw_post_records}")
    print(f"Total usable post records:   {total_usable_post_records}")
    print(f"Total clean/usable records:  {len(clean_records)}")
    print(f"Total dropped rows:          {len(dropped_records)}")
    print(f"Total ER capped rows:        {len(capped_records)}")
    print("\nCategory Resolution Sources:")
    print(f"  Manual 18 mapping: {source_counts['original_18']}")
    print(f"  CSV mapping:       {source_counts['csv']}")
    print(f"  Keyword heuristic: {source_counts['heuristic']}")
    print("\nCounts per Category:")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<15}: {cnt}")
    print("\nCounts per Tier:")
    for tier in ["Nano", "Micro", "Macro", "Mega"]:
        print(f"  {tier:<15}: {tier_counts.get(tier, 0)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
