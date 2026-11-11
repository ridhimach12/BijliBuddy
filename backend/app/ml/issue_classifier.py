"""Module 1: Electrical Issue Classification using TF-IDF and Logistic Regression."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

from app.core.config import get_settings
from app.core.constants import CATEGORY_BY_NAME
from app.ml.data_generator import (
    SYNTHETIC_DATASET_NOTICE,
    generate_synthetic_issue_dataset,
    save_synthetic_datasets,
)
from app.services.safety import assess_electrical_hazard


class IssueClassifierService:
    """TF-IDF + LogisticRegression classifier for household electrical issues."""

    def __init__(self, artifacts_dir: Optional[Path] = None):
        settings = get_settings()
        self.artifacts_dir = Path(artifacts_dir or settings.ML_ARTIFACTS_DIR)
        self.model_path = self.artifacts_dir / "issue_classifier.joblib"
        self.metrics_path = self.artifacts_dir / "issue_classifier_metrics.json"
        self.pipeline: Optional[Pipeline] = None
        self.metrics: Dict = {}

    def train_and_evaluate(self, force: bool = True) -> Dict:
        """Train TF-IDF + Logistic Regression with template-grouped train/test split."""
        if not force and self.model_path.exists() and self.metrics_path.exists():
            self.load()
            return self.metrics

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        save_synthetic_datasets(self.artifacts_dir)

        df = generate_synthetic_issue_dataset(seed=42)
        # Hold out specific template_ids per category so variations never leak across splits
        test_mask = df["template_id"].apply(lambda tid: int(tid.split("::")[-1]) >= 14)
        train_df = df[~test_mask].reset_index(drop=True)
        test_df = df[test_mask].reset_index(drop=True)

        pipeline = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        lowercase=True,
                        sublinear_tf=True,
                        min_df=1,
                        max_features=3500,
                        stop_words="english",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=3.0,
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )

        pipeline.fit(train_df["description"], train_df["category"])
        test_preds = pipeline.predict(test_df["description"])

        acc = float(accuracy_score(test_df["category"], test_preds))
        macro_f1 = float(f1_score(test_df["category"], test_preds, average="macro"))
        report = classification_report(
            test_df["category"], test_preds, output_dict=True, zero_division=0
        )

        # Persist production inference model trained on train split (kept honest with test metrics)
        # Re-fit on full synthetic starter set only after evaluating held-out generalization,
        # or keep train-split model if desired. Refitting on full synthetic corpus gives richer
        # coverage for live demo queries while reporting strict held-out split metrics.
        full_pipeline = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        lowercase=True,
                        sublinear_tf=True,
                        min_df=1,
                        max_features=3500,
                        stop_words="english",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=3.0,
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        full_pipeline.fit(df["description"], df["category"])

        metrics = {
            "model_type": "TF-IDF + LogisticRegression",
            "dataset_type": "synthetic_starter",
            "dataset_notice": SYNTHETIC_DATASET_NOTICE,
            "total_samples": int(len(df)),
            "train_samples": int(len(train_df)),
            "test_samples": int(len(test_df)),
            "split_strategy": "Template-grouped holdout (4 unseen base templates per category)",
            "test_accuracy": round(acc, 4),
            "test_macro_f1": round(macro_f1, 4),
            "classes": list(full_pipeline.classes_),
            "per_class_metrics": {
                cls_name: {
                    "precision": round(float(report[cls_name]["precision"]), 4),
                    "recall": round(float(report[cls_name]["recall"]), 4),
                    "f1_score": round(float(report[cls_name]["f1-score"]), 4),
                    "support": int(report[cls_name]["support"]),
                }
                for cls_name in full_pipeline.classes_
                if cls_name in report
            },
        }

        joblib.dump(full_pipeline, self.model_path)
        self.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        self.pipeline = full_pipeline
        self.metrics = metrics
        return metrics

    def load(self) -> None:
        """Load persisted model and metrics, training if missing."""
        if not self.model_path.exists() or not self.metrics_path.exists():
            self.train_and_evaluate(force=True)
            return
        self.pipeline = joblib.load(self.model_path)
        self.metrics = json.loads(self.metrics_path.read_text(encoding="utf-8"))

    def ensure_loaded(self) -> None:
        """Ensure classifier is loaded in memory."""
        if self.pipeline is None:
            self.load()

    @staticmethod
    def infer_complexity_hint(description: str, category: str, urgency: str) -> str:
        """Infer default repair complexity hint from issue text and category."""
        text = description.lower()
        high_signals = [
            "rewiring", "burnt", "melted", "short circuit", "spark", "smoke",
            "main", "distribution box", "db box", "entire", "whole house", "24v", "heavy",
        ]
        low_signals = [
            "bulb", "tube light", "doorbell", "capacitor", "single switch",
            "regulator", "replace one", "holder",
        ]
        if urgency == "emergency" or any(sig in text for sig in high_signals):
            return "high"
        if any(sig in text for sig in low_signals):
            return "low"
        if category in ("Wiring", "Inverter", "MCB/circuit breaker"):
            return "medium"
        return "low" if category == "Lighting" else "medium"

    def predict(self, description: str, urgency: str = "normal") -> Dict:
        """Classify a free-text customer electrical issue and perform hazard safety checks."""
        self.ensure_loaded()
        assert self.pipeline is not None

        cleaned = (description or "").strip()
        if not cleaned:
            raise ValueError("Issue description cannot be empty.")

        probs = self.pipeline.predict_proba([cleaned])[0]
        classes = list(self.pipeline.classes_)
        ranked_indices = np.argsort(probs)[::-1]

        top_idx = int(ranked_indices[0])
        predicted_category = str(classes[top_idx])
        confidence = round(float(probs[top_idx]), 4)

        cat_meta = CATEGORY_BY_NAME.get(predicted_category, {})
        suggested_service_type = cat_meta.get(
            "suggested_service_type", f"{predicted_category} Inspection & Repair"
        )
        estimated_duration = int(cat_meta.get("estimated_duration_mins", 45))

        top_alternatives: List[Tuple[str, float]] = [
            (str(classes[int(i)]), round(float(probs[int(i)]), 4))
            for i in ranked_indices[:3]
        ]

        hazard_assessment = assess_electrical_hazard(cleaned, urgency=urgency)
        suggested_complexity = self.infer_complexity_hint(cleaned, predicted_category, urgency)

        return {
            "predicted_category": predicted_category,
            "confidence_score": confidence,
            "suggested_service_type": suggested_service_type,
            "suggested_complexity": suggested_complexity,
            "estimated_duration_mins": estimated_duration,
            "top_alternatives": [
                {"category": cat, "probability": prob} for cat, prob in top_alternatives
            ],
            "hazard_assessment": hazard_assessment,
            "dataset_notice": SYNTHETIC_DATASET_NOTICE,
            "model_metrics_summary": {
                "model_type": self.metrics.get("model_type"),
                "test_accuracy": self.metrics.get("test_accuracy"),
                "test_macro_f1": self.metrics.get("test_macro_f1"),
            },
        }


_classifier_singleton: Optional[IssueClassifierService] = None


def get_issue_classifier() -> IssueClassifierService:
    """Return process-wide cached IssueClassifierService."""
    global _classifier_singleton
    if _classifier_singleton is None:
        _classifier_singleton = IssueClassifierService()
        _classifier_singleton.ensure_loaded()
    return _classifier_singleton
