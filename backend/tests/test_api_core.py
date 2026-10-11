"""Core API tests for ROIlytics — predict, analytics, models, discover endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "influencer_count" in data
    assert data["influencer_count"] > 0


def test_models_results():
    res = client.get("/api/models/results")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data or "best_model" in data or "metrics" in data


def test_analytics_overview():
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "category_distribution" in data
    assert "avg_roi" in data


def test_discover_stats():
    res = client.get("/api/discover/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] > 0


def test_discover_search():
    res = client.post("/api/discover", json={
        "category": "Fitness",
        "budget": 5000,
        "goal": "awareness",
        "limit": 5,
        "offset": 0
    })
    assert res.status_code == 200
    data = res.json()
    assert "influencers" in data or "items" in data or isinstance(data, list)


def test_discover_top():
    res = client.get("/api/discover/top?category=Fitness&budget=5000&goal=awareness&limit=3")
    assert res.status_code == 200
    data = res.json()
    assert "top_influencers" in data or "influencers" in data or isinstance(data, list)


def test_predict():
    payload = {
        "followers_count": 50000,
        "media_count": 120,
        "avg_likes": 2500,
        "avg_comments": 150,
        "category": "Fitness",
        "posting_frequency": 3.5,
        "spend": 5000
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "roi" in data or "estimated_roi" in data or "predicted_roi" in data
