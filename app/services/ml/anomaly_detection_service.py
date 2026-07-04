import logging
import os
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.schemas.prediction import AnomalyResult
from app.services.ml.feature_engineering import MotorFeatures

logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "ml/models")
MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_detector.pkl")

CONTAMINATION = 0.05
N_ESTIMATORS = 100
RANDOM_STATE = 42


class AnomalyDetectionService:
    """Isolation Forest anomaly detector for electric motor sensor data."""

    MODEL_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._initialise()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if os.path.exists(MODEL_PATH):
            try:
                self._pipeline = joblib.load(MODEL_PATH)
                logger.info("Anomaly detector loaded from %s", MODEL_PATH)
                return
            except Exception as exc:
                logger.warning("Could not load model (%s) — retraining from synthetic data", exc)

        self._pipeline = self._build_pipeline()
        self._fit_synthetic()

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "detector",
                    IsolationForest(
                        n_estimators=N_ESTIMATORS,
                        contamination=CONTAMINATION,
                        max_samples="auto",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def _fit_synthetic(self) -> None:
        """
        Fit the model on synthetic normal-operation data so it is immediately
        usable before real labelled data is collected.
        """
        rng = np.random.default_rng(RANDOM_STATE)
        n_normal = 2000
        n_anomaly = int(n_normal * CONTAMINATION)

        # Normal operating window: 12 features matching MotorFeatures.to_array()
        X_normal = np.column_stack(
            [
                rng.normal(65, 8, n_normal),         # temperature
                rng.normal(3.0, 0.8, n_normal),      # vibration
                rng.normal(15, 3, n_normal),          # current
                rng.normal(380, 10, n_normal),        # voltage
                rng.normal(5500, 500, n_normal),      # power
                rng.normal(75, 10, n_normal),         # load
                rng.normal(0.85, 0.08, n_normal),     # current_ratio
                rng.normal(0.87, 0.04, n_normal),     # power_factor
                rng.normal(65, 8, n_normal),          # temp rolling mean
                rng.normal(3.0, 0.8, n_normal),       # vib rolling mean
                rng.normal(2.0, 0.5, n_normal),       # temp std
                rng.normal(0.3, 0.1, n_normal),       # vib std
            ]
        )

        # Synthetic anomalies: overtemperature + high vibration
        X_anom = X_normal[:n_anomaly].copy()
        X_anom[:, 0] += rng.uniform(25, 45, n_anomaly)  # temperature spike
        X_anom[:, 1] += rng.uniform(7, 15, n_anomaly)   # vibration spike

        X_all = np.vstack([X_normal, X_anom])

        self._pipeline.fit(X_all)
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self._pipeline, MODEL_PATH)
        logger.info(
            "Anomaly detector fitted on %d synthetic samples, saved to %s",
            len(X_all),
            MODEL_PATH,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def detect(self, features: MotorFeatures) -> AnomalyResult:
        """
        Returns anomaly flag and a normalised score in [0, 1].
        Higher score = more anomalous.
        """
        X = features.to_array().reshape(1, -1)

        label = self._pipeline.predict(X)[0]          # 1 = normal, -1 = anomaly
        decision = float(self._pipeline.decision_function(X)[0])

        # decision_function > 0 means normal, < 0 means anomaly
        # Map to [0, 1]: score 0.5 at threshold, 1.0 at very negative end
        score = float(np.clip(0.5 - decision, 0.0, 1.0))

        return AnomalyResult(anomaly=(label == -1), score=round(score, 4))

    def retrain(self, X: np.ndarray) -> None:
        """Retrain with a new dataset (call from background task, never in-process)."""
        self._pipeline = self._build_pipeline()
        self._pipeline.fit(X)
        joblib.dump(self._pipeline, MODEL_PATH)
        logger.info("Anomaly detector retrained with %d samples", len(X))
