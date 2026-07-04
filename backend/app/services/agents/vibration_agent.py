"""Agent Vibratoire — analyse vibrations RMS, tendances, normes ISO 10816."""
from __future__ import annotations
from typing import Any


_ISO_ZONES = [
    (2.3,  "A", "OK",       "Neuf / récemment révisé"),
    (4.5,  "B", "OK",       "Acceptable en fonctionnement continu"),
    (7.1,  "C", "WARNING",  "Alarme — maintenance à planifier (ISO 10816)"),
    (999,  "D", "CRITICAL", "Danger — arrêt recommandé (ISO 10816)"),
]


def _iso_zone(vib: float) -> tuple[str, str, str]:
    for limit, zone, status, desc in _ISO_ZONES:
        if vib <= limit:
            return zone, status, desc
    return "D", "CRITICAL", "Danger — arrêt recommandé (ISO 10816)"


def analyze(analysis: dict[str, Any]) -> dict[str, Any]:
    stats  = analysis.get("statistics", {})
    trends = analysis.get("trends", {})
    fault  = analysis.get("fault", "No Fault")

    def s(key: str, field: str = "mean") -> float | None:
        d = stats.get(key)
        return d[field] if d else None

    findings  = []
    severity_score = 0

    # ── Vibration RMS ─────────────────────────────────────────────────
    v_mean = s("vibration")
    v_max  = s("vibration", "max")
    v_trend = trends.get("vibration", "STABLE")

    if v_mean is not None:
        zone, status, desc = _iso_zone(v_mean)
        findings.append({
            "label":  "Vibration RMS (moy)",
            "value":  f"{v_mean:.2f} mm/s",
            "status": status,
            "detail": f"ISO 10816 Zone {zone} — {desc}",
            "norm":   "ISO 10816",
        })
        if zone == "D":
            severity_score += 50
        elif zone == "C":
            severity_score += 30
        elif zone == "B":
            severity_score += 10

    if v_max is not None:
        zone_max, status_max, desc_max = _iso_zone(v_max)
        if zone_max in ("C", "D"):
            findings.append({
                "label":  "Vibration RMS (max)",
                "value":  f"{v_max:.2f} mm/s",
                "status": status_max,
                "detail": f"Pic Zone {zone_max} — {desc_max}",
                "norm":   "ISO 10816",
            })
            severity_score += 15

    # ── Trend analysis ────────────────────────────────────────────────
    trend_map = {
        "RISING":  ("WARNING", "Tendance haussière — dégradation en cours"),
        "FALLING": ("OK",      "Tendance baissière — amélioration détectée"),
        "STABLE":  ("OK",      "Tendance stable"),
    }
    t_status, t_desc = trend_map.get(v_trend, ("OK", "Stable"))
    findings.append({
        "label":  "Tendance Vibratoire",
        "value":  v_trend,
        "status": t_status,
        "detail": t_desc,
        "norm":   "ISO 13373",
    })
    if v_trend == "RISING":
        severity_score += 20

    # ── Fault-specific vibration signature ───────────────────────────
    fault_signatures = {
        "Bearing Wear":  ("Signature roulement probable — fréquences BPFI/BPFO à analyser en FFT", "ISO 10816"),
        "Misalignment":  ("Composante 2×RPM dominante attendue — vérifier alignement laser", "ISO 10816"),
        "Unbalance":     ("Composante 1×RPM dominante — équilibrage dynamique requis (ISO 1940-1 G2.5)", "ISO 1940-1"),
        "Rotor Fault":   ("Bandes latérales autour de la fréquence de rotation — MCSA recommandé", "IEC 60034"),
    }
    if fault in fault_signatures:
        detail, norm = fault_signatures[fault]
        findings.append({
            "label":  "Signature Spectrale",
            "value":  fault,
            "status": "WARNING",
            "detail": detail,
            "norm":   norm,
        })
        severity_score += 10

    # ── Severity mapping ─────────────────────────────────────────────
    if severity_score >= 60:
        severity = "CRITICAL"
    elif severity_score >= 35:
        severity = "HIGH"
    elif severity_score >= 15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    conclusions = {
        "CRITICAL": "Niveaux vibratoires critiques (ISO Zone D). Arrêt recommandé — risque de dommages mécaniques.",
        "HIGH":     "Vibrations en Zone C (ISO 10816). Maintenance à planifier dans les 7 jours.",
        "MEDIUM":   "Vibrations en Zone B. Surveillance renforcée. Analyser la tendance.",
        "LOW":      "Niveaux vibratoires conformes à la norme ISO 10816 Zone A/B. Aucune anomalie détectée.",
    }

    return {
        "agent_id":   "vibration",
        "title":      "Agent Vibratoire",
        "icon":       "📳",
        "domain":     "Vibration RMS · Tendances · Spectres · ISO 10816",
        "severity":   severity,
        "findings":   findings,
        "conclusion": conclusions[severity],
        "confidence": min(95, 55 + severity_score),
        "norm_refs":  ["ISO 10816", "ISO 20816", "ISO 13373", "ISO 1940-1"],
    }
