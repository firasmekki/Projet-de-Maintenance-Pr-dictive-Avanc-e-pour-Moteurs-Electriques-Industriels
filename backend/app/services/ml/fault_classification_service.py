import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.schemas.prediction import FaultClassificationResult
from app.services.ml.feature_engineering import MotorFeatures

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(os.environ.get("ML_MODEL_DIR", "ml/models"))
_MODEL_PATH = _MODEL_DIR / "fault_classifier.pkl"
_ENCODER_PATH = _MODEL_DIR / "label_encoder.pkl"

_RANDOM_STATE = 42
_SAMPLES_PER_CLASS = 400

FAULT_CLASSES: list[str] = [
    "Normal",
    "Bearing Wear",
    "Misalignment",
    "Unbalance",
    "Rotor Fault",
    "Insulation Fault",
    "Overload",
]


class FaultClassificationService:
    """
    Random Forest multi-class fault classifier.
    Features: 13 motor sensor-derived values (see FeatureEngineer).
    Classes: 7 (Normal + 6 fault types).
    """

    MODEL_VERSION = "1.0.0"

    # Domain-knowledge fault signatures — (mean, noise_scale) per feature
    # Features order: temp, vib, cur, volt, pwr, load, pf, thd, cr, t_mean, v_mean, t_std, v_std
    _PROFILES: dict[str, list[float]] = {
        "Normal":           [65,  3.0,  15.0, 380, 5500, 75, 0.87, 3.5, 0.85, 65,  3.0,  2.0, 0.3],
        "Bearing Wear":     [78,  9.5,  15.5, 380, 5600, 76, 0.86, 4.0, 0.87, 76,  9.2,  3.0, 1.5],
        "Misalignment":     [82,  12.5, 18.0, 375, 6200, 82, 0.84, 4.5, 1.10, 80,  12.0, 3.5, 2.0],
        "Unbalance":        [71,  7.5,  16.5, 379, 5800, 78, 0.86, 3.8, 0.95, 70,  7.2,  2.5, 1.2],
        "Rotor Fault":      [88,  5.0,  22.0, 376, 7200, 85, 0.82, 5.5, 1.35, 86,  4.8,  4.0, 0.6],
        "Insulation Fault": [95,  4.5,  20.0, 350, 6800, 80, 0.72, 6.5, 1.20, 92,  4.3,  5.0, 0.5],
        "Overload":         [85,  5.5,  24.0, 378, 8500, 95, 0.85, 4.2, 1.50, 83,  5.3,  3.5, 0.7],
    }

    _NOISE: dict[str, list[float]] = {
        "Normal":           [5, 0.5, 2, 8, 300, 8, 0.02, 0.4, 0.04, 5, 0.5, 0.4, 0.08],
        "Bearing Wear":     [6, 2.5, 2, 8, 300, 8, 0.03, 0.5, 0.05, 6, 2.5, 1.0, 0.50],
        "Misalignment":     [5, 3.0, 2, 8, 400, 10, 0.04, 0.6, 0.08, 5, 3.0, 1.5, 0.70],
        "Unbalance":        [5, 2.0, 2, 8, 300, 8, 0.03, 0.4, 0.06, 5, 2.0, 0.8, 0.40],
        "Rotor Fault":      [6, 1.5, 3, 10, 500, 10, 0.04, 0.7, 0.10, 6, 1.5, 1.2, 0.30],
        "Insulation Fault": [7, 1.5, 3, 20, 500, 10, 0.05, 0.8, 0.10, 7, 1.5, 2.0, 0.30],
        "Overload":         [6, 2.0, 3, 8, 600, 5, 0.04, 0.5, 0.10, 6, 2.0, 1.5, 0.40],
    }

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._encoder: LabelEncoder | None = None
        self._initialise()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if _MODEL_PATH.exists() and _ENCODER_PATH.exists():
            try:
                self._pipeline = joblib.load(_MODEL_PATH)
                self._encoder = joblib.load(_ENCODER_PATH)
                logger.info("Fault classifier loaded from %s", _MODEL_PATH)
                return
            except Exception as exc:
                logger.warning("Model load failed (%s) — retraining on synthetic data", exc)

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
                        random_state=_RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def _generate_class_samples(
        self,
        fault: str,
        n: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        base = np.array(self._PROFILES[fault], dtype=np.float32)
        scale = np.array(self._NOISE[fault], dtype=np.float32)
        noise = rng.normal(0, 1, (n, len(base))).astype(np.float32)
        return base + noise * scale

    def _fit_synthetic(self) -> None:
        rng = np.random.default_rng(_RANDOM_STATE)
        X_parts: list[np.ndarray] = []
        y_parts: list[str] = []

        for fault in FAULT_CLASSES:
            X_parts.append(self._generate_class_samples(fault, _SAMPLES_PER_CLASS, rng))
            y_parts.extend([fault] * _SAMPLES_PER_CLASS)

        X_all = np.vstack(X_parts)
        y_encoded = self._encoder.transform(y_parts)

        self._pipeline.fit(X_all, y_encoded)

        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._pipeline, _MODEL_PATH)
        joblib.dump(self._encoder, _ENCODER_PATH)
        logger.info(
            "Fault classifier fitted on %d synthetic samples (%d classes), saved to %s",
            len(X_all), len(FAULT_CLASSES), _MODEL_PATH,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, features: MotorFeatures) -> FaultClassificationResult:
        X = features.to_array().reshape(1, -1)

        proba: np.ndarray = self._pipeline.predict_proba(X)[0]
        predicted_idx: int = int(np.argmax(proba))
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
        """Retrain with labelled data — call from a background worker only."""
        self._pipeline = self._build_pipeline()
        self._pipeline.fit(X, y)
        joblib.dump(self._pipeline, _MODEL_PATH)
        logger.info("Fault classifier retrained with %d samples", len(X))
