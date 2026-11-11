"""Unit tests for Module 1: Electrical Issue Classification & Safety Hazard Detection."""

from app.core.constants import CATEGORY_NAMES
from app.ml.issue_classifier import IssueClassifierService


def test_issue_classifier_training_and_metrics(tmp_path):
    service = IssueClassifierService(artifacts_dir=tmp_path)
    metrics = service.train_and_evaluate(force=True)

    assert metrics["dataset_type"] == "synthetic_starter"
    assert metrics["train_samples"] > 0
    assert metrics["test_samples"] > 0
    assert metrics["test_accuracy"] >= 0.75
    assert metrics["test_macro_f1"] >= 0.70
    assert set(metrics["classes"]) == set(CATEGORY_NAMES)


def test_issue_classifier_predictions_and_safety():
    service = IssueClassifierService()
    service.ensure_loaded()

    res_fan = service.predict("Bedroom ceiling fan wobbling and running very slowly")
    assert res_fan["predicted_category"] == "Fan installation/repair"
    assert 0.0 < res_fan["confidence_score"] <= 1.0
    assert "Fan" in res_fan["suggested_service_type"]

    res_mcb = service.predict("Main MCB trips repeatedly every time geyser turns on")
    assert res_mcb["predicted_category"] == "MCB/circuit breaker"

    res_hazard = service.predict("Switchboard is sparking with burning smell and smoke", urgency="emergency")
    assert res_hazard["hazard_assessment"]["hazard_detected"] is True
    assert res_hazard["hazard_assessment"]["severity"] == "critical"
    assert any("112" in line for line in res_hazard["hazard_assessment"]["safety_instructions"])
    assert "NOT diagnose" in res_hazard["hazard_assessment"]["image_disclaimer"]
