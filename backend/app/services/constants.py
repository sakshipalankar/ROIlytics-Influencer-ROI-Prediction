"""Shared constants for ROIlytics — categories, encodings, and benchmarks."""
from __future__ import annotations

# All 10 industry categories
# Original 6 keep codes 0-5 for best_model.pkl compatibility; 4 new have codes 6-9
CATEGORY_MAP: dict[str, int] = {
    "Fitness": 0,
    "Fashion": 1,
    "Tech": 2,
    "Food": 3,
    "Travel": 4,
    "Lifestyle": 5,
    "Beauty": 6,
    "Gaming": 7,
    "Finance": 8,
    "Education": 9,
}

EXTRAPOLATED_CATEGORIES: set[str] = {"Beauty", "Gaming", "Finance", "Education"}

BUCKET_MAP: dict[str, int] = {
    "Nano": 0,
    "Micro": 1,
    "Macro": 2,
    "Mega": 3,
}

CATEGORY_ER_BENCHMARKS: dict[str, float] = {
    "Fitness":   0.055,
    "Fashion":   0.045,
    "Tech":      0.038,
    "Food":      0.052,
    "Travel":    0.042,
    "Lifestyle": 0.048,
    "Beauty":    0.056,
    "Gaming":    0.040,
    "Finance":   0.033,
    "Education": 0.036,
}

BUDGET_TIER_MAP: dict[tuple[int, int], str] = {
    (0,          2_000):       "Nano",
    (2_000,      15_000):      "Micro",
    (15_000,     100_000):     "Macro",
    (100_000,    999_999_999): "Mega",
}

CATEGORIES: list[str] = list(CATEGORY_MAP.keys())
CATEGORY_ENCODING = CATEGORY_MAP
CATEGORY_BENCHMARKS = CATEGORY_ER_BENCHMARKS

# Known brand/company accounts to exclude from creator rankings by default
BRAND_ACCOUNTS: set[str] = {
    "nike", "adidas", "myntra", "zomato",
    "mysmartprice", "91mobiles", "digit.in", "houseofmisu"
}


