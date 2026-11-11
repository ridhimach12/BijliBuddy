"""Unit tests for Module 3: ML Price Estimation (Random Forest Regressor)."""

from app.ml.price_estimator import PriceEstimatorService


def test_price_estimator_training_and_metrics(tmp_path):
    service = PriceEstimatorService(artifacts_dir=tmp_path)
    metrics = service.train_and_evaluate(force=True)

    assert metrics["dataset_type"] == "synthetic_starter"
    assert metrics["train_samples"] > 0
    assert metrics["test_samples"] > 0
    assert metrics["test_r2_score"] >= 0.75
    assert metrics["test_mae_inr"] < 120.0


def test_price_estimator_range_and_urgency_scaling():
    service = PriceEstimatorService()
    service.ensure_loaded()

    normal = service.estimate_price(
        service_category="Switchboard",
        repair_complexity="low",
        location_zone="East Delhi",
        urgency="normal",
        time_of_service="morning",
        estimated_duration=35,
    )
    emergency = service.estimate_price(
        service_category="Wiring",
        repair_complexity="high",
        location_zone="South Delhi",
        urgency="emergency",
        time_of_service="night",
        estimated_duration=120,
    )

    assert normal["lower_estimate_inr"] <= normal["predicted_base_price_inr"] <= normal["upper_estimate_inr"]
    assert emergency["lower_estimate_inr"] <= emergency["predicted_base_price_inr"] <= emergency["upper_estimate_inr"]
    assert emergency["predicted_base_price_inr"] > normal["predicted_base_price_inr"]
    assert "final quotation" in emergency["disclaimer"]
