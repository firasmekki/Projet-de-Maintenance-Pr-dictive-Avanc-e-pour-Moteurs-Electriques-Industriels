"""
Standalone training script for Module 5 ML models.

Usage:
    python -m ml.trainer                        # retrain both models
    python -m ml.trainer --model anomaly        # anomaly detector only
    python -m ml.trainer --model fault          # fault classifier only
    python -m ml.trainer --data path/to/data.csv  # train from real CSV

CSV schema (when --data provided):
    temperature, vibration, current, voltage, power, load,
    current_ratio, power_factor,
    temperature_rolling_mean, vibration_rolling_mean,
    temperature_std, vibration_std,
    label   (fault class string or "Normal")
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ml.trainer")

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "ml/models")


def _load_csv(path: str):
    import pandas as pd

    df = pd.read_csv(path)
    feature_cols = [
        "temperature", "vibration", "current", "voltage", "power", "load",
        "current_ratio", "power_factor",
        "temperature_rolling_mean", "vibration_rolling_mean",
        "temperature_std", "vibration_std",
    ]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values if "label" in df.columns else None
    return X, y


def retrain_anomaly(X: np.ndarray) -> None:
    from app.services.ml.anomaly_detection_service import AnomalyDetectionService

    svc = AnomalyDetectionService()
    svc.retrain(X)
    logger.info("Anomaly detector retrained with %d real samples", len(X))


def retrain_fault(X: np.ndarray, y: np.ndarray) -> None:
    from sklearn.preprocessing import LabelEncoder
    import joblib

    from app.services.ml.fault_classification_service import FaultClassificationService, ENCODER_PATH

    svc = FaultClassificationService()
    encoder: LabelEncoder = joblib.load(ENCODER_PATH)
    y_encoded = encoder.transform(y)
    svc.retrain(X, y_encoded)
    logger.info("Fault classifier retrained with %d real samples", len(X))


def main() -> None:
    parser = argparse.ArgumentParser(description="ORBIT AI ML model trainer")
    parser.add_argument(
        "--model",
        choices=["anomaly", "fault", "all"],
        default="all",
        help="Which model to retrain",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to CSV training data (optional, uses synthetic data if omitted)",
    )
    args = parser.parse_args()

    if args.data:
        logger.info("Loading training data from %s", args.data)
        X, y = _load_csv(args.data)
        logger.info("Loaded %d samples, %d features", len(X), X.shape[1])
    else:
        logger.info("No --data provided — models will be retrained on synthetic data")
        X, y = None, None

    os.makedirs(MODEL_DIR, exist_ok=True)

    if args.model in ("anomaly", "all"):
        logger.info("=== Retraining anomaly detector ===")
        from app.services.ml.anomaly_detection_service import AnomalyDetectionService

        svc = AnomalyDetectionService()
        if X is not None:
            svc.retrain(X)
        else:
            # Force re-initialise which runs _fit_synthetic
            import os, importlib
            import ml.models
            for f in Path(MODEL_DIR).glob("anomaly_detector.pkl"):
                f.unlink()
            AnomalyDetectionService()
        logger.info("Anomaly detector: DONE")

    if args.model in ("fault", "all"):
        logger.info("=== Retraining fault classifier ===")
        from app.services.ml.fault_classification_service import FaultClassificationService

        if X is not None and y is not None:
            retrain_fault(X, y)
        else:
            for f in Path(MODEL_DIR).glob("fault_classifier.pkl"):
                f.unlink()
            for f in Path(MODEL_DIR).glob("label_encoder.pkl"):
                f.unlink()
            FaultClassificationService()
        logger.info("Fault classifier: DONE")

    logger.info("Training complete. Models saved to %s/", MODEL_DIR)


if __name__ == "__main__":
    main()
