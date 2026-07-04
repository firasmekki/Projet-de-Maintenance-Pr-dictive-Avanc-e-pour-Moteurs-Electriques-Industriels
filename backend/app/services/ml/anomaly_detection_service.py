import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.schemas.prediction import AnomalyResult
from app.services.ml.feature_engineering import MotorFeatures

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(os.environ.get("ML_MODEL_DIR", "ml/models"))
_MODEL_PATH = _MODEL_DIR / "anomaly_detector.pkl"

_CONTAMINATION = 0.05
_N_ESTIMATORS = 100
_RANDOM_STATE = 42


class AnomalyDetectionService:
    """
    Isolation Forest anomaly detector.
    Loads a persisted model on construction; falls back to synthetic-data fit
    when no saved model is found.
    """

    MODEL_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._initialise()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if _MODEL_PATH.exists():
            try:
                self._pipeline = joblib.load(_MODEL_PATH)
                logger.info("Anomaly detector loaded from %s", _MODEL_PATH)
                return
            except Exception as exc:
                logger.warning("Model load failed (%s) — retraining on synthetic data", exc)

        self._pipeline = self._build_pipeline()
        self._fit_synthetic()

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "detector",
                    IsolationForest(
                        n_estimators=_N_ESTIMATORS,
                        contamination=_CONTAMINATION,
                        max_samples="auto",
                        random_state=_RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def _fit_synthetic(self) -> None:
        rng = np.random.default_rng(_RANDOM_STATE)
        n = 2000

        # 13 features in FEATURE_NAMES order
        X_normal = np.column_stack(
            [
                rng.normal(65, 8, n),        # temperature
                rng.normal(3.0, 0.8, n),     # vibration
                rng.normal(15, 3, n),         # current
                rng.normal(380, 10, n),       # voltage
                rng.normal(5500, 500, n),     # power
                rng.normal(75, 10, n),        # load
                rng.normal(0.87, 0.04, n),    # power_factor
                rng.normal(3.5, 0.5, n),      # thd
                rng.normal(0.85, 0.08, n),    # current_ratio
                rng.normal(65, 8, n),         # temperature_mean
                rng.normal(3.0, 0.8, n),      # vibration_mean
                rng.normal(2.0, 0.5, n),      # temperature_std
                rng.normal(0.3, 0.1, n),      # vibration_std
            ]
        )

        # Inject synthetic anomalies (5%)
        anom_idx = rng.choice(n, size=int(n * _CONTAMINATION), replace=False)
        X_normal[anom_idx, 0] += rng.uniform(25, 50, len(anom_idx))  # temperature spike
        X_normal[anom_idx, 1] += rng.uniform(7, 15, len(anom_idx))   # vibration spike

        self._pipeline.fit(X_normal)

        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._pipeline, _MODEL_PATH)
        logger.info("Anomaly detector fitted on %d synthetic samples, saved to %s", n, _MODEL_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, features: MotorFeatures) -> AnomalyResult:
        """Return anomaly flag and normalised score in [0, 1]. Higher = more anomalous."""
        X = features.to_array().reshape(1, -1)

        label: int = self._pipeline.predict(X)[0]          # 1 = normal, -1 = anomaly
        decision: float = float(self._pipeline.decision_function(X)[0])

        # decision > 0 ⟹ normal; map to anomaly score [0, 1]
        score = float(np.clip(0.5 - decision, 0.0, 1.0))

        return AnomalyResult(anomaly=(label == -1), score=round(score, 4))

    def retrain(self, X: np.ndarray) -> None:
        """Replace model with a newly fitted one (call from a background worker)."""
        self._pipeline = self._build_pipeline()
        self._pipeline.fit(X)
        joblib.dump(self._pipeline, _MODEL_PATH)
        logger.info("Anomaly detector retrained with %d samples", len(X))
