"""Module 3: ML Price Estimation using Random Forest Regressor."""

import json
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.core.config import get_settings
from app.ml.data_generator import (
    SYNTHETIC_DATASET_NOTICE,
    generate_synthetic_pricing_dataset,
    save_synthetic_datasets,
)

CATEGORICAL_FEATURES = [
    "service_category",
    "repair_complexity",
    "location_zone",
    "urgency",
    "time_of_service",
]
NUMERIC_FEATURES = ["estimated_duration"]

PRICE_MODEL_LIMITATIONS = [
    "Trained on an explicitly synthetic starter dataset calibrated to typical Delhi household service rates.",
    "Excludes physical hardware/spare part costs (e.g., new copper wiring coils, MCB units, ceiling fans, or inverter batteries).",
    "Actual cost may vary depending on concealed wiring accessibility, building height, or unexpected circuit faults found on-site.",
    "Always distinct from the electrician's final on-site quotation.",
]


class PriceEstimatorService:
    """Random Forest Regressor for transparent baseline INR price range estimation."""

    def __init__(self, artifacts_dir: Optional[Path] = None):
        settings = get_settings()
        self.artifacts_dir = Path(artifacts_dir or settings.ML_ARTIFACTS_DIR)
        self.model_path = self.artifacts_dir / "price_estimator.joblib"
        self.metrics_path = self.artifacts_dir / "price_estimator_metrics.json"
        self.pipeline: Optional[Pipeline] = None
        self.metrics: Dict = {}

    @staticmethod
    def _build_pipeline() -> Pipeline:
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
                ("num", "passthrough", NUMERIC_FEATURES),
            ]
        )
        return Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=140,
                        max_depth=12,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def train_and_evaluate(self, force: bool = True) -> Dict:
        """Train RandomForestRegressor on synthetic pricing data with an 80/20 train/test split."""
        if not force and self.model_path.exists() and self.metrics_path.exists():
            self.load()
            return self.metrics

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        save_synthetic_datasets(self.artifacts_dir)

        df = generate_synthetic_pricing_dataset(n_samples=640, seed=42)
        feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES
        X = df[feature_cols]
        y = df["price_inr"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )

        eval_pipeline = self._build_pipeline()
        eval_pipeline.fit(X_train, y_train)
        preds = eval_pipeline.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(root_mean_squared_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))

        # Fit final inference pipeline on all synthetic rows after recording held-out evaluation
        full_pipeline = self._build_pipeline()
        full_pipeline.fit(X, y)

        metrics = {
            "model_type": "RandomForestRegressor (OneHotEncoder + 140 trees)",
            "dataset_type": "synthetic_starter",
            "dataset_notice": SYNTHETIC_DATASET_NOTICE,
            "total_samples": int(len(df)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "test_mae_inr": round(mae, 2),
            "test_rmse_inr": round(rmse, 2),
            "test_r2_score": round(r2, 4),
            "features": feature_cols,
            "limitations": PRICE_MODEL_LIMITATIONS,
        }

        joblib.dump(full_pipeline, self.model_path)
        self.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        self.pipeline = full_pipeline
        self.metrics = metrics
        return metrics

    def load(self) -> None:
        """Load persisted Random Forest price model and metrics."""
        if not self.model_path.exists() or not self.metrics_path.exists():
            self.train_and_evaluate(force=True)
            return
        self.pipeline = joblib.load(self.model_path)
        self.metrics = json.loads(self.metrics_path.read_text(encoding="utf-8"))

    def ensure_loaded(self) -> None:
        """Ensure estimator is loaded in memory."""
        if self.pipeline is None:
            self.load()

    def estimate_price(
        self,
        service_category: str,
        repair_complexity: str = "medium",
        location_zone: str = "Central Delhi",
        urgency: str = "normal",
        time_of_service: str = "morning",
        estimated_duration: int = 45,
    ) -> Dict:
        """Predict base INR labour/inspection price and uncertainty interval."""
        self.ensure_loaded()
        assert self.pipeline is not None

        row = pd.DataFrame(
            [
                {
                    "service_category": service_category,
                    "repair_complexity": repair_complexity,
                    "location_zone": location_zone,
                    "urgency": urgency,
                    "time_of_service": time_of_service,
                    "estimated_duration": int(max(15, min(240, estimated_duration))),
                }
            ]
        )

        # Compute individual decision tree predictions to quantify interval width honestly
        transformed = self.pipeline.named_steps["preprocessor"].transform(row)
        rf: RandomForestRegressor = self.pipeline.named_steps["regressor"]
        tree_preds = np.array([tree.predict(transformed)[0] for tree in rf.estimators_])

        mean_pred = float(np.mean(tree_preds))
        p20 = float(np.percentile(tree_preds, 20))
        p80 = float(np.percentile(tree_preds, 80))

        base_price = int(round(max(180.0, mean_pred) / 10.0) * 10)
        lower = int(round(max(150.0, min(p20, base_price * 0.86)) / 10.0) * 10)
        upper = int(round(max(p80, base_price * 1.18) / 10.0) * 10)
        if lower > base_price:
            lower = max(150, base_price - 50)
        if upper < base_price:
            upper = base_price + 80

        return {
            "predicted_base_price_inr": base_price,
            "lower_estimate_inr": lower,
            "upper_estimate_inr": upper,
            "currency": "INR",
            "estimate_label": "AI Synthetic Model Estimate (Excludes Spare Parts)",
            "disclaimer": (
                "This is an AI baseline labour estimate trained on synthetic data — "
                "it is distinct from and does not replace the electrician's final quotation after inspection."
            ),
            "inputs_used": {
                "service_category": service_category,
                "repair_complexity": repair_complexity,
                "location_zone": location_zone,
                "urgency": urgency,
                "time_of_service": time_of_service,
                "estimated_duration_mins": int(row["estimated_duration"].iloc[0]),
            },
            "limitations": PRICE_MODEL_LIMITATIONS,
            "model_metrics_summary": {
                "model_type": self.metrics.get("model_type"),
                "test_mae_inr": self.metrics.get("test_mae_inr"),
                "test_r2_score": self.metrics.get("test_r2_score"),
            },
        }


_price_estimator_singleton: Optional[PriceEstimatorService] = None


def get_price_estimator() -> PriceEstimatorService:
    """Return process-wide cached PriceEstimatorService."""
    global _price_estimator_singleton
    if _price_estimator_singleton is None:
        _price_estimator_singleton = PriceEstimatorService()
        _price_estimator_singleton.ensure_loaded()
    return _price_estimator_singleton
