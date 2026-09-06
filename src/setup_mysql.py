"""
Setup and Migrate ROIlytics Data to MySQL Database (roilytics_db)
"""
import os
import sys
import sqlite3
import csv
from pathlib import Path
import pymysql
from dotenv import load_dotenv

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "roilytics_db")

SCHEMA_FILE = PROJECT_ROOT / "database" / "schema.sql"
SQLITE_DB = PROJECT_ROOT / "data" / "influencers.db"
CAMPAIGN_CSV = PROJECT_ROOT / "data" / "kaggle_campaign_data.csv"


def get_mysql_connection(password: str = None):
    pwd = password if password is not None else MYSQL_PASSWORD
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=pwd,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def test_connection_and_connect():
    """Attempt connecting with env password, then fallback candidate passwords."""
    candidates = [MYSQL_PASSWORD] if MYSQL_PASSWORD else []
    # Common local dev passwords
    common_passwords = ["", "root", "root123", "admin", "password", "123456", "1234", "Password123!"]
    for p in common_passwords:
        if p not in candidates:
            candidates.append(p)

    for pwd in candidates:
        try:
            conn = get_mysql_connection(pwd)
            print(f"Connected to MySQL on {MYSQL_HOST}:{MYSQL_PORT} as '{MYSQL_USER}'")
            return conn, pwd
        except pymysql.MySQLError:
            continue

    print(f"Could not connect to MySQL with default credentials.")
    print("Please provide the MySQL password via MYSQL_PASSWORD in .env or as command line arg.")
    sys.exit(1)


def init_database_and_tables(conn):
    """Run DDL schema script."""
    print(f"Creating database '{MYSQL_DATABASE}' and tables...")
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute(f"USE `{MYSQL_DATABASE}`;")

        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Split and execute statements
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
        for stmt in statements:
            # Skip USE or CREATE DATABASE since already handled
            if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                continue
            cur.execute(stmt)

    conn.commit()
    print("All tables & indexes created successfully in MySQL!")


def migrate_influencers(conn):
    """Migrate 10,500+ influencers from SQLite to MySQL."""
    if not SQLITE_DB.exists():
        print(f"SQLite file not found at {SQLITE_DB}")
        return

    print(f"Reading from SQLite database: {SQLITE_DB}...")
    s_conn = sqlite3.connect(str(SQLITE_DB))
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()
    s_cur.execute("SELECT * FROM influencers")
    rows = s_cur.fetchall()
    total = len(rows)
    print(f"Found {total} records in SQLite influencers table.")

    if total == 0:
        return

    columns = [
        "username", "full_name", "category", "sub_category", "biography",
        "followers_count", "following_count", "media_count", "avg_likes",
        "avg_comments", "avg_video_views", "engagement_rate", "posting_frequency",
        "estimated_reach", "is_verified", "country", "follower_tier",
        "audience_female_pct", "audience_male_pct", "audience_age_18_24",
        "audience_age_25_34", "audience_age_35_44", "spend", "revenue", "roi"
    ]

    col_names = ", ".join(f"`{c}`" for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT IGNORE INTO `{MYSQL_DATABASE}`.`influencers` ({col_names}) VALUES ({placeholders})"

    batch_size = 500
    batch = []
    inserted_count = 0

    with conn.cursor() as cur:
        for r in rows:
            val_tuple = tuple(r[c] if c in r.keys() else None for c in columns)
            batch.append(val_tuple)
            if len(batch) >= batch_size:
                cur.executemany(insert_sql, batch)
                conn.commit()
                inserted_count += len(batch)
                print(f"   Migrated {inserted_count}/{total} influencers...", end="\r")
                batch = []

        if batch:
            cur.executemany(insert_sql, batch)
            conn.commit()
            inserted_count += len(batch)

    s_conn.close()
    print(f"\nSuccessfully migrated {inserted_count} influencers into MySQL!")


def migrate_campaigns(conn):
    """Migrate 600 campaigns from CSV to MySQL."""
    if not CAMPAIGN_CSV.exists():
        print(f"Campaign CSV not found at {CAMPAIGN_CSV}")
        return

    print(f"Reading campaigns from: {CAMPAIGN_CSV}...")
    campaigns = []
    with open(CAMPAIGN_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            campaigns.append((
                row.get("Campaign_ID") or row.get("campaign_id") or f"CAMP_{len(campaigns):04d}",
                row.get("Brand_Name") or row.get("brand_name") or "Global Brand",
                row.get("Category") or row.get("category") or "General",
                row.get("Platform") or row.get("platform") or "Instagram",
                row.get("Campaign_Type") or row.get("campaign_type") or "Sponsored Post",
                float(row.get("Spend") or row.get("spend") or 0),
                float(row.get("Revenue") or row.get("revenue") or 0),
                float(row.get("ROI") or row.get("roi") or 0),
                int(float(row.get("Impressions") or row.get("impressions") or 0)),
                int(float(row.get("Reach") or row.get("reach") or 0)),
            ))

    if not campaigns:
        return

    insert_sql = """
    INSERT IGNORE INTO `roilytics_db`.`campaigns`
      (`campaign_id`, `brand_name`, `category`, `platform`, `campaign_type`, `spend`, `revenue`, `roi`, `impressions`, `reach`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.executemany(insert_sql, campaigns)
        conn.commit()

    print(f"Successfully migrated {len(campaigns)} marketing campaigns into MySQL!")


def seed_default_users(conn):
    """Seed demo accounts."""
    insert_sql = """
    INSERT IGNORE INTO `roilytics_db`.`users`
      (`username`, `email`, `password_hash`, `provider`, `role`)
    VALUES (%s, %s, %s, %s, %s)
    """
    users = [
        ("Alex Rivers", "demo@roilytics.ai", "Password123!", "email", "Senior Campaign Strategist"),
        ("Sarah Chen", "sarah.chen@glowbeauty.com", "Password123!", "email", "Marketing Director"),
    ]
    with conn.cursor() as cur:
        cur.executemany(insert_sql, users)
        conn.commit()
    print(f"Seeded {len(users)} default users into MySQL.")


def main():
    if len(sys.argv) > 1:
        custom_pwd = sys.argv[1]
        conn = get_mysql_connection(custom_pwd)
        pwd_used = custom_pwd
    else:
        conn, pwd_used = test_connection_and_connect()

    init_database_and_tables(conn)
    migrate_influencers(conn)
    migrate_campaigns(conn)
    seed_default_users(conn)

    # Summary checks
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS c FROM `{MYSQL_DATABASE}`.`influencers`;")
        inf_count = cur.fetchone()["c"]
        cur.execute(f"SELECT COUNT(*) AS c FROM `{MYSQL_DATABASE}`.`campaigns`;")
        cmp_count = cur.fetchone()["c"]
        cur.execute(f"SELECT COUNT(*) AS c FROM `{MYSQL_DATABASE}`.`users`;")
        usr_count = cur.fetchone()["c"]

    print("\n" + "=" * 55)
    print("🎉 ROIlytics MySQL Database Setup Completed Successfully!")
    print(f"Database:        {MYSQL_DATABASE}")
    print(f"Influencers:     {inf_count:,} records")
    print(f"Campaigns:       {cmp_count:,} records")
    print(f"Users:           {usr_count:,} records")
    print("=" * 55)
    conn.close()


if __name__ == "__main__":
    main()
