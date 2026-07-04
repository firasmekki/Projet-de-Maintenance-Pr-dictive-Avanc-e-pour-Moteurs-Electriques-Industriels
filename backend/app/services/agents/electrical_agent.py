"""Agent Électrique — analyse courant, tension, puissance, facteur de puissance, THD, charge."""
from __future__ import annotations
from typing import Any


def analyze(analysis: dict[str, Any]) -> dict[str, Any]:
    stats   = analysis.get("statistics", {})
    trends  = analysis.get("trends",     {})
    fault   = analysis.get("fault",      "No Fault")

    def s(key: str, field: str = "mean") -> float | None:
        d = stats.get(key)
        return d[field] if d else None

    findings:      list[dict] = []
    severity_score = 0

    # ── Load factor ──────────────────────────────────────────────────────
    lo_mean = s("load")
    if lo_mean is not None:
        if lo_mean > 0.95:
            findings.append({
                "label":  "Charge Moteur",
                "value":  f"{lo_mean*100:.1f}%",
                "status": "CRITICAL",
                "detail": "Surcharge critique — dépasse 95% de la capacité nominale",
                "norm":   "IEC 60034-1",
            })
            severity_score += 40
        elif lo_mean > 0.90:
            findings.append({
                "label":  "Charge Moteur",
                "value":  f"{lo_mean*100:.1f}%",
                "status": "WARNING",
                "detail": "Charge élevée — surveiller le courant et la température",
                "norm":   "IEC 60034-1",
            })
            severity_score += 20
        else:
            findings.append({
                "label":  "Charge Moteur",
                "value":  f"{lo_mean*100:.1f}%",
                "status": "OK",
                "detail": "Charge dans les limites nominales",
                "norm":   "IEC 60034-1",
            })

    # ── Power factor (cos φ) ─────────────────────────────────────────────
    pf_mean = s("power_factor")
    if pf_mean is not None:
        if pf_mean < 0.70:
            findings.append({
                "label":  "Facteur de Puissance (cos φ)",
                "value":  f"{pf_mean:.3f}",
                "status": "CRITICAL",
                "detail": "Très dégradé — pertes élevées, risque surcharge transformateur",
                "norm":   "IEC 60034-30",
            })
            severity_score += 40
        elif pf_mean < 0.80:
            findings.append({
                "label":  "Facteur de Puissance (cos φ)",
                "value":  f"{pf_mean:.3f}",
                "status": "WARNING",
                "detail": "Dégradé — vérifier la compensation de réactif",
                "norm":   "IEC 60034-30",
            })
            severity_score += 22
        elif pf_mean < 0.87:
            findings.append({
                "label":  "Facteur de Puissance (cos φ)",
                "value":  f"{pf_mean:.3f}",
                "status": "WARNING",
                "detail": "Légèrement bas — surveillance recommandée",
                "norm":   "IEC 60034-30",
            })
            severity_score += 8
        else:
            findings.append({
                "label":  "Facteur de Puissance (cos φ)",
                "value":  f"{pf_mean:.3f}",
                "status": "OK",
                "detail": "Facteur de puissance dans les normes IEC 60034-30",
                "norm":   "IEC 60034-30",
            })

    # ── THD (Total Harmonic Distortion) ──────────────────────────────────
    thd_mean = s("thd")
    if thd_mean is not None:
        if thd_mean > 8.0:
            findings.append({
                "label":  "THD",
                "value":  f"{thd_mean:.1f}%",
                "status": "CRITICAL",
                "detail": "Distorsion harmonique élevée — surchauffe bobinage, usure accélérée",
                "norm":   "IEEE 519",
            })
            severity_score += 30
        elif thd_mean > 5.0:
            findings.append({
                "label":  "THD",
                "value":  f"{thd_mean:.1f}%",
                "status": "WARNING",
                "detail": "THD au-dessus du seuil recommandé (5% IEEE 519)",
                "norm":   "IEEE 519",
            })
            severity_score += 15
        else:
            findings.append({
                "label":  "THD",
                "value":  f"{thd_mean:.1f}%",
                "status": "OK",
                "detail": "Distorsion harmonique dans les limites (< 5% IEEE 519)",
                "norm":   "IEEE 519",
            })

    # ── Current analysis ─────────────────────────────────────────────────
    cr_mean = s("current")
    if cr_mean is not None:
        cr_trend = trends.get("current", "STABLE")
        rated    = analysis.get("estimated_rated_current")
        if rated and rated > 0:
            ratio = cr_mean / rated
            if ratio > 1.15:
                findings.append({
                    "label":  "Courant (ratio)",
                    "value":  f"{cr_mean:.1f} A ({ratio:.2f}×In)",
                    "status": "CRITICAL",
                    "detail": f"+{int((ratio-1)*100)}% au-dessus du nominal — surcharge",
                    "norm":   "IEC 60034-1",
                })
                severity_score += 30
            elif ratio > 1.05:
                findings.append({
                    "label":  "Courant (ratio)",
                    "value":  f"{cr_mean:.1f} A ({ratio:.2f}×In)",
                    "status": "WARNING",
                    "detail": f"+{int((ratio-1)*100)}% au-dessus du nominal",
                    "norm":   "IEC 60034-1",
                })
                severity_score += 12
            else:
                findings.append({
                    "label":  "Courant",
                    "value":  f"{cr_mean:.1f} A",
                    "status": "OK",
                    "detail": "Dans les limites nominales",
                    "norm":   "IEC 60034-1",
                })
        else:
            findings.append({
                "label":  "Courant",
                "value":  f"{cr_mean:.1f} A",
                "status": "OK" if cr_trend == "STABLE" else "WARNING",
                "detail": f"Tendance : {cr_trend}",
                "norm":   "IEC 60034-1",
            })
        if cr_trend == "RISING":
            severity_score += 12

    # ── Voltage / unbalance ───────────────────────────────────────────────
    v_mean = s("voltage")
    v_max  = s("voltage", "max")
    v_min  = s("voltage", "min")
    if v_mean is not None and v_max is not None and v_min is not None:
        unbalance_pct = ((v_max - v_min) / max(v_mean, 1)) * 100
        if unbalance_pct > 3.0:
            findings.append({
                "label":  "Déséquilibre Tension",
                "value":  f"{unbalance_pct:.1f}%",
                "status": "CRITICAL" if unbalance_pct > 5 else "WARNING",
                "detail": "Déséquilibre inter-phases — hausse courant × 3–10",
                "norm":   "NEMA MG-1",
            })
            severity_score += 20
        else:
            findings.append({
                "label":  "Tension",
                "value":  f"{v_mean:.1f} V",
                "status": "OK",
                "detail": "Tension équilibrée",
                "norm":   "IEC 60038",
            })

    # ── Power trend ───────────────────────────────────────────────────────
    p_mean  = s("power")
    p_trend = trends.get("power", "STABLE")
    if p_mean is not None:
        findings.append({
            "label":  "Puissance Consommée",
            "value":  f"{p_mean:.1f} kW",
            "status": "WARNING" if p_trend == "RISING" else "OK",
            "detail": f"Tendance : {p_trend}",
            "norm":   "IEEE 112",
        })
        if p_trend == "RISING":
            severity_score += 10

    # ── Severity mapping ──────────────────────────────────────────────────
    if severity_score >= 60:
        severity = "CRITICAL"
    elif severity_score >= 35:
        severity = "HIGH"
    elif severity_score >= 15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    conclusions = {
        "CRITICAL": "Anomalie électrique critique. Surcharge, cos φ dégradé ou THD excessif. Arrêt préventif et inspection immédiate.",
        "HIGH":     "Anomalie électrique significative. Planifier inspection électrique dans les 7 jours.",
        "MEDIUM":   "Légère déviation électrique. Surveillance renforcée recommandée.",
        "LOW":      "Paramètres électriques dans les normes IEC 60034. Aucune anomalie électrique détectée.",
    }

    return {
        "agent_id":   "electrical",
        "title":      "Agent Électrique",
        "icon":       "⚡",
        "domain":     "Charge · Cos φ · THD · Courant · Tension · Puissance",
        "severity":   severity,
        "findings":   findings,
        "conclusion": conclusions[severity],
        "confidence": min(95, 50 + severity_score),
        "norm_refs":  ["IEC 60034-1", "IEC 60034-30", "IEEE 112", "IEEE 519", "NEMA MG-1"],
    }
