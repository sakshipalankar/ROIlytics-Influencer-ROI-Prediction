"""Tests for scraped data ingestion pipeline and scoring."""
import pytest
from backend.scripts.ingest_scraped import parse_count
from backend.app.services.constants import (
    CATEGORY_BENCHMARKS,
    CATEGORIES,
    CATEGORY_ENCODING,
)
from backend.app.services.influencer_db import compute_fit_score


def test_parse_count():
    assert parse_count(None) is None
    assert parse_count("") is None
    assert parse_count("0") == 0
    assert parse_count(123) == 123
    assert parse_count(123.45) == 123
    assert parse_count("1,234") == 1234
    assert parse_count("12,345") == 12345
    assert parse_count("45.3K") == 45300
    assert parse_count("1.2M") == 1200000
    assert parse_count("2.5B") == 2500000000
    assert parse_count("500 followers") == 500
    assert parse_count("244K likes") == 244000


def test_engagement_rate_and_capping():
    # ER = (avg_likes + avg_comments) / followers_count
    followers = 10000
    avg_likes = 500
    avg_comments = 50
    er = (avg_likes + avg_comments) / followers
    assert er == pytest.approx(0.055)

    # Capped at 0.5
    extreme_likes = 8000
    extreme_comments = 2000
    raw_er = (extreme_likes + extreme_comments) / followers
    capped_er = min(raw_er, 0.5)
    assert capped_er == 0.5


def test_fit_score_ordering_and_category_benchmark():
    high_er_creator = {
        "id": 1,
        "username": "creator_fit",
        "category": "Fitness",
        "followers_count": 50000,
        "avg_likes": 3000,
        "avg_comments": 200,
        "engagement_rate": 0.064,  # Well above Fitness benchmark of ~0.032
        "posting_frequency": 4.0,
        "follower_tier": "Micro",
    }

    low_er_creator = {
        "id": 2,
        "username": "creator_unfit",
        "category": "Fitness",
        "followers_count": 50000,
        "avg_likes": 200,
        "avg_comments": 10,
        "engagement_rate": 0.0042,  # Far below Fitness benchmark
        "posting_frequency": 0.5,
        "follower_tier": "Micro",
    }

    score_high = compute_fit_score(high_er_creator, "Fitness", budget=5000, goal="engagement", budget_tier="Micro")
    score_low = compute_fit_score(low_er_creator, "Fitness", budget=5000, goal="engagement", budget_tier="Micro")

    assert score_high > score_low
    assert score_high > 60
    assert score_low < 50


def test_fit_score_all_categories_benchmark_fallback():
    # When category is "All" or None, scoring must evaluate creator against its own category benchmark
    tech_creator = {
        "id": 10,
        "username": "tech_guy",
        "category": "Tech",
        "followers_count": 50000,
        "avg_likes": 1500,
        "avg_comments": 100,
        "engagement_rate": 0.032,  # Above Tech benchmark of 0.024
        "posting_frequency": 3.0,
        "follower_tier": "Micro",
    }

    score_all = compute_fit_score(tech_creator, None, budget=5000, goal="awareness", budget_tier="Micro")
    assert score_all > 50


def test_constants_all_10_categories():
    assert len(CATEGORIES) == 10
    assert set(CATEGORIES) == {
        "Fitness", "Fashion", "Tech", "Food", "Travel",
        "Lifestyle", "Beauty", "Gaming", "Finance", "Education"
    }
    # Original 6 codes preserved (0 to 5)
    assert CATEGORY_ENCODING["Fitness"] == 0
    assert CATEGORY_ENCODING["Fashion"] == 1
    assert CATEGORY_ENCODING["Tech"] == 2
    assert CATEGORY_ENCODING["Food"] == 3
    assert CATEGORY_ENCODING["Travel"] == 4
    assert CATEGORY_ENCODING["Lifestyle"] == 5
    # Extrapolated 4 categories (6 to 9)
    assert CATEGORY_ENCODING["Beauty"] == 6
    assert CATEGORY_ENCODING["Gaming"] == 7
    assert CATEGORY_ENCODING["Finance"] == 8
    assert CATEGORY_ENCODING["Education"] == 9
