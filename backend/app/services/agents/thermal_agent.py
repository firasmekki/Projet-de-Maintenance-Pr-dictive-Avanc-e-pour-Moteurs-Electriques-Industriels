"""Agent Thermique — analyse température, tendances, classes d'isolation IEC 60034."""
from __future__ import annotations
from typing import Any


def analyze(analysis: dict[str, Any]) -> dict[str, Any]:
    stats  = analysis.get("statistics", {})
    trends = analysis.get("trends", {})
    fault  = analysis.get("fault", "No Fault")

    def s(key: str, field: str = "mean") -> float | None:
        d = stats.get(key)
        return d[field] if d else None

    findings      = []
    severity_score = 0

    t_mean  = s("temperature")
    t_max   = s("temperature", "max")
    t_std   = s("temperature", "std")
    t_trend = trends.get("temperature", "STABLE")

    # ── Temperature vs IEC 60034 thresholds ──────────────────────────
    if t_mean is not None:
        if t_mean >= 100:
            status = "CRITICAL"
            desc   = "Au-delà des limites IEC 60034 Classe B (130°C). Risque d'isolation prématurée."
            severity_score += 50
        elif t_mean >= 90:
            status = "CRITICAL"
            desc   = "Température critique — échauffement excessif. Vérifier refroidissement."
            severity_score += 35
        elif t_mean >= 80:
            status = "WARNING"
            desc   = "Température élevée — surveillance renforcée recommandée (seuil alarme: 90°C)"
            severity_score += 20
        elif t_mean >= 70:
            status = "WARNING"
            desc   = "Légèrement élevée — surveiller la tendance"
            severity_score += 8
        else:
            status = "OK"
            desc   = "Température dans les normes IEC 60034 Classe B"

        findings.append({
            "label":  "Température Moyenne",
            "value":  f"{t_mean:.1f} °C",
            "status": status,
            "detail": desc,
            "norm":   "IEC 60034-1",
        })

    # ── Peak temperature ─────────────────────────────────────────────
    if t_max is not None and t_max > 85:
        zone = "CRITICAL" if t_max >= 100 else "WARNING"
        findings.append({
            "label":  "Température Maximale",
            "value":  f"{t_max:.1f} °C",
            "status": zone,
            "detail": f"Pic thermique — dépasse le seuil d'alarme (90°C IEC 60034)",
            "norm":   "IEC 60034-1",
        })
        severity_score += 15

    # ── Thermal variability ───────────────────────────────────────────
    if t_std is not None and t_std > 8:
        findings.append({
            "label":  "Variabilité Thermique",
            "value":  f"σ = {t_std:.1f} °C",
            "status": "WARNING",
            "detail": "Forte variabilité — charge cyclique ou problème de refroidissement",
            "norm":   "IEC 60034-1",
        })
        severity_score += 12

    # ── Trend analysis ────────────────────────────────────────────────
    trend_map = {
        "RISING":  ("WARNING", "Tendance haussière — dégradation thermique en cours (Loi d'Arrhenius: +10°C = ÷2 durée de vie)"),
        "FALLING": ("OK",      "Tendance baissière — refroidissement efficace"),
        "STABLE":  ("OK",      "Température stable"),
    }
    t_status, t_desc = trend_map.get(t_trend, ("OK", "Stable"))
    findings.append({
        "label":  "Tendance Thermique",
        "value":  t_trend,
        "status": t_status,
        "detail": t_desc,
        "norm":   "IEC 60034-1",
    })
    if t_trend == "RISING":
        severity_score += 20

    # ── Fault-specific thermal analysis ──────────────────────────────
    thermal_faults = {
        "Insulation Fault": "Température élevée cohérente avec défaut isolation — test de résistance d'isolation recommandé (> 100 MΩ normal)",
        "Overload":         "Échauffement par surcharge — réduire la charge ou vérifier le refroidissement",
        "Bearing Wear":     "Température roulement en hausse — frottement mécanique, vérifier lubrification",
    }
    if fault in thermal_faults:
        findings.append({
            "label":  "Corrélation Défaut",
            "value":  fault,
            "status": "WARNING",
            "detail": thermal_faults[fault],
            "norm":   "IEC 60034-1",
        })
        severity_score += 8

    # ── Severity mapping ─────────────────────────────────────────────
    if severity_score >= 55:
        severity = "CRITICAL"
    elif severity_score >= 30:
        severity = "HIGH"
    elif severity_score >= 12:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    conclusions = {
        "CRITICAL": "Température critique. Risque immédiat de dégradation d'isolation (IEC 60034). Intervenir d'urgence.",
        "HIGH":     "Température élevée significative. Inspection thermique dans les 7 jours. Vérifier le refroidissement.",
        "MEDIUM":   "Légère élévation thermique. Surveiller la tendance. Vérifier la lubrification.",
        "LOW":      "Température dans les limites IEC 60034 Classe B. Aucune anomalie thermique détectée.",
    }

    return {
        "agent_id":   "thermal",
        "title":      "Agent Thermique",
        "icon":       "🌡️",
        "domain":     "Température · Isolation · Refroidissement · IEC 60034",
        "severity":   severity,
        "findings":   findings,
        "conclusion": conclusions[severity],
        "confidence": min(95, 55 + severity_score),
        "norm_refs":  ["IEC 60034-1", "IEC 60034-14"],
    }
