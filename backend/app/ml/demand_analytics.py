"""Module 4: Demand Analytics & Baseline Statistical Demand Forecasting."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import numpy as np
import pandas as pd

from app.core.constants import DAYS_OF_WEEK, TIME_SLOTS

FORECAST_MODEL_LIMITATIONS = [
    "Baseline statistical forecasting model (recency-weighted moving average + day-of-week seasonal indices) designed for small/early-stage marketplace datasets.",
    "Uses Poisson empirical intervals; actual demand spikes during Delhi summer peak AC loads, monsoon waterlogging, or grid faults require external weather and DISCOM outage features.",
    "Assumes short-term stationarity over the next 7 days and treats all localities proportionally based on historical booking share.",
]


def _empty_analytics_response(forecast_horizon_days: int) -> Dict:
    today = datetime.now(timezone.utc).date()
    return {
        "total_analyzed_bookings": 0,
        "by_locality": [],
        "by_day_of_week": [{"day": d, "bookings": 0} for d in DAYS_OF_WEEK],
        "by_time_slot": [{"time_slot": s, "bookings": 0} for s in TIME_SLOTS],
        "by_category": [],
        "daily_trend": [],
        "forecast_next_days": [
            {
                "date": (today + timedelta(days=i + 1)).isoformat(),
                "day_name": DAYS_OF_WEEK[(today + timedelta(days=i + 1)).weekday()],
                "expected_bookings": 0.0,
                "lower_bound": 0.0,
                "upper_bound": 1.0,
            }
            for i in range(forecast_horizon_days)
        ],
        "forecast_by_locality": [],
        "forecast_by_category": [],
        "model_info": {
            "model_type": "Baseline Weighted Moving Average + Day-of-Week Seasonal Index",
            "dataset_size": 0,
            "limitations": FORECAST_MODEL_LIMITATIONS,
        },
    }


def analyze_and_forecast_demand(
    booking_records: List[Dict],
    forecast_horizon_days: int = 7,
) -> Dict:
    """Aggregate booking demand across locality, day, time slot, and category,
    and forecast short-term future demand with explicit uncertainty bounds.
    """
    if not booking_records:
        return _empty_analytics_response(forecast_horizon_days)

    df = pd.DataFrame(booking_records)
    df["created_dt"] = pd.to_datetime(df["created_at"], format="ISO8601", utc=True)
    df["date"] = df["created_dt"].dt.date
    df["day_idx"] = df["created_dt"].dt.weekday
    df["day_name"] = df["day_idx"].apply(lambda idx: DAYS_OF_WEEK[int(idx)])

    total_count = int(len(df))

    # 1. Breakdown by locality
    loc_counts = (
        df.groupby("locality")
        .size()
        .reset_index(name="bookings")
        .sort_values("bookings", ascending=False)
    )
    by_locality = [
        {
            "locality": str(row["locality"]),
            "bookings": int(row["bookings"]),
            "share_pct": round(float(row["bookings"]) / total_count * 100.0, 1),
        }
        for _, row in loc_counts.iterrows()
    ]

    # 2. Breakdown by day of week (Monday..Sunday)
    dow_counts = df.groupby("day_name").size().to_dict()
    by_day_of_week = [
        {"day": d, "bookings": int(dow_counts.get(d, 0))} for d in DAYS_OF_WEEK
    ]

    # 3. Breakdown by time slot
    slot_counts = df.groupby("time_slot").size().to_dict()
    by_time_slot = [
        {"time_slot": slot, "bookings": int(slot_counts.get(slot, 0))}
        for slot in TIME_SLOTS
    ]

    # 4. Breakdown by service category
    cat_counts = (
        df.groupby("category")
        .size()
        .reset_index(name="bookings")
        .sort_values("bookings", ascending=False)
    )
    by_category = [
        {
            "category": str(row["category"]),
            "bookings": int(row["bookings"]),
            "share_pct": round(float(row["bookings"]) / total_count * 100.0, 1),
        }
        for _, row in cat_counts.iterrows()
    ]

    # 5. Daily time series over observed date range
    min_date = df["date"].min()
    max_date = df["date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D").date
    daily_map = df.groupby("date").size().to_dict()

    daily_series = [
        {"date": d.isoformat(), "bookings": int(daily_map.get(d, 0))} for d in all_dates
    ]

    # Baseline Statistical Forecast:
    # Combine overall daily mean and recent 7-day weighted moving average (60% recent, 40% overall)
    counts_arr = np.array([item["bookings"] for item in daily_series], dtype=float)
    overall_daily_mean = float(np.mean(counts_arr)) if len(counts_arr) > 0 else 1.0
    recent_window = counts_arr[-min(7, len(counts_arr)) :]
    weights = np.arange(1, len(recent_window) + 1, dtype=float)
    recent_wma = float(np.sum(recent_window * weights) / np.sum(weights))
    baseline_daily_rate = max(0.25, 0.60 * recent_wma + 0.40 * overall_daily_mean)

    # Day-of-week seasonal multipliers with Laplace smoothing so rare days don't collapse to 0
    avg_dow = (total_count + 7.0) / 7.0
    dow_multipliers = {
        idx: ((dow_counts.get(DAYS_OF_WEEK[idx], 0) + 1.0) / avg_dow)
        for idx in range(7)
    }

    last_date = max_date
    forecast_next_days: List[Dict] = []
    total_expected_horizon = 0.0

    for offset in range(1, forecast_horizon_days + 1):
        target_date = last_date + timedelta(days=offset)
        dow = target_date.weekday()
        expected = round(baseline_daily_rate * dow_multipliers[dow], 2)
        # 90% Poisson normal approximation interval
        margin = 1.64 * np.sqrt(max(0.25, expected))
        lower = round(max(0.0, expected - margin), 2)
        upper = round(expected + margin, 2)
        total_expected_horizon += expected
        forecast_next_days.append(
            {
                "date": target_date.isoformat(),
                "day_name": DAYS_OF_WEEK[dow],
                "expected_bookings": expected,
                "lower_bound": lower,
                "upper_bound": upper,
            }
        )

    # Expected weekly demand per top locality & category (Laplace smoothed share)
    n_locs = max(1, len(by_locality))
    forecast_by_locality = [
        {
            "locality": item["locality"],
            "expected_next_7_days": round(
                total_expected_horizon * ((item["bookings"] + 0.5) / (total_count + 0.5 * n_locs)),
                1,
            ),
        }
        for item in by_locality[:8]
    ]

    n_cats = max(1, len(by_category))
    forecast_by_category = [
        {
            "category": item["category"],
            "expected_next_7_days": round(
                total_expected_horizon * ((item["bookings"] + 0.5) / (total_count + 0.5 * n_cats)),
                1,
            ),
        }
        for item in by_category
    ]

    return {
        "total_analyzed_bookings": total_count,
        "by_locality": by_locality,
        "by_day_of_week": by_day_of_week,
        "by_time_slot": by_time_slot,
        "by_category": by_category,
        "daily_trend": daily_series[-30:],  # last 30 days for crisp charting
        "forecast_next_days": forecast_next_days,
        "forecast_by_locality": forecast_by_locality,
        "forecast_by_category": forecast_by_category,
        "model_info": {
            "model_type": "Baseline Weighted Moving Average + Day-of-Week Seasonal Index",
            "dataset_size": total_count,
            "observed_days": len(daily_series),
            "baseline_daily_rate": round(baseline_daily_rate, 2),
            "expected_next_7_days_total": round(total_expected_horizon, 1),
            "limitations": FORECAST_MODEL_LIMITATIONS,
        },
    }
