import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.main import app
import os

# Set env var before importing to test the settings
os.environ["ENABLE_PUBLIC_LOOKUP"] = "true"

client = TestClient(app)

def test_snapshot_valid():
    response = client.post("/api/public/snapshot", json={
        "username": "test_snap_valid",
        "category": "Tech",
        "spend": 5000,
        "followers_count": 1000,
        "media_count": 10,
        "posts": [{"like_count": 100, "comments_count": 10}, {"like_count": 100, "comments_count": 10}, {"like_count": 100, "comments_count": 10}],
        "collected_note": "Test note"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "public_snapshot"
    assert data["reliable"] == True
    assert data["estimated_roi"] is not None
    assert "Manual snapshot" in data["note"]
    assert "Test note" in data["note"]

def test_snapshot_no_followers_fails_validation():
    response = client.post("/api/public/snapshot", json={
        "username": "test_snap_invalid",
        "category": "Tech",
        "spend": 5000,
        "followers_count": 0,
        "media_count": 10,
        "posts": [{"like_count": 100, "comments_count": 10}]
    })
    assert response.status_code == 422

def test_snapshot_negative_metrics_fails_validation():
    response = client.post("/api/public/snapshot", json={
        "username": "test_snap_invalid2",
        "category": "Tech",
        "spend": 5000,
        "followers_count": 1000,
        "media_count": 10,
        "posts": [{"like_count": -5, "comments_count": 10}]
    })
    assert response.status_code == 422

def test_snapshot_future_date_fails_validation():
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = client.post("/api/public/snapshot", json={
        "username": "test_snap_invalid3",
        "category": "Tech",
        "spend": 5000,
        "followers_count": 1000,
        "media_count": 10,
        "posts": [{"like_count": 10, "comments_count": 10, "timestamp": future}]
    })
    assert response.status_code == 422

def test_demo_summary():
    response = client.get("/api/demo/summary")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "token_states" in data
    assert "lookup_enabled" in data
    assert "reader_implemented" in data
