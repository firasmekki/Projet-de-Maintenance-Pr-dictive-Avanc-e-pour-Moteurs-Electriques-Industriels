import logging
import os
from typing import Dict, List, Optional

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.schemas.prediction import FaultClassificationResult
from app.services.ml.feature_engineering import MotorFeatures

logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "ml/models")
MODEL_PATH = os.path.join(MODEL_DIR, "fault_classifier.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")

FAULT_CLASSES: List[str] = [
    "Normal",
    "Bearing Wear",
    "Misalignment",
    "Unbalance",
    "Rotor Fault",
    "Insulation Fault",
    "Overload",
]

RANDOM_STATE = 42
SAMPLES_PER_CLASS = 400


class FaultClassificationService:
    """Random Forest multi-class fault classifier for electric motors."""

    MODEL_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._encoder: Optional[LabelEncoder] = None
        self._initialise()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
            try:
                self._pipeline = joblib.load(MODEL_PATH)
                self._encoder = joblib.load(ENCODER_PATH)
                logger.info("Fault classifier loaded from %s", MODEL_PATH)
                return
            except Exception as exc:
                logger.warning("Could not load classifier (%s) — retraining", exc)

        self._encoder = LabelEncoder()
        self._encoder.fit(FAULT_CLASSES)
        self._pipeline = self._build_pipeline()
        self._fit_synthetic()

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=10,
                        min_samples_split=5,
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    # ------------------------------------------------------------------
    # Synthetic training data — domain-knowledge-based fault signatures
    # ------------------------------------------------------------------

    _FAULT_PROFILES: Dict[str, Dict] = {
        "Normal":           {"temp": 65,  "vib": 3.0,  "cur": 15.0, "volt": 380, "pwr": 5500, "load": 75, "cr": 0.85, "pf": 0.87, "ts": 2.0, "vs": 0.3},
        "Bearing Wear":     {"temp": 78,  "vib": 9.5,  "cur": 15.5, "volt": 380, "pwr": 5600, "load": 76, "cr": 0.87, "pf": 0.86, "ts": 3.0, "vs": 1.5},
        "Misalignment":     {"temp": 82,  "vib": 12.5, "cur": 18.0, "volt": 375, "pwr": 6200, "load": 82, "cr": 1.10, "pf": 0.84, "ts": 3.5, "vs": 2.0},
        "Unbalance":        {"temp": 71,  "vib": 7.5,  "cur": 16.5, "volt": 379, "pwr": 5800, "load": 78, "cr": 0.95, "pf": 0.86, "ts": 2.5, "vs": 1.2},
        "Rotor Fault":      {"temp": 88,  "vib": 5.0,  "cur": 22.0, "volt": 376, "pwr": 7200, "load": 85, "cr": 1.35, "pf": 0.82, "ts": 4.0, "vs": 0.6},
        "Insulation Fault": {"temp": 95,  "vib": 4.5,  "cur": 20.0, "volt": 350, "pwr": 6800, "load": 80, "cr": 1.20, "pf": 0.72, "ts": 5.0, "vs": 0.5},
        "Overload":         {"temp": 85,  "vib": 5.5,  "cur": 24.0, "volt": 378, "pwr": 8500, "load": 95, "cr": 1.50, "pf": 0.85, "ts": 3.5, "vs": 0.7},
    }

    _FAULT_NOISE: Dict[str, List[float]] = {
        "Normal":           [5, 0.5, 2, 8, 300, 8, 0.04, 0.02, 5, 0.5, 0.4, 0.08],
        "Bearing Wear":     [6, 2.5, 2, 8, 300, 8, 0.05, 0.03, 6, 2.5, 1.0, 0.5],
        "Misalignment":     [5, 3.0, 2.5, 8, 400, 10, 0.08, 0.04, 5, 3.0, 1.5, 0.7],
        "Unbalance":        [5, 2.0, 2, 8, 300, 8, 0.06, 0.03, 5, 2.0, 0.8, 0.4],
        "Rotor Fault":      [6, 1.5, 3, 10, 500, 10, 0.10, 0.04, 6, 1.5, 1.2, 0.3],
        "Insulation Fault": [7, 1.5, 3, 20, 500, 10, 0.10, 0.05, 7, 1.5, 2.0, 0.3],
        "Overload":         [6, 2.0, 3, 8, 600, 5, 0.10, 0.04, 6, 2.0, 1.5, 0.4],
    }

    def _generate_class_samples(self, fault: str, n: int, rng: np.random.Generator) -> np.ndarray:
        p = self._FAULT_PROFILES[fault]
        base = np.array(
            [p["temp"], p["vib"], p["cur"], p["volt"], p["pwr"],
             p["load"], p["cr"], p["pf"], p["temp"], p["vib"], p["ts"], p["vs"]],
            dtype=np.float32,
        )
        noise_scale = np.array(self._FAULT_NOISE[fault], dtype=np.float32)
        noise = rng.normal(0, 1, (n, 12)).astype(np.float32)
        return base + noise * noise_scale

    def _fit_synthetic(self) -> None:
        rng = np.random.default_rng(RANDOM_STATE)
        X_parts, y_parts = [], []

        for fault in FAULT_CLASSES:
            X = self._generate_class_samples(fault, SAMPLES_PER_CLASS, rng)
            X_parts.append(X)
            y_parts.extend([fault] * SAMPLES_PER_CLASS)

        X_all = np.vstack(X_parts)
        y_encoded = self._encoder.transform(y_parts)

        self._pipeline.fit(X_all, y_encoded)

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self._pipeline, MODEL_PATH)
        joblib.dump(self._encoder, ENCODER_PATH)
        logger.info(
            "Fault classifier fitted on %d synthetic samples (%d classes), saved to %s",
            len(X_all),
            len(FAULT_CLASSES),
            MODEL_PATH,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def classify(self, features: MotorFeatures) -> FaultClassificationResult:
        X = features.to_array().reshape(1, -1)

        proba = self._pipeline.predict_proba(X)[0]
        predicted_idx = int(np.argmax(proba))
        predicted_class: str = self._encoder.inverse_transform([predicted_idx])[0]
        confidence = round(float(proba[predicted_idx]) * 100.0, 2)

        all_probabilities = {
            str(self._encoder.inverse_transform([i])[0]): round(float(p) * 100.0, 2)
            for i, p in enumerate(proba)
        }

        return FaultClassificationResult(
            fault=predicted_class,
            confidence=confidence,
            all_probabilities=all_probabilities,
        )

    def retrain(self, X: np.ndarray, y: np.ndarray) -> None:
        """Retrain with labelled data. Call from a background task."""
        self._pipeline = self._build_pipeline()
        self._pipeline.fit(X, y)
        joblib.dump(self._pipeline, MODEL_PATH)
        logger.info("Fault classifier retrained with %d samples", len(X))
