"""Module 5: Explainable Electrician Reliability Score with Bayesian smoothing."""

import math
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ReliabilityMetricsInput:
    verified_completed_jobs: int
    accepted_jobs: int
    rejected_jobs: int
    cancelled_jobs: int
    average_rating: Optional[float]
    review_count: int
    on_time_jobs: int
    on_time_evaluated_jobs: int
    is_admin_verified: bool


def compute_reliability_score(metrics: ReliabilityMetricsInput) -> Dict:
    """Compute an explainable 0-100 reliability score using Bayesian smoothing.

    New electricians with little or zero history are pulled toward fair platform priors
    rather than receiving zero scores.
    """
    # Platform Bayesian priors (neutral-positive starting baseline for new workers)
    prior_rating = 4.2
    prior_rating_weight = 5.0

    # 1. Smoothed customer rating (0..1)
    if metrics.review_count > 0 and metrics.average_rating is not None:
        smoothed_rating = (
            metrics.review_count * metrics.average_rating + prior_rating_weight * prior_rating
        ) / (metrics.review_count + prior_rating_weight)
    else:
        smoothed_rating = prior_rating
    rating_norm = max(0.0, min(1.0, (smoothed_rating - 1.0) / 4.0))

    # 2. Smoothed acceptance rate: Beta(alpha=4.0, beta=1.0) -> prior 0.80
    total_responses = max(0, metrics.accepted_jobs + metrics.rejected_jobs)
    smoothed_acceptance = (metrics.accepted_jobs + 4.0) / (total_responses + 5.0)

    # 3. Smoothed completion / non-cancellation rate: Beta(alpha=4.5, beta=0.5) -> prior 0.90
    total_outcomes = max(0, metrics.verified_completed_jobs + metrics.cancelled_jobs)
    smoothed_completion = (metrics.verified_completed_jobs + 4.5) / (total_outcomes + 5.0)
    raw_cancellation_rate = (
        round(metrics.cancelled_jobs / total_outcomes, 4) if total_outcomes > 0 else 0.0
    )

    # 4. Smoothed on-time rate: Beta(alpha=4.2, beta=0.8) -> prior 0.84
    smoothed_on_time = (metrics.on_time_jobs + 4.2) / (
        max(0, metrics.on_time_evaluated_jobs) + 5.0
    )

    # 5. Verified completed volume maturity bonus (gentle logarithmic ramp up to 25 jobs)
    experience_signal = min(1.0, math.log1p(max(0, metrics.verified_completed_jobs)) / math.log1p(25))

    # Weighted score out of 96 + 4 points strictly for Admin-verified credential status
    base_score = (
        30.0 * rating_norm
        + 20.0 * smoothed_acceptance
        + 22.0 * smoothed_completion
        + 16.0 * smoothed_on_time
        + 8.0 * experience_signal
    )
    verification_bonus = 4.0 if metrics.is_admin_verified else 0.0
    total_score = round(max(0.0, min(100.0, base_score + verification_bonus)), 1)

    if metrics.verified_completed_jobs < 5:
        confidence_tier = "Provisional (New Electrician)"
        fairness_note = (
            "Bayesian prior smoothing applied because completed jobs < 5, "
            "ensuring new electricians are evaluated fairly without cold-start penalty."
        )
    elif metrics.verified_completed_jobs < 15:
        confidence_tier = "Growing Track Record"
        fairness_note = "Score blends observed job history with moderate Bayesian smoothing."
    else:
        confidence_tier = "Established Track Record"
        fairness_note = "Score is predominantly driven by verified completed job history."

    return {
        "reliability_score": total_score,
        "confidence_tier": confidence_tier,
        "fairness_note": fairness_note,
        "smoothed_rating": round(smoothed_rating, 2),
        "raw_average_rating": round(metrics.average_rating, 2) if metrics.average_rating is not None else None,
        "review_count": metrics.review_count,
        "verified_completed_jobs": metrics.verified_completed_jobs,
        "smoothed_acceptance_rate": round(smoothed_acceptance, 3),
        "smoothed_completion_rate": round(smoothed_completion, 3),
        "raw_cancellation_rate": raw_cancellation_rate,
        "smoothed_on_time_rate": round(smoothed_on_time, 3),
        "is_admin_verified": metrics.is_admin_verified,
        "breakdown": [
            {
                "factor": "Customer Rating (Bayesian Smoothed)",
                "weight_pct": 30,
                "normalized_value": round(rating_norm, 3),
                "points_earned": round(30.0 * rating_norm, 1),
            },
            {
                "factor": "Completion & Non-Cancellation Discipline",
                "weight_pct": 22,
                "normalized_value": round(smoothed_completion, 3),
                "points_earned": round(22.0 * smoothed_completion, 1),
            },
            {
                "factor": "Request Acceptance Rate",
                "weight_pct": 20,
                "normalized_value": round(smoothed_acceptance, 3),
                "points_earned": round(20.0 * smoothed_acceptance, 1),
            },
            {
                "factor": "On-Time Completion Rate",
                "weight_pct": 16,
                "normalized_value": round(smoothed_on_time, 3),
                "points_earned": round(16.0 * smoothed_on_time, 1),
            },
            {
                "factor": "Verified Job Volume Maturity",
                "weight_pct": 8,
                "normalized_value": round(experience_signal, 3),
                "points_earned": round(8.0 * experience_signal, 1),
            },
            {
                "factor": "Admin Credential Verification",
                "weight_pct": 4,
                "normalized_value": 1.0 if metrics.is_admin_verified else 0.0,
                "points_earned": verification_bonus,
            },
        ],
    }
