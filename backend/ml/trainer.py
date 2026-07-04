"""
Standalone model trainer for ORBIT AI Module 5.

Usage:
    # Retrain both models on synthetic data (default):
    python -m ml.trainer

    # Retrain anomaly detector only:
    python -m ml.trainer --model anomaly

    # Retrain fault classifier only:
    python -m ml.trainer --model fault

    # Retrain with real labelled data from CSV:
    python -m ml.trainer --data path/to/data.csv

Expected CSV columns (13 features + optional label):
    temperature, vibration, current, voltage, power, load,
    power_factor, thd, current_ratio,
    temperature_mean, vibration_mean, temperature_std, vibration_std,
    label   (fault class string, e.g. "Normal", "Bearing Wear", ...)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ml.trainer")

_MODEL_DIR = Path(os.environ.get("ML_MODEL_DIR", "ml/models"))
_FEATURE_COLS = [
    "temperature", "vibration", "current", "voltage", "power", "load",
    "power_factor", "thd", "current_ratio",
    "temperature_mean", "vibration_mean", "temperature_std", "vibration_std",
]


def _load_csv(path: str):
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for --data. Install it: pip install pandas")
        sys.exit(1)

    import numpy as np

    df = pd.read_csv(path)
    missing = [c for c in _FEATURE_COLS if c not in df.columns]
    if missing:
        logger.error("CSV is missing columns: %s", missing)
        sys.exit(1)

    X = df[_FEATURE_COLS].values.astype(np.float32)
    y = df["label"].values if "label" in df.columns else None
    logger.info("Loaded %d samples from %s", len(X), path)
    return X, y


def _retrain_anomaly(X=None) -> None:
    from app.services.ml.anomaly_detection_service import AnomalyDetectionService

    svc = AnomalyDetectionService()
    if X is not None:
        svc.retrain(X)
        logger.info("Anomaly detector retrained with real data (%d samples)", len(X))
    else:
        # Force re-initialise: delete existing model so synthetic fit runs
        model_path = _MODEL_DIR / "anomaly_detector.pkl"
        if model_path.exists():
            model_path.unlink()
            logger.info("Deleted existing anomaly model to force re-fit")
        AnomalyDetectionService()
        logger.info("Anomaly detector retrained on synthetic data")


def _retrain_fault(X=None, y=None) -> None:
    import joblib
    from sklearn.preprocessing import LabelEncoder

    from app.services.ml.fault_classification_service import FaultClassificationService

    if X is not None and y is not None:
        svc = FaultClassificationService()
        encoder: LabelEncoder = joblib.load(_MODEL_DIR / "label_encoder.pkl")
        y_encoded = encoder.transform(y)
        svc.retrain(X, y_encoded)
        logger.info("Fault classifier retrained with real data (%d samples)", len(X))
    else:
        for fname in ("fault_classifier.pkl", "label_encoder.pkl"):
            p = _MODEL_DIR / fname
            if p.exists():
                p.unlink()
                logger.info("Deleted %s to force re-fit", fname)
        FaultClassificationService()
        logger.info("Fault classifier retrained on synthetic data")


def main() -> None:
    parser = argparse.ArgumentParser(description="ORBIT AI ML model trainer")
    parser.add_argument(
        "--model",
        choices=["anomaly", "fault", "all"],
        default="all",
        help="Which model(s) to retrain (default: all)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to CSV with labelled training data (optional)",
    )
    args = parser.parse_args()

    _MODEL_DIR.mkdir(parents=True, exist_ok=True)

    X, y = (None, None)
    if args.data:
        X, y = _load_csv(args.data)

    if args.model in ("anomaly", "all"):
        logger.info("=== Retraining anomaly detector ===")
        _retrain_anomaly(X)

    if args.model in ("fault", "all"):
        logger.info("=== Retraining fault classifier ===")
        _retrain_fault(X, y)

    logger.info("Training complete. Models saved to %s/", _MODEL_DIR)


if __name__ == "__main__":
    main()
