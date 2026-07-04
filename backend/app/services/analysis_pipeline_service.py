"""Full offline analysis pipeline — production-grade industrial quality."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_MAX_CHART_POINTS     = 200
_MIN_ISOLATION_SAMPLES = 10

# ---------------------------------------------------------------------------
# Fault rules — load + power_factor aware
# ---------------------------------------------------------------------------

_FAULT_RULES: list[tuple[str, Any]] = [
    ("Bearing Wear",     lambda t, v, cr, lo, pf: (35 if v > 6   else 0) + (30 if t > 85  else 0) + (20 if lo > 0.85 else 0) + (10 if 0.85 <= cr <= 1.08 else 0)),
    ("Misalignment",     lambda t, v, cr, lo, pf: (45 if v > 7.5 else 0) + (20 if 75 < t <= 90 else 0) + (20 if cr <= 1.0 else 0)),
    ("Unbalance",        lambda t, v, cr, lo, pf: (40 if v > 5   else 0) + (25 if t <= 82 else 0) + (20 if cr <= 1.0 else 0)),
    ("Rotor Fault",      lambda t, v, cr, lo, pf: (40 if cr > 1.05 else 0) + (20 if 3 <= v <= 7 else 0) + (20 if 75 < t <= 90 else 0)),
    ("Insulation Fault", lambda t, v, cr, lo, pf: (35 if t > 90  else 0) + (25 if v < 4   else 0) + (30 if cr > 1.05 else 0) + (20 if pf < 0.76 else 0)),
    ("Overload",         lambda t, v, cr, lo, pf: (45 if lo > 0.90 else 0) + (30 if t > 85 else 0) + (20 if pf < 0.82 else 0) + (15 if cr > 1.05 else 0)),
]


def _score_row(
    temp: float, vib: float, current_ratio: float,
    load: float = 0.80, power_factor: float = 0.88,
) -> tuple[str, int]:
    # Hard rules for extreme compound conditions
    if vib > 7.1 and temp > 85:
        if load > 0.92 and power_factor < 0.82:
            return "Overload", 90
        return "Bearing Wear", 86

    if load > 0.92 and power_factor < 0.78 and temp > 80:
        return "Overload", 82

    if temp > 95 and power_factor < 0.76 and vib < 5.0:
        return "Insulation Fault", 78

    if vib > 8.0 and temp < 82:
        return "Misalignment", 74

    if current_ratio > 1.15 and temp > 85:
        return "Overload", 76

    best_fault, best_score = "No Fault", 0
    for fault, fn in _FAULT_RULES:
        s = min(100, int(fn(temp, vib, current_ratio, load, power_factor)))
        if s > best_score:
            best_score, best_fault = s, fault

    if best_score < 45:
        return "No Fault", best_score
    return best_fault, best_score


def _health_row(
    temp: float, vib: float, current_ratio: float,
    load: float = 0.80, power_factor: float = 0.88,
) -> int:
    score = 100
    if temp >= 100:  score -= 23
    elif temp > 90:  score -= 17
    elif temp > 80:  score -= 10
    elif temp > 70:  score -= 4

    if vib > 7.1:    score -= 23
    elif vib > 4.5:  score -= 15
    elif vib > 2.3:  score -= 6

    if current_ratio > 1.15: score -= 18
    elif current_ratio > 1.05: score -= 10
    elif current_ratio > 0.98: score -= 4

    if load > 0.95:    score -= 10
    elif load > 0.90:  score -= 5

    if power_factor < 0.70:  score -= 12
    elif power_factor < 0.80: score -= 7

    n_crit = sum([temp >= 90, vib > 7.1, current_ratio > 1.10, load > 0.93, power_factor < 0.78])
    if n_crit >= 4:   score -= 10
    elif n_crit >= 3: score -= 6
    elif n_crit >= 2: score -= 3

    return max(0, score)


def _trend(values: list[float]) -> str:
    if len(values) < 4:
        return "STABLE"
    n = max(2, len(values) // 3)
    first_mean = float(np.mean(values[:n]))
    last_mean  = float(np.mean(values[-n:]))
    if first_mean == 0:
        return "STABLE"
    change = (last_mean - first_mean) / abs(first_mean)
    if change > 0.05:  return "RISING"
    if change < -0.05: return "FALLING"
    return "STABLE"


def _downsample(lst: list, n: int = _MAX_CHART_POINTS) -> list:
    if len(lst) <= n:
        return lst
    step = len(lst) / n
    return [lst[int(i * step)] for i in range(n)]


# ---------------------------------------------------------------------------
# New: Health Timeline
# ---------------------------------------------------------------------------

def _detect_health_timeline(health_scores: list[int]) -> list[dict]:
    """Detect phase transitions and return labeled segments."""
    n = len(health_scores)
    if n < 4:
        return []

    n_segs = max(4, min(12, n // max(1, n // 8)))
    seg_size = max(1, n // n_segs)

    raw: list[dict] = []
    for i in range(0, n, seg_size):
        seg = health_scores[i: i + seg_size]
        if not seg:
            continue
        avg = float(np.mean(seg))
        if avg >= 75:
            phase = "Sain"
        elif avg >= 55:
            phase = "Dégradation Précoce"
        elif avg >= 35:
            phase = "Avertissement"
        else:
            phase = "Critique"

        raw.append({
            "phase":      phase,
            "avg_health": round(avg, 1),
            "start_pct":  round(i / n * 100, 1),
            "end_pct":    round(min((i + seg_size) / n * 100, 100.0), 1),
        })

    # Merge consecutive same-phase segments
    merged: list[dict] = []
    for seg in raw:
        if merged and merged[-1]["phase"] == seg["phase"]:
            merged[-1]["end_pct"] = seg["end_pct"]
        else:
            merged.append(dict(seg))

    return merged


# ---------------------------------------------------------------------------
# New: Explainable AI (XAI)
# ---------------------------------------------------------------------------

def _compute_xai(
    temp: float, vib: float, current_ratio: float,
    load: float, power_factor: float, thd: float,
    trends: dict[str, str], anomaly_score: float, fault: str,
) -> list[dict]:
    """Feature contribution percentages toward the detected fault."""
    raw: dict[str, int] = {}

    # Vibration
    if vib > 7.1:   raw["Vibration RMS (ISO Zone D)"]  = 40
    elif vib > 4.5: raw["Vibration RMS (ISO Zone C)"]  = 25
    elif vib > 2.3: raw["Vibration RMS (Zone B)"]      = 10

    # Temperature
    if temp >= 100:  raw["Température critique (≥100°C)"] = 35
    elif temp > 90:  raw["Température élevée (>90°C)"]    = 25
    elif temp > 80:  raw["Température haute (>80°C)"]     = 12

    # Load
    if load > 0.95:    raw["Charge moteur (>95%)"]  = 30
    elif load > 0.90:  raw["Charge moteur (>90%)"]  = 15

    # Power factor
    if power_factor < 0.75:   raw["Cos φ dégradé (<0.75)"] = 25
    elif power_factor < 0.85: raw["Cos φ bas (<0.85)"]     = 12

    # THD
    if thd > 8.0:   raw["THD élevé (>8%)"]    = 20
    elif thd > 5.0: raw["THD moyen (>5%)"]    = 10

    # Current ratio
    if current_ratio > 1.15: raw["Courant hors nominal (×1.15)"] = 20
    elif current_ratio > 1.05: raw["Courant légèrement haut"]   = 10

    # Trends
    if trends.get("vibration")   == "RISING":  raw["Tendance vibration ↑"]    = 15
    if trends.get("temperature") == "RISING":  raw["Tendance thermique ↑"]    = 10
    if trends.get("current")     == "RISING":  raw["Tendance courant ↑"]      = 8
    if trends.get("power")       == "RISING":  raw["Tendance puissance ↑"]    = 5

    # Anomaly score
    if anomaly_score > 0.3:
        raw["Anomalies Isolation Forest"]  = max(5, int(anomaly_score * 20))

    if not raw:
        return []

    total = sum(raw.values()) or 1
    items = [{"feature": k, "contribution": round(v * 100 / total)} for k, v in raw.items()]
    items.sort(key=lambda x: -x["contribution"])
    return items[:7]


# ---------------------------------------------------------------------------
# New: Remaining Useful Life
# ---------------------------------------------------------------------------

def _estimate_rul(health_score: int, risk_7d: float, fault: str) -> dict:
    if fault == "No Fault" and health_score >= 75:
        return {"value": "6+ mois", "days": 180, "confidence": "ÉLEVÉE", "label": "green"}
    if risk_7d >= 80 or health_score < 30:
        days = max(1, int((1 - risk_7d / 100) * 14))
        return {"value": f"{days}–{days * 2} jours", "days": days, "confidence": "ÉLEVÉE", "label": "red"}
    if risk_7d >= 50 or health_score < 50:
        days = max(7, int(30 * (1 - risk_7d / 100) + 5))
        return {"value": f"{days} jours", "days": days, "confidence": "ÉLEVÉE", "label": "orange"}
    if risk_7d >= 20:
        return {"value": "1–3 mois", "days": 60, "confidence": "MOYENNE", "label": "yellow"}
    return {"value": "3–6 mois", "days": 120, "confidence": "FAIBLE", "label": "green"}


# ---------------------------------------------------------------------------
# New: Risk factors
# ---------------------------------------------------------------------------

def _build_risk_factors(
    fault: str, iso_zone: str, temp: float, anomaly_count: int,
    trends: dict, load: float, power_factor: float, thd: float,
) -> list[str]:
    factors: list[str] = []
    if fault not in ("No Fault",):
        factors.append(f"Défaut détecté : {fault}")
    if iso_zone in ("Zone D", "Zone C"):
        factors.append(f"Vibrations {iso_zone} (ISO 10816)")
    if temp > 90:
        factors.append(f"Température critique : {temp:.1f}°C (seuil IEC 60034 : 90°C)")
    if load > 0.92:
        factors.append(f"Charge élevée : {load * 100:.0f}% (risque surcharge)")
    if power_factor < 0.80:
        factors.append(f"Cos φ dégradé : {power_factor:.2f} (norme IEC 60034-30)")
    if thd > 8:
        factors.append(f"THD élevé : {thd:.1f}% (seuil IEEE 519 : 5%)")
    if anomaly_count > 0:
        factors.append(f"{anomaly_count} anomalies détectées (Isolation Forest)")
    rising = [k for k, v in trends.items() if v == "RISING"]
    if len(rising) >= 3:
        factors.append("Dégradation multi-capteurs simultanée")
    elif len(rising) >= 1:
        factors.append(f"Tendance haussière : {', '.join(rising)}")
    return factors


# ---------------------------------------------------------------------------
# New: Prioritized recommendations
# ---------------------------------------------------------------------------

_RECS_PRIO: dict[str, list[dict]] = {
    "Bearing Wear": [
        {"priority": 1, "action": "Inspecter les roulements (côté entraînement et non-entraînement)",           "urgency": "immediate"},
        {"priority": 2, "action": "Analyse de lubrification : viscosité, contamination, niveau",                "urgency": "immediate"},
        {"priority": 3, "action": "Analyse FFT vibratoire pour identifier fréquences BPFI/BPFO",               "urgency": "days"},
        {"priority": 4, "action": "Vérifier l'alignement de l'arbre (± 0,05 mm par laser)",                   "urgency": "days"},
        {"priority": 5, "action": "Réduire la charge mécanique si possible",                                   "urgency": "immediate"},
        {"priority": 6, "action": "Surveillance continue toutes les 2h jusqu'à la maintenance",                "urgency": "immediate"},
    ],
    "Overload": [
        {"priority": 1, "action": "Réduire la charge immédiatement (< 90% de la capacité nominale)",          "urgency": "immediate"},
        {"priority": 2, "action": "Inspecter l'équipement entraîné (pompe, ventilateur, convoyeur colmaté)",  "urgency": "immediate"},
        {"priority": 3, "action": "Vérifier le dimensionnement moteur vs la charge réelle",                   "urgency": "days"},
        {"priority": 4, "action": "Tester la résistance d'isolation des bobinages (> 100 MΩ)",                "urgency": "days"},
        {"priority": 5, "action": "Vérifier le refroidissement : ventilateur, grilles d'aération",            "urgency": "immediate"},
        {"priority": 6, "action": "Planifier arrêt préventif dans les 24–48h",                                "urgency": "immediate"},
    ],
    "Insulation Fault": [
        {"priority": 1, "action": "Test de résistance d'isolation au Megohmmètre (normal > 100 MΩ)",          "urgency": "immediate"},
        {"priority": 2, "action": "Test DAR : IP = R10min/R1min — valeur > 2 requise",                        "urgency": "immediate"},
        {"priority": 3, "action": "Nettoyer les voies de refroidissement et les filtres",                     "urgency": "immediate"},
        {"priority": 4, "action": "Séchage des bobinages si humidité détectée (étuve ou résistances)",        "urgency": "days"},
        {"priority": 5, "action": "Planifier re-vernissage ou rembobinage si R < 1 MΩ",                       "urgency": "days"},
        {"priority": 6, "action": "Surveillance température toutes les 30 min",                               "urgency": "immediate"},
    ],
    "Misalignment": [
        {"priority": 1, "action": "Alignement laser (tolérance : ± 0,05 mm angulaire et parallèle)",          "urgency": "days"},
        {"priority": 2, "action": "Inspecter l'accouplement : usure, jeu, éléments élastiques",               "urgency": "days"},
        {"priority": 3, "action": "Vérifier le soft foot (tolérance < 0,05 mm)",                              "urgency": "days"},
        {"priority": 4, "action": "Inspecter les roulements (désalignement → usure accélérée)",               "urgency": "days"},
        {"priority": 5, "action": "Vérifier rigidité de la fondation et des ancrages",                        "urgency": "weeks"},
        {"priority": 6, "action": "Mesure FFT après correction pour validation ISO 10816",                    "urgency": "days"},
    ],
    "Unbalance": [
        {"priority": 1, "action": "Équilibrage dynamique ISO 1940-1 Grade G2.5",                              "urgency": "days"},
        {"priority": 2, "action": "Nettoyer les surfaces du ventilateur (dépôts asymétriques)",               "urgency": "immediate"},
        {"priority": 3, "action": "Vérifier les fixations du rotor et absence de pièce mobile",               "urgency": "immediate"},
        {"priority": 4, "action": "Inspecter les roulements (déséquilibre → surcharge roulement)",            "urgency": "days"},
        {"priority": 5, "action": "Mesure FFT pour confirmer composante 1×RPM dominante",                     "urgency": "days"},
        {"priority": 6, "action": "Vérifier l'alignement après correction du déséquilibre",                  "urgency": "days"},
    ],
    "Rotor Fault": [
        {"priority": 1, "action": "Analyse MCSA : spectre courant, bandes à f ± 2s×f",                       "urgency": "days"},
        {"priority": 2, "action": "Inspection visuelle du rotor (barres de cage, court-circuit)",             "urgency": "days"},
        {"priority": 3, "action": "Test de résistance du rotor",                                              "urgency": "days"},
        {"priority": 4, "action": "Vérifier l'excentricité magnétique (UMP)",                                 "urgency": "weeks"},
        {"priority": 5, "action": "Planifier rembobinage ou remplacement si défaut confirmé",                 "urgency": "weeks"},
        {"priority": 6, "action": "Surveillance courant et vibrations toutes les 4h",                         "urgency": "immediate"},
    ],
    "Early Degradation": [
        {"priority": 1, "action": "Augmenter la fréquence de surveillance à toutes les 4h",                  "urgency": "immediate"},
        {"priority": 2, "action": "Inspecter les roulements et effectuer une lubrification préventive",       "urgency": "days"},
        {"priority": 3, "action": "Vérifier l'équilibre du rotor et l'alignement",                           "urgency": "days"},
        {"priority": 4, "action": "Analyser l'historique de charge : surcharge intermittente ?",              "urgency": "days"},
        {"priority": 5, "action": "Planifier inspection complète dans les 30 jours",                          "urgency": "weeks"},
        {"priority": 6, "action": "Mettre à jour le plan de maintenance préventive",                          "urgency": "weeks"},
    ],
    "No Fault": [
        {"priority": 1, "action": "Continuer la surveillance normale (fréquence standard)",                   "urgency": "months"},
        {"priority": 2, "action": "Prochaine inspection selon le calendrier de maintenance préventive",       "urgency": "months"},
        {"priority": 3, "action": "Vérifier la lubrification lors de la prochaine révision",                 "urgency": "months"},
    ],
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

def _autoencoder_anomaly(features: np.ndarray) -> dict:
    """PCA-based linear AutoEncoder — reconstruction error = anomaly score."""
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA

        if features.shape[0] < 10 or features.shape[1] < 2:
            return {}

        scaler   = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        # Bottleneck = 1 component (strong compression)
        pca       = PCA(n_components=1)
        X_encoded = pca.fit_transform(X_scaled)
        X_decoded = pca.inverse_transform(X_encoded)

        errors    = np.mean((X_scaled - X_decoded) ** 2, axis=1)
        threshold = float(np.percentile(errors, 95))
        anomalies = errors > threshold

        return {
            "method":               "AutoEncoder (PCA linéaire — bottleneck 1D)",
            "n_anomalies":          int(anomalies.sum()),
            "pct_anomalies":        round(100.0 * anomalies.sum() / len(errors), 2),
            "mean_reconstruction_error": round(float(errors.mean()), 4),
            "threshold":            round(threshold, 4),
            "explained_variance":   round(float(pca.explained_variance_ratio_[0]) * 100, 1),
        }
    except Exception as exc:
        import logging; logging.getLogger(__name__).warning("AutoEncoder failed: %s", exc)
        return {}


def _predict_health_trajectory(health_scores: list[int]) -> dict:
    """Polynomial trend + forward projection (LSTM-equivalent for lightweight deployment)."""
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures

        n = len(health_scores)
        if n < 8:
            return {}

        X = np.arange(n).reshape(-1, 1).astype(float)
        y = np.array(health_scores, dtype=float)

        # Degree-2 polynomial captures both linear trend and acceleration
        poly  = PolynomialFeatures(degree=2, include_bias=True)
        Xp    = poly.fit_transform(X)
        model = LinearRegression().fit(Xp, y)

        # Slope at last point (1st derivative of polynomial at x=n-1)
        a2 = model.coef_[2] if len(model.coef_) > 2 else 0.0
        a1 = model.coef_[1]
        slope_at_end = a1 + 2 * a2 * (n - 1)

        # Project future points (assume same sampling density)
        project_steps = max(30, n // 3)
        X_future = poly.transform(np.arange(n, n + project_steps).reshape(-1, 1))
        traj_raw  = model.predict(X_future)
        trajectory = [max(0, min(100, round(float(v), 1))) for v in traj_raw]

        # Predictions at specific future indices
        def pred_at(extra_pct: float) -> float:
            idx = int(n * extra_pct)
            future_x = poly.transform([[n + idx]])
            return max(0, min(100, round(float(model.predict(future_x)[0]), 1)))

        p7  = pred_at(0.23)
        p14 = pred_at(0.47)
        p30 = pred_at(1.0)

        # Estimate days to reach critical threshold (score < 35)
        days_to_critical: str | None = None
        current = float(y[-1])
        if slope_at_end < -0.1 and current > 35:
            steps_needed = (current - 35) / abs(slope_at_end)
            days_est = int(steps_needed * 30 / max(n, 1))
            if days_est < 90:
                days_to_critical = f"~{max(1, days_est)} jours"

        trend_label = (
            "DÉGRADATION RAPIDE" if slope_at_end < -0.5 else
            "DÉGRADATION LENTE"  if slope_at_end < -0.1 else
            "STABLE"             if abs(slope_at_end) < 0.1 else
            "AMÉLIORATION"
        )

        return {
            "method":              "Régression Polynomiale (Prévision Temporelle ML)",
            "trajectory":          trajectory[:60],
            "predictions":         {"day_7": p7, "day_14": p14, "day_30": p30},
            "trend_slope":         round(float(slope_at_end), 3),
            "trend_label":         trend_label,
            "days_to_critical":    days_to_critical,
            "current_health":      round(float(current), 1),
        }
    except Exception as exc:
        import logging; logging.getLogger(__name__).warning("Prediction failed: %s", exc)
        return {}


def _compute_fft_spectrum(vibs: list[float]) -> dict | None:
    """Compute FFT of the vibration RMS time series."""
    try:
        n = len(vibs)
        if n < 16:
            return None

        # Use largest power-of-2 ≤ n
        fft_n = 1
        while fft_n * 2 <= n:
            fft_n *= 2

        y = np.array(vibs[:fft_n], dtype=float)
        # Remove DC offset
        y -= y.mean()

        Y     = np.fft.rfft(y)
        freqs = np.fft.rfftfreq(fft_n)
        mags  = np.abs(Y) / fft_n

        # Skip DC (index 0) for dominant detection
        mags_no_dc   = mags[1:]
        freqs_no_dc  = freqs[1:]
        if len(mags_no_dc) == 0:
            return None

        # Top 20 frequencies
        top_idx = np.argsort(mags_no_dc)[-20:]
        spectrum = sorted([
            {"frequency": round(float(freqs_no_dc[i]), 5),
             "magnitude": round(float(mags_no_dc[i]), 4)}
            for i in top_idx
            if mags_no_dc[i] > 0
        ], key=lambda x: x["frequency"])

        dom_idx = int(np.argmax(mags_no_dc))
        dominant = {
            "frequency": round(float(freqs_no_dc[dom_idx]), 5),
            "magnitude": round(float(mags_no_dc[dom_idx]), 4),
        }

        return {
            "spectrum":          spectrum,
            "dominant":          dominant,
            "n_points":          fft_n,
            "frequency_unit":    "cycles / mesure",
            "note": "FFT de la série temporelle RMS — montre la périodicité des variations vibratoires",
        }
    except Exception as exc:
        import logging; logging.getLogger(__name__).warning("FFT failed: %s", exc)
        return None


def _compute_correlation_matrix(
    temps: list, vibs: list, currents: list,
    voltages: list, powers: list, loads: list,
) -> dict | None:
    """Pearson correlation matrix between available sensors."""
    sensor_map = {
        "Température": temps,
        "Vibration":   vibs,
        "Courant":     currents,
        "Tension":     voltages,
        "Puissance":   powers,
        "Charge":      loads,
    }
    present = {k: v for k, v in sensor_map.items() if len(v) >= 4}
    if len(present) < 2:
        return None

    min_len = min(len(v) for v in present.values())
    labels  = list(present.keys())
    n       = len(labels)
    arrays  = [np.array(present[l][:min_len]) for l in labels]

    matrix = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            try:
                corr = float(np.corrcoef(arrays[i], arrays[j])[0, 1])
                if np.isnan(corr):
                    corr = 0.0
                corr = round(corr, 3)
            except Exception:
                corr = 0.0
            matrix[i][j] = corr
            matrix[j][i] = corr

    return {"labels": labels, "matrix": matrix.tolist()}


class AnalysisPipelineService:

    def analyze(
        self,
        records:       list[dict[str, Any]],
        motor_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not records:
            return {"error": "Empty dataset"}

        temps    = [float(r["temperature"])  for r in records if r.get("temperature")  is not None]
        vibs     = [float(r["vibration"])    for r in records if r.get("vibration")    is not None]
        currents = [float(r["current"])      for r in records if r.get("current")      is not None]
        voltages = [float(r["voltage"])      for r in records if r.get("voltage")      is not None]
        powers   = [float(r["power"])        for r in records if r.get("power")        is not None]
        loads    = [float(r["load"])         for r in records if r.get("load")         is not None]
        pf_vals  = [float(r["power_factor"]) for r in records if r.get("power_factor") is not None]
        thd_vals = [float(r["thd"])          for r in records if r.get("thd")          is not None]

        # ── Normalise load to [0, 1] — datasets may store as percentage (55, 76, 98) ──
        if loads and max(loads) > 1.5:
            loads = [lo / 100.0 for lo in loads]

        # ── Normalise power_factor to [0, 1] if stored as percentage ──────────
        if pf_vals and max(pf_vals) > 1.5:
            pf_vals = [pf / 100.0 for pf in pf_vals]

        n_rows = len(records)

        # Use nominal current from motor profile when provided (much more accurate)
        if motor_profile and motor_profile.get("nominal_current_a"):
            rated_current = float(motor_profile["nominal_current_a"])
            logger.info("Using nominal current from motor profile: %.2f A", rated_current)
        else:
            rated_current = float(np.percentile(currents, 90)) if currents else 1.0
        if rated_current == 0:
            rated_current = 1.0

        t_arr  = np.array(temps    if temps    else [65.0] * n_rows)
        v_arr  = np.array(vibs     if vibs     else [3.0]  * n_rows)
        cr_arr = np.array([c / rated_current for c in currents] if currents else [0.8] * n_rows)
        lo_arr = np.array(loads    if loads    else [0.80]  * n_rows)
        pf_arr = np.array(pf_vals  if pf_vals  else [0.88]  * n_rows)

        avg_load = float(np.mean(lo_arr))
        avg_pf   = float(np.mean(pf_arr))
        avg_temp = float(np.mean(t_arr))
        avg_vib  = float(np.mean(v_arr))
        avg_thd  = float(np.mean(thd_vals)) if thd_vals else 0.0

        # ── Per-row health scores ─────────────────────────────────────────
        health_scores: list[int] = []
        fault_counts:  dict[str, int] = {}
        loop_n = min(len(t_arr), len(v_arr), len(cr_arr), len(lo_arr), len(pf_arr))

        for i in range(loop_n):
            t, v, cr = float(t_arr[i]), float(v_arr[i]), float(cr_arr[i])
            lo, pf   = float(lo_arr[i]), float(pf_arr[i])
            hs = _health_row(t, v, cr, lo, pf)
            health_scores.append(hs)
            fault, _ = _score_row(t, v, cr, lo, pf)
            fault_counts[fault] = fault_counts.get(fault, 0) + 1

        # ── Weighted health score (recent data = 50% weight) ──────────────
        if health_scores:
            n = len(health_scores)
            weights = np.ones(n, dtype=float)
            last20_idx = max(0, int(n * 0.80))
            mid_idx    = max(0, int(n * 0.50))
            weights[last20_idx:] = 2.5
            weights[mid_idx:last20_idx] = 1.0
            weights[:mid_idx] = 0.4
            overall_health = int(round(float(np.average(health_scores, weights=weights))))
            overall_health = max(0, min(100, overall_health))
        else:
            overall_health = 100

        # ── Health timeline ───────────────────────────────────────────────
        health_timeline = _detect_health_timeline([max(0, min(100, h)) for h in health_scores])

        # ── Isolation Forest anomaly detection ────────────────────────────
        anomaly_count = 0; anomaly_pct = 0.0; anomaly_score_mean = 0.0
        autoencoder_result: dict = {}
        feature_rows = []
        for i in range(n_rows):
            row_feats = []
            for arr in [t_arr, v_arr, cr_arr]:
                if i < len(arr):
                    row_feats.append(float(arr[i]))
            if len(row_feats) == 3:
                feature_rows.append(row_feats)

        if len(feature_rows) >= _MIN_ISOLATION_SAMPLES:
            try:
                from sklearn.ensemble import IsolationForest
                from sklearn.preprocessing import StandardScaler
                X        = np.array(feature_rows)
                scaler   = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                clf      = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
                clf.fit(X_scaled)
                labels = clf.predict(X_scaled)
                scores = clf.decision_function(X_scaled)
                anomaly_count      = sum(int(l) == -1 for l in labels)
                anomaly_pct        = round(100.0 * anomaly_count / len(labels), 2)
                anomaly_score_mean = float(round(float(np.clip(0.5 - np.mean(scores), 0.0, 1.0)), 4))
            except Exception as exc:
                logger.warning("IsolationForest failed: %s", exc)

            # ── AutoEncoder (second anomaly detection method) ─────────────
            autoencoder_result = _autoencoder_anomaly(np.array(feature_rows))

        # ── Statistics ────────────────────────────────────────────────────
        def stats(vals: list[float]) -> dict[str, float] | None:
            if not vals:
                return None
            a = np.array(vals)
            return {
                "min":    round(float(a.min()),    3),
                "max":    round(float(a.max()),    3),
                "mean":   round(float(a.mean()),   3),
                "std":    round(float(a.std()),    3),
                "median": round(float(np.median(a)), 3),
            }

        # ── Trends ────────────────────────────────────────────────────────
        def safe_trend(vals: list[float]) -> str:
            return _trend(vals) if vals else "STABLE"

        trends = {
            "temperature": safe_trend(temps),
            "vibration":   safe_trend(vibs),
            "current":     safe_trend(currents),
            "voltage":     safe_trend(voltages),
            "power":       safe_trend(powers),
        }

        # ── Primary fault (mean values for robustness) ────────────────────
        avg_cr = float(np.mean(cr_arr)) if currents else 0.8

        try:
            from app.services.ml.xgboost_classifier import predict_fault, get_fault_probabilities
            primary_fault, primary_confidence = predict_fault(
                temp=avg_temp, vib=avg_vib, current_ratio=avg_cr,
                load=avg_load, power_factor=avg_pf,
                temp_trend=trends.get("temperature", "STABLE"),
                vib_trend=trends.get("vibration", "STABLE"),
            )
            xgb_proba = get_fault_probabilities(avg_temp, avg_vib, avg_cr, avg_load, avg_pf)
        except Exception as exc:
            logger.warning("XGBoost unavailable, using rules: %s", exc)
            primary_fault, primary_confidence = _score_row(avg_temp, avg_vib, avg_cr, avg_load, avg_pf)
            xgb_proba = []

        # ── Early Degradation override ────────────────────────────────────
        if (
            primary_fault == "No Fault"
            and trends["temperature"] == "RISING"
            and trends["vibration"]   == "RISING"
            and len(temps) >= 4 and max(temps) < 90
            and len(vibs)  >= 4 and max(vibs)  < 7
        ):
            primary_fault      = "Early Degradation"
            primary_confidence = 75

        # ── Health status ─────────────────────────────────────────────────
        if overall_health >= 75:   health_status = "Healthy"
        elif overall_health >= 45: health_status = "Warning"
        else:                      health_status = "Critical"

        if primary_fault == "Early Degradation" and health_status == "Healthy":
            health_status = "Warning"

        # ── Severity ──────────────────────────────────────────────────────
        if primary_confidence >= 85:   severity = "CRITICAL"
        elif primary_confidence >= 70: severity = "HIGH"
        elif primary_confidence >= 50: severity = "MEDIUM"
        else:                          severity = "LOW"

        if primary_fault == "Early Degradation": severity = "MEDIUM"
        if primary_fault == "No Fault":          severity = "LOW"

        # ── ISO vibration zone ────────────────────────────────────────────
        if avg_vib > 7.1:    iso_zone = "Zone D"
        elif avg_vib > 4.5:  iso_zone = "Zone C"
        elif avg_vib > 2.3:  iso_zone = "Zone B"
        else:                iso_zone = "Zone A"

        # ── Risk prediction ───────────────────────────────────────────────
        rising_count      = sum(1 for v in trends.values() if v == "RISING")
        health_risk       = (100 - overall_health) / 100.0
        anomaly_component = anomaly_score_mean * 0.20
        fault_component   = (primary_confidence / 100.0) * 0.30 if primary_fault not in ("No Fault",) else 0.0
        trend_component   = (rising_count / max(len(trends), 1)) * 0.15
        raw_risk          = health_risk * 0.40 + anomaly_component + fault_component + trend_component
        risk_7d           = round(min(100.0, raw_risk * 100), 1)
        risk_30d          = round(min(100.0, risk_7d * 1.5 + rising_count * 2.0), 1)

        if risk_7d < 20:    risk_level = "LOW"
        elif risk_7d < 45:  risk_level = "MEDIUM"
        elif risk_7d < 70:  risk_level = "HIGH"
        else:               risk_level = "CRITICAL"

        # ── XAI contributions ─────────────────────────────────────────────
        xai = _compute_xai(
            avg_temp, avg_vib, avg_cr, avg_load, avg_pf, avg_thd,
            trends, anomaly_score_mean, primary_fault,
        )

        # ── RUL estimate ──────────────────────────────────────────────────
        rul = _estimate_rul(overall_health, risk_7d, primary_fault)

        # ── Risk factors ──────────────────────────────────────────────────
        risk_factors = _build_risk_factors(
            primary_fault, iso_zone, avg_temp, anomaly_count,
            trends, avg_load, avg_pf, avg_thd,
        )

        # ── Prioritized recommendations ───────────────────────────────────
        recs_prio = _RECS_PRIO.get(primary_fault, _RECS_PRIO["No Fault"])

        # ── Fault distribution ────────────────────────────────────────────
        if xgb_proba:
            total_rows = max(len(health_scores), 1)
            fault_distribution = [
                {"name": item["name"], "value": max(1, int(item["value"] * total_rows / 100))}
                for item in sorted(xgb_proba, key=lambda x: -x["value"])
                if item["value"] > 2 and item["name"] != "No Fault"
            ] or [
                {"name": f, "value": c}
                for f, c in sorted(fault_counts.items(), key=lambda x: -x[1]) if f != "No Fault"
            ]
        else:
            fault_distribution = [
                {"name": f, "value": c}
                for f, c in sorted(fault_counts.items(), key=lambda x: -x[1])
            ]

        # ── Correlation matrix ────────────────────────────────────────────
        correlation_matrix = _compute_correlation_matrix(
            temps, vibs, currents, voltages, powers, loads,
        )

        # ── Health trajectory prediction (LSTM-equivalent) ────────────────
        health_prediction = _predict_health_trajectory(
            [max(0, min(100, h)) for h in health_scores]
        )

        # ── FFT spectral analysis of vibration series ─────────────────────
        fft_spectrum = _compute_fft_spectrum(vibs) if len(vibs) >= 16 else None

        # ── Root cause summary ────────────────────────────────────────────
        root_causes: list[str] = []
        if avg_vib > 7.1:   root_causes.append(f"Vibration ISO Zone D ({avg_vib:.1f} mm/s)")
        if avg_temp > 90:   root_causes.append(f"Température critique ({avg_temp:.1f}°C)")
        if avg_load > 0.92: root_causes.append(f"Surcharge ({avg_load*100:.0f}%)")
        if avg_pf < 0.80:   root_causes.append(f"Cos φ dégradé ({avg_pf:.2f})")
        if avg_thd > 5:     root_causes.append(f"THD élevé ({avg_thd:.1f}%)")

        # ── Time series ───────────────────────────────────────────────────
        timestamps = [r.get("timestamp") for r in records]

        def ts_series(vals: list[float]) -> list[dict]:
            downsampled = _downsample(vals)
            ts_down     = _downsample(timestamps)
            out = []
            for i, v in enumerate(downsampled):
                pt: dict[str, Any] = {"index": i, "value": round(v, 3)}
                ts = ts_down[i] if i < len(ts_down) else None
                if ts and ts != "NaT" and ts is not None:
                    pt["timestamp"] = str(ts)
                out.append(pt)
            return out

        # Clamp health scores to valid range before building chart data
        health_scores_clamped = [max(0, min(100, int(h))) for h in health_scores]

        health_ds = _downsample(health_scores_clamped)
        ts_health: list[dict] = []
        ts_down   = _downsample(timestamps)
        for i, v in enumerate(health_ds):
            pt: dict[str, Any] = {"index": i, "value": max(0, min(100, int(v)))}
            ts = ts_down[i] if i < len(ts_down) else None
            if ts and str(ts) not in ("None", "NaT"):
                pt["timestamp"] = str(ts)
            ts_health.append(pt)

        # ── Recommendations (text) ────────────────────────────────────────
        _RECS = {
            "Bearing Wear":      "Inspecter les roulements, vérifier la lubrification. Planifier remplacement si Zone D (ISO 10816). Mesure FFT recommandée.",
            "Misalignment":      "Réaliser un alignement laser (± 0,05 mm). Inspecter l'accouplement et vérifier le soft foot.",
            "Unbalance":         "Équilibrage dynamique requis (ISO 1940-1 G2.5). Nettoyer les surfaces et vérifier les fixations.",
            "Rotor Fault":       "Effectuer une analyse MCSA. Inspecter les barres de cage du rotor.",
            "Insulation Fault":  "Test de résistance d'isolation (> 100 MΩ). Vérifier refroidissement. Séchage ou rembobinage si nécessaire.",
            "Overload":          "Réduire immédiatement la charge. Vérifier dimensionnement. Arrêt préventif dans les 24–48h recommandé.",
            "Early Degradation": "Dégradation précoce. Augmenter surveillance (toutes les 4h). Maintenance préventive dans les 30 jours.",
            "No Fault":          "Aucun défaut. Continuer la surveillance normale.",
        }

        return {
            # Core diagnostics
            "health_score":       overall_health,
            "health_status":      health_status,
            "fault":              primary_fault,
            "severity":           severity,
            "confidence":         primary_confidence,
            "risk_level":         risk_level,
            "recommendation":     _RECS.get(primary_fault, _RECS["No Fault"]),
            "iso_zone":           iso_zone,
            "root_causes":        root_causes,
            # New analytical fields
            "health_timeline":    health_timeline,
            "xai":                xai,
            "rul":                rul,
            "risk_factors":       risk_factors,
            "recommendations_prioritized": recs_prio,
            # Anomaly
            "anomaly": {
                "detected":   anomaly_count > 0,
                "count":      anomaly_count,
                "percentage": anomaly_pct,
                "mean_score": anomaly_score_mean,
            },
            # Risk
            "risk": {
                "days_7":  risk_7d,
                "days_30": risk_30d,
                "level":   risk_level,
            },
            "trends": trends,
            "statistics": {
                "temperature":  stats(temps),
                "vibration":    stats(vibs),
                "current":      stats(currents),
                "voltage":      stats(voltages),
                "power":        stats(powers),
                "load":         stats(loads),
                "power_factor": stats(pf_vals),
                "thd":          stats(thd_vals),
                "health_score": stats([float(max(0, min(100, h))) for h in health_scores]),
            },
            "time_series": {
                "temperature":  ts_series(temps)    if temps    else [],
                "vibration":    ts_series(vibs)      if vibs     else [],
                "current":      ts_series(currents)  if currents else [],
                "voltage":      ts_series(voltages)  if voltages else [],
                "power":        ts_series(powers)    if powers   else [],
                "load":         ts_series(loads)     if loads    else [],
                "health_score": ts_health,
            },
            "fault_distribution":         fault_distribution,
            "estimated_rated_current":    round(rated_current, 3),
            # XAI context for chatbot
            "motor_profile":        motor_profile,
            "correlation_matrix":   correlation_matrix,
            "health_prediction":    health_prediction,
            "fft_spectrum":         fft_spectrum,
            "autoencoder":          autoencoder_result,
            "xai_context": {
                "avg_temp":  round(avg_temp, 1),
                "avg_vib":   round(avg_vib,  2),
                "avg_load":  round(avg_load,  2),
                "avg_pf":    round(avg_pf,    3),
                "avg_thd":   round(avg_thd,   1),
                "iso_zone":  iso_zone,
            },
        }
