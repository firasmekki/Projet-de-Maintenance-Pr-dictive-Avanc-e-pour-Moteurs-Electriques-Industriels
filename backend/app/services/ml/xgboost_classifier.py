"""XGBoost fault classifier trained on synthetic industrial motor data."""
from __future__ import annotations

import logging
import threading
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_FAULT_LABELS = [
    "No Fault",
    "Bearing Wear",
    "Misalignment",
    "Unbalance",
    "Rotor Fault",
    "Insulation Fault",
    "Overload",
    "Early Degradation",
]

_lock      = threading.Lock()
_model     = None
_scaler    = None
_trained   = False


def _generate_training_data() -> tuple[np.ndarray, np.ndarray]:
    """Synthetic data based on known fault signatures (temp, vib, cr, load, pf)."""
    rng = np.random.default_rng(42)
    rows, labels = [], []

    # (temp_range, vib_range, cr_range, load_range, pf_range)
    specs: list[tuple[str, tuple, tuple, tuple, tuple, tuple]] = [
        ("No Fault",          (55, 78), (0.5, 3.5),  (0.70, 0.92), (0.55, 0.88), (0.85, 0.97)),
        ("Bearing Wear",      (78, 96), (5.0, 9.5),  (0.85, 1.05), (0.65, 0.90), (0.80, 0.91)),
        ("Misalignment",      (70, 87), (7.0, 13.0), (0.75, 0.95), (0.68, 0.90), (0.82, 0.93)),
        ("Unbalance",         (62, 82), (5.5, 10.5), (0.72, 0.95), (0.58, 0.87), (0.85, 0.96)),
        ("Rotor Fault",       (74, 92), (2.5, 7.0),  (1.05, 1.22), (0.68, 0.95), (0.74, 0.88)),
        ("Insulation Fault",  (85, 102),(1.5, 5.0),  (1.05, 1.22), (0.68, 0.90), (0.68, 0.82)),
        ("Overload",          (85, 103),(2.5, 7.0),  (1.15, 1.42), (0.88, 1.00), (0.78, 0.91)),
        ("Early Degradation", (68, 85), (3.0, 6.5),  (0.80, 1.00), (0.70, 0.92), (0.83, 0.93)),
    ]

    n_per_class = 350
    for idx, (name, t_r, v_r, cr_r, l_r, pf_r) in enumerate(specs):
        t    = rng.uniform(*t_r,  n_per_class) + rng.normal(0, 1.5, n_per_class)
        v    = rng.uniform(*v_r,  n_per_class) + rng.normal(0, 0.4, n_per_class)
        cr   = rng.uniform(*cr_r, n_per_class) + rng.normal(0, 0.03, n_per_class)
        load = rng.uniform(*l_r,  n_per_class) + rng.normal(0, 0.03, n_per_class)
        pf   = rng.uniform(*pf_r, n_per_class) + rng.normal(0, 0.02, n_per_class)

        # Derived features
        temp_norm = np.clip((t - 40) / 70, 0, 1)
        vib_norm  = np.clip(v / 12,  0, 1)
        cr_norm   = np.clip(cr - 1,  -0.5, 0.5)

        X = np.column_stack([t, v, cr, load, pf, temp_norm, vib_norm, cr_norm])
        rows.append(X)
        labels.extend([idx] * n_per_class)

    return np.vstack(rows), np.array(labels)


def _ensure_trained() -> None:
    global _model, _scaler, _trained
    with _lock:
        if _trained:
            return
        try:
            from sklearn.preprocessing import StandardScaler
            from xgboost import XGBClassifier

            X, y = _generate_training_data()
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_scaled, y)

            _model   = model
            _scaler  = scaler
            _trained = True
            logger.info("XGBoost fault classifier trained — %d samples, %d classes", len(X), len(_FAULT_LABELS))
        except Exception as exc:
            logger.warning("XGBoost training failed: %s", exc)
            _trained = True  # don't retry forever


def _build_features(
    temp: float,
    vib:  float,
    current_ratio: float,
    load: float = 0.8,
    power_factor:  float = 0.88,
) -> np.ndarray:
    temp_norm = np.clip((temp - 40) / 70, 0, 1)
    vib_norm  = np.clip(vib / 12,  0, 1)
    cr_norm   = np.clip(current_ratio - 1, -0.5, 0.5)
    return np.array([[temp, vib, current_ratio, load, power_factor,
                       temp_norm, vib_norm, cr_norm]])


def predict_fault(
    temp:          float,
    vib:           float,
    current_ratio: float,
    load:          float = 0.8,
    power_factor:  float = 0.88,
    temp_trend:    str   = "STABLE",
    vib_trend:     str   = "STABLE",
) -> tuple[str, int]:
    """Return (fault_name, confidence_pct). Hard threshold rules override XGBoost."""
    _ensure_trained()

    # ── Hard threshold rules — fire BEFORE XGBoost ───────────────────────
    # These handle compound fault scenarios that XGBoost synthetic training may miss.

    # Overload + bearing stress (worst case: all critical simultaneously)
    if vib > 7.1 and temp > 85 and load > 0.92 and power_factor < 0.82:
        return "Overload", 90

    # Vibration Zone D + high temp = Bearing Wear
    if vib > 7.1 and temp > 85:
        return "Bearing Wear", 88

    # High load + degraded pf + elevated temp (classic overload signature)
    if load > 0.92 and power_factor < 0.78 and temp > 80:
        return "Overload", 84

    # Extreme temp + low pf + low vibration = Insulation Fault
    if temp > 95 and power_factor < 0.76 and vib < 5.0:
        return "Insulation Fault", 80

    # Extreme vibration + cool motor = Misalignment or Unbalance
    if vib > 8.5 and temp < 80:
        return "Misalignment", 76

    # High current ratio + elevated temp
    if current_ratio > 1.15 and temp > 85:
        return "Overload", 78

    if _model is None or _scaler is None:
        return _rule_fallback(temp, vib, current_ratio)

    try:
        X      = _build_features(temp, vib, current_ratio, load, power_factor)
        Xs     = _scaler.transform(X)
        proba  = _model.predict_proba(Xs)[0]
        idx    = int(np.argmax(proba))
        conf   = int(round(proba[idx] * 100))
        fault  = _FAULT_LABELS[idx]

        # Post-process: Early Degradation override
        if (fault == "No Fault"
                and temp_trend == "RISING"
                and vib_trend  == "RISING"
                and temp < 90
                and vib  < 7):
            return "Early Degradation", 75

        # Minimum confidence threshold
        if conf < 45 and fault != "No Fault":
            return "No Fault", conf

        return fault, conf

    except Exception as exc:
        logger.warning("XGBoost predict failed: %s", exc)
        return _rule_fallback(temp, vib, current_ratio)


def get_fault_probabilities(
    temp:          float,
    vib:           float,
    current_ratio: float,
    load:          float = 0.8,
    power_factor:  float = 0.88,
) -> list[dict[str, Any]]:
    """Return probability distribution across all fault classes."""
    _ensure_trained()

    if _model is None or _scaler is None:
        return []

    try:
        X     = _build_features(temp, vib, current_ratio, load, power_factor)
        Xs    = _scaler.transform(X)
        proba = _model.predict_proba(Xs)[0]
        return [
            {"name": _FAULT_LABELS[i], "value": int(round(p * 100))}
            for i, p in enumerate(proba)
            if p > 0.01
        ]
    except Exception:
        return []


def _rule_fallback(temp: float, vib: float, cr: float) -> tuple[str, int]:
    """Minimal rule-based fallback when XGBoost is unavailable."""
    if cr > 1.15 and temp > 85:
        return "Overload", 70
    if temp > 90 and cr > 1.05:
        return "Insulation Fault", 65
    if vib > 7.5:
        return "Misalignment", 60
    if vib > 6 and temp > 80:
        return "Bearing Wear", 58
    if vib > 6:
        return "Unbalance", 55
    if cr > 1.05:
        return "Rotor Fault", 52
    return "No Fault", 0
