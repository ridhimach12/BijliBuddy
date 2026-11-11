"""CLI script to train and evaluate BijliBuddy ML models on synthetic starter datasets."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.issue_classifier import IssueClassifierService
from app.ml.price_estimator import PriceEstimatorService


def main() -> None:
    print("Training Module 1: Electrical Issue Classifier (TF-IDF + LogisticRegression)...")
    classifier = IssueClassifierService()
    clf_metrics = classifier.train_and_evaluate(force=True)
    print(json.dumps({
        "model": clf_metrics["model_type"],
        "dataset": clf_metrics["dataset_type"],
        "train_samples": clf_metrics["train_samples"],
        "test_samples": clf_metrics["test_samples"],
        "test_accuracy": clf_metrics["test_accuracy"],
        "test_macro_f1": clf_metrics["test_macro_f1"],
    }, indent=2))

    print("\nTraining Module 3: ML Price Estimator (RandomForestRegressor)...")
    pricer = PriceEstimatorService()
    price_metrics = pricer.train_and_evaluate(force=True)
    print(json.dumps({
        "model": price_metrics["model_type"],
        "dataset": price_metrics["dataset_type"],
        "train_samples": price_metrics["train_samples"],
        "test_samples": price_metrics["test_samples"],
        "test_mae_inr": price_metrics["test_mae_inr"],
        "test_rmse_inr": price_metrics["test_rmse_inr"],
        "test_r2_score": price_metrics["test_r2_score"],
    }, indent=2))


if __name__ == "__main__":
    main()
