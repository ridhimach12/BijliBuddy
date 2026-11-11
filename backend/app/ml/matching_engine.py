"""Module 2: Explainable Intelligent Electrician Matching Engine."""

import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from app.ml.reliability import ReliabilityMetricsInput, compute_reliability_score


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinates in kilometres."""
    earth_radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(earth_radius_km * c, 2)


def estimate_arrival_minutes(distance_km: float, urgency: str = "normal") -> int:
    """Estimate urban arrival time in minutes for Delhi traffic + dispatch prep."""
    avg_speed_kmh = 22.0 if urgency in ("urgent", "emergency") else 17.5
    prep_mins = 7 if urgency in ("urgent", "emergency") else 12
    travel_mins = (distance_km / avg_speed_kmh) * 60.0
    eta = int(round(prep_mins + travel_mins))
    return max(10, min(95, eta))


@dataclass
class MatchingWeights:
    """Configurable normalized feature weights (must sum to 1.0 for scoring within availability tier)."""

    distance: float = 0.25
    skill: float = 0.26
    rating: float = 0.16
    acceptance_rate: float = 0.12
    completion_rate: float = 0.12
    eta: float = 0.09

    def normalized(self) -> "MatchingWeights":
        total = (
            self.distance
            + self.skill
            + self.rating
            + self.acceptance_rate
            + self.completion_rate
            + self.eta
        )
        if total <= 0:
            return MatchingWeights()
        return MatchingWeights(
            distance=self.distance / total,
            skill=self.skill / total,
            rating=self.rating / total,
            acceptance_rate=self.acceptance_rate / total,
            completion_rate=self.completion_rate / total,
            eta=self.eta / total,
        )


@dataclass
class ElectricianCandidate:
    electrician_id: int
    user_id: int
    full_name: str
    phone: str
    locality: str
    zone: str
    latitude: float
    longitude: float
    service_radius_km: float
    experience_years: int
    is_available: bool
    working_hours_start: str
    working_hours_end: str
    verification_status: str
    base_visit_fee_inr: int
    skills: List[str]
    bio: str
    verified_completed_jobs: int
    accepted_jobs: int
    rejected_jobs: int
    cancelled_jobs: int
    average_rating: Optional[float]
    review_count: int
    on_time_jobs: int
    on_time_evaluated_jobs: int


def rank_electricians(
    candidates: List[ElectricianCandidate],
    customer_lat: float,
    customer_lon: float,
    target_category: str,
    urgency: str = "normal",
    top_k: int = 5,
    weights: Optional[MatchingWeights] = None,
) -> Dict:
    """Rank eligible electricians using normalized features and explainable weights.

    HARD SAFETY/FAIRNESS RULE:
    Unavailable electricians are NEVER ranked above available candidates.
    """
    w = (weights or MatchingWeights()).normalized()
    scored_items: List[Dict] = []

    for c in candidates:
        distance_km = haversine_distance_km(customer_lat, customer_lon, c.latitude, c.longitude)
        within_radius = distance_km <= max(1.0, c.service_radius_km)
        eta_mins = estimate_arrival_minutes(distance_km, urgency=urgency)

        # Normalized distance score (1.0 at 0km, decays smoothly with service radius & 15km cap)
        ref_radius = max(c.service_radius_km, 8.0)
        distance_norm = max(0.0, 1.0 - (distance_km / (ref_radius * 1.8)))
        if not within_radius:
            distance_norm *= 0.65

        # Normalized skill compatibility (exact match = 1.0, General maintenance partial, else base)
        has_exact_skill = target_category in c.skills
        has_general = "General electrical maintenance" in c.skills
        if has_exact_skill:
            skill_norm = 1.0
        elif has_general:
            skill_norm = 0.55
        elif len(c.skills) > 0:
            skill_norm = 0.25
        else:
            skill_norm = 0.10

        # Reliability + Bayesian smoothed rating/acceptance/completion
        is_verified = c.verification_status == "verified"
        reliability = compute_reliability_score(
            ReliabilityMetricsInput(
                verified_completed_jobs=c.verified_completed_jobs,
                accepted_jobs=c.accepted_jobs,
                rejected_jobs=c.rejected_jobs,
                cancelled_jobs=c.cancelled_jobs,
                average_rating=c.average_rating,
                review_count=c.review_count,
                on_time_jobs=c.on_time_jobs,
                on_time_evaluated_jobs=c.on_time_evaluated_jobs,
                is_admin_verified=is_verified,
            )
        )

        rating_norm = max(0.0, min(1.0, (reliability["smoothed_rating"] - 1.0) / 4.0))
        acceptance_norm = reliability["smoothed_acceptance_rate"]
        completion_norm = reliability["smoothed_completion_rate"]
        eta_norm = max(0.0, min(1.0, 1.0 - ((eta_mins - 10.0) / 80.0)))

        raw_weighted = (
            w.distance * distance_norm
            + w.skill * skill_norm
            + w.rating * rating_norm
            + w.acceptance_rate * acceptance_norm
            + w.completion_rate * completion_norm
            + w.eta * eta_norm
        )
        # Small boost for Admin-verified credentials without overriding availability
        if is_verified:
            raw_weighted = min(1.0, raw_weighted + 0.03)

        # Availability penalty if unavailable (plus strict tuple sort guarantees available first)
        effective_score = raw_weighted if c.is_available else raw_weighted * 0.45
        match_score_pct = round(effective_score * 100.0, 1)

        # Build human-readable recommendation explanation
        reasons: List[str] = []
        if c.is_available:
            reasons.append(f"Currently available ({c.working_hours_start}–{c.working_hours_end})")
        else:
            reasons.append("Currently marked unavailable — ranked below available electricians")

        if has_exact_skill:
            reasons.append(f"Verified skill match in {target_category}")
        elif has_general:
            reasons.append(f"Covers General electrical maintenance (secondary fit for {target_category})")
        else:
            reasons.append(f"Primary skills: {', '.join(c.skills) or 'General'}")

        if within_radius:
            reasons.append(f"Nearby at {distance_km} km in {c.locality} (within {c.service_radius_km:.0f} km radius)")
        else:
            reasons.append(f"Located {distance_km} km away in {c.locality} (outside {c.service_radius_km:.0f} km radius)")

        rating_str = (
            f"{c.average_rating:.1f}★ ({c.review_count} reviews)"
            if c.average_rating is not None and c.review_count > 0
            else f"New electrician (Bayesian baseline {reliability['smoothed_rating']:.1f}★)"
        )
        reasons.append(
            f"Reliability {reliability['reliability_score']}/100 • {rating_str} • ETA ~{eta_mins} mins"
        )
        if is_verified:
            reasons.append("Admin-verified credentials")
        else:
            reasons.append(f"Credential verification status: {c.verification_status}")

        scored_items.append(
            {
                "electrician_id": c.electrician_id,
                "user_id": c.user_id,
                "full_name": c.full_name,
                "locality": c.locality,
                "zone": c.zone,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "distance_km": distance_km,
                "within_service_radius": within_radius,
                "service_radius_km": c.service_radius_km,
                "experience_years": c.experience_years,
                "match_score": match_score_pct,
                "skills_match_pct": round(skill_norm * 100.0, 1),
                "matched_skills": c.skills,
                "has_exact_skill": has_exact_skill,
                "is_available": c.is_available,
                "availability_label": "Available Now" if c.is_available else "Currently Unavailable",
                "working_hours": f"{c.working_hours_start} - {c.working_hours_end}",
                "verification_status": c.verification_status,
                "is_verified": is_verified,
                "rating": round(c.average_rating, 2) if c.average_rating is not None else None,
                "smoothed_rating": reliability["smoothed_rating"],
                "review_count": c.review_count,
                "acceptance_rate": round(acceptance_norm * 100.0, 1),
                "completion_rate": round(completion_norm * 100.0, 1),
                "reliability_score": reliability["reliability_score"],
                "reliability_tier": reliability["confidence_tier"],
                "estimated_arrival_mins": eta_mins,
                "base_visit_fee_inr": c.base_visit_fee_inr,
                "bio": c.bio,
                "explanation_summary": " • ".join(reasons[:3]),
                "explanation_reasons": reasons,
                "feature_breakdown": {
                    "distance_norm": round(distance_norm, 3),
                    "skill_norm": round(skill_norm, 3),
                    "rating_norm": round(rating_norm, 3),
                    "acceptance_norm": round(acceptance_norm, 3),
                    "completion_norm": round(completion_norm, 3),
                    "eta_norm": round(eta_norm, 3),
                    "weights_used": asdict(w),
                },
            }
        )

    # Strict sort: Available candidates ALWAYS precede unavailable candidates,
    # then within-radius eligibility, then weighted match score descending.
    scored_items.sort(
        key=lambda item: (
            1 if item["is_available"] else 0,
            1 if item["within_service_radius"] else 0,
            item["match_score"],
        ),
        reverse=True,
    )

    eligible_top = scored_items[:top_k]

    return {
        "target_category": target_category,
        "total_candidates_evaluated": len(candidates),
        "weights_config": asdict(w),
        "recommendations": eligible_top,
    }
