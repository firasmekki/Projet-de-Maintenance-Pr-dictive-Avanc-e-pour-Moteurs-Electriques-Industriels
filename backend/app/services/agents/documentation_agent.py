"""Agent Documentation — expert normes ISO/IEC, manuels constructeurs, procédures."""
from __future__ import annotations
from typing import Any


_FAULT_DOCS: dict[str, dict] = {
    "Bearing Wear": {
        "standard":   "ISO 15243",
        "procedure":  "Inspection selon ISO 15243 — Mode de défaillance : fatigue de surface (pitting). Vérifier BPFI/BPFO/BSF en analyse FFT.",
        "interval":   "Inspection toutes les 500h ou à chaque dépassement ISO Zone B (> 2.3 mm/s)",
        "references": ["ISO 15243", "ISO 10816", "SKF Bearing Maintenance Handbook"],
    },
    "Misalignment": {
        "standard":   "ISO 10816 / ANSI S2.75",
        "procedure":  "Alignement laser requis (tolérance ± 0.05 mm). Vérifier soft-foot. Composante 2×RPM dominante selon ANSI S2.75.",
        "interval":   "Vérification après chaque intervention mécanique ou vibrations > 4.5 mm/s",
        "references": ["ISO 10816", "ANSI S2.75", "Ludeca Shaft Alignment Manual"],
    },
    "Unbalance": {
        "standard":   "ISO 1940-1",
        "procedure":  "Équilibrage dynamique Grade G2.5 (ISO 1940-1). Composante 1×RPM dominante. Nettoyer surfaces ventilateur.",
        "interval":   "Équilibrage lors de chaque remplacement de rotor ou quand vibrations > 2.3 mm/s",
        "references": ["ISO 1940-1", "ISO 10816", "Schenck Balancing Manual"],
    },
    "Rotor Fault": {
        "standard":   "IEC 60034-4",
        "procedure":  "Analyse MCSA (Motor Current Signature Analysis). Bandes à f ± 2s×f. Test à cage d'écureuil selon IEC 60034-4.",
        "interval":   "Surveillance courant mensuelle si défaut suspecté",
        "references": ["IEC 60034-4", "IEEE 1418", "EPRI Motor Diagnostics Guide"],
    },
    "Insulation Fault": {
        "standard":   "IEC 60034-27 / IEEE 43",
        "procedure":  "Test résistance isolation Megohmmètre. IP = R10min/R1min > 2 (IEEE 43). Indice de polarisation selon IEC 60034-27.",
        "interval":   "Test annuel préventif ou si température > seuil classe isolation",
        "references": ["IEC 60034-27", "IEEE 43", "IEC 60034-1 Thermal Class"],
    },
    "Overload": {
        "standard":   "IEC 60034-1 / NEMA MG-1",
        "procedure":  "Vérifier service factor (NEMA MG-1). Courant > 1.15×In pendant > 1h → déclenche relais thermique (IEC 60947-4).",
        "interval":   "Vérification mensuelle du courant moyen vs nominal",
        "references": ["IEC 60034-1", "NEMA MG-1", "IEC 60947-4"],
    },
    "Early Degradation": {
        "standard":   "ISO 13373",
        "procedure":  "Programme de surveillance renforcé selon ISO 13373. Mesures toutes les 4h. Analyse tendance vibratoire.",
        "interval":   "Inspection préventive dans les 30 jours (ISO 13373 Niveau 2)",
        "references": ["ISO 13373", "ISO 17359", "MIMOSA CRIS Standard"],
    },
    "No Fault": {
        "standard":   "ISO 13373 / ISO 17359",
        "procedure":  "Surveillance de routine conforme ISO 17359. Programme de maintenance préventive selon ISO 13373.",
        "interval":   "Révision semestrielle ou annuelle selon criticité de l'équipement",
        "references": ["ISO 17359", "ISO 13373", "IEC 60034"],
    },
}

_MANUFACTURER_INFO: dict[str, dict] = {
    "Siemens":          {"contact": "support.industry.siemens.com", "hotline": "+49 911 895 7222"},
    "ABB":              {"contact": "motors.abb.com",               "hotline": "+41 43 317 7111"},
    "Schneider Electric":{"contact": "se.com/support",             "hotline": "+33 1 41 29 70 00"},
    "WEG":              {"contact": "weg.net/br/suporte",           "hotline": "+55 47 3276 4000"},
    "SEW-Eurodrive":    {"contact": "sew-eurodrive.com",           "hotline": "+49 7251 75 0"},
    "Leroy-Somer":      {"contact": "leroy-somer.com",             "hotline": "+33 5 45 64 45 64"},
}

_ISO_VIBRATION: dict[str, dict] = {
    "Zone A": {"threshold": "< 2.3 mm/s",  "status": "OK",       "description": "Neuf ou récemment révisé — nominal"},
    "Zone B": {"threshold": "2.3–4.5 mm/s","status": "OK",       "description": "Acceptable pour fonctionnement long terme"},
    "Zone C": {"threshold": "4.5–7.1 mm/s","status": "WARNING",  "description": "Alarme — maintenance à planifier rapidement"},
    "Zone D": {"threshold": "> 7.1 mm/s",  "status": "CRITICAL", "description": "Danger — arrêt recommandé immédiatement"},
}

_THERMAL_CLASSES: dict[str, dict] = {
    "A": {"max_temp": 105, "norm": "IEC 60034-1"},
    "B": {"max_temp": 130, "norm": "IEC 60034-1"},
    "F": {"max_temp": 155, "norm": "IEC 60034-1"},
    "H": {"max_temp": 180, "norm": "IEC 60034-1"},
}


def analyze(analysis: dict[str, Any]) -> dict[str, Any]:
    fault    = analysis.get("fault", "No Fault")
    stats    = analysis.get("statistics", {})
    trends   = analysis.get("trends", {})
    iso_zone = analysis.get("iso_zone", "Zone A")
    mp       = analysis.get("motor_profile") or {}

    findings:      list[dict] = []
    severity_score = 0
    references:    list[str] = []

    # ── ISO 10816/20816 vibration compliance ──────────────────────────
    zone_info = _ISO_VIBRATION.get(iso_zone, _ISO_VIBRATION["Zone A"])
    vib_stat  = stats.get("vibration")
    if vib_stat:
        vib_mean = vib_stat.get("mean", 0)
        vib_max  = vib_stat.get("max",  0)
        findings.append({
            "label":  f"ISO 20816 — {iso_zone}",
            "value":  f"moy {vib_mean:.2f} / max {vib_max:.2f} mm/s",
            "status": zone_info["status"],
            "detail": f"{zone_info['threshold']} — {zone_info['description']}",
            "norm":   "ISO 10816 / ISO 20816",
        })
        if iso_zone == "Zone D":     severity_score += 50
        elif iso_zone == "Zone C":   severity_score += 30
        elif iso_zone == "Zone B":   severity_score += 10
        references += ["ISO 10816", "ISO 20816"]

    # ── IEC 60034-1 thermal compliance ────────────────────────────────
    temp_stat = stats.get("temperature")
    if temp_stat:
        temp_mean = temp_stat.get("mean", 0)
        temp_max  = temp_stat.get("max",  0)
        ins_class = mp.get("insulation_class", "B").split(" ")[0] if mp.get("insulation_class") else "B"
        thermal   = _THERMAL_CLASSES.get(ins_class, _THERMAL_CLASSES["B"])
        pct_used  = round(temp_max / thermal["max_temp"] * 100, 1)
        status    = "CRITICAL" if pct_used > 85 else "WARNING" if pct_used > 70 else "OK"
        findings.append({
            "label":  f"IEC 60034-1 — Classe {ins_class} ({thermal['max_temp']}°C max)",
            "value":  f"max {temp_max:.1f}°C ({pct_used}% du seuil)",
            "status": status,
            "detail": f"Règle d'Arrhenius : chaque +10°C divise la durée de vie d'isolation par 2",
            "norm":   "IEC 60034-1",
        })
        if pct_used > 85: severity_score += 40
        elif pct_used > 70: severity_score += 20
        references += ["IEC 60034-1"]

    # ── Power factor compliance ───────────────────────────────────────
    pf_stat = stats.get("power_factor")
    if pf_stat:
        pf_mean = pf_stat.get("mean", 0)
        status  = "CRITICAL" if pf_mean < 0.70 else "WARNING" if pf_mean < 0.80 else "OK"
        detail  = (
            "En-dessous du minimum IEC 60034-30 — compensation de réactif recommandée"
            if pf_mean < 0.80 else
            "Conforme aux exigences IEC 60034-30 (cos φ > 0.80)"
        )
        findings.append({
            "label":  "IEC 60034-30 — Facteur de puissance",
            "value":  f"cos φ = {pf_mean:.3f}",
            "status": status,
            "detail": detail,
            "norm":   "IEC 60034-30",
        })
        if pf_mean < 0.75: severity_score += 25
        references += ["IEC 60034-30"]

    # ── Fault-specific documentation ──────────────────────────────────
    doc = _FAULT_DOCS.get(fault, _FAULT_DOCS["No Fault"])
    findings.append({
        "label":  f"Procédure — {fault}",
        "value":  doc["standard"],
        "status": "WARNING" if fault != "No Fault" else "OK",
        "detail": doc["procedure"],
        "norm":   doc["standard"],
    })
    findings.append({
        "label":  "Intervalle d'inspection",
        "value":  doc["interval"][:40],
        "status": "OK",
        "detail": doc["interval"],
        "norm":   doc["references"][0] if doc["references"] else "",
    })
    references += doc["references"]
    if fault not in ("No Fault",): severity_score += 15

    # ── Manufacturer documentation ────────────────────────────────────
    manufacturer = mp.get("manufacturer", "")
    if manufacturer and manufacturer in _MANUFACTURER_INFO:
        mfr_info = _MANUFACTURER_INFO[manufacturer]
        findings.append({
            "label":  f"{manufacturer} — Support technique",
            "value":  "Documentation disponible",
            "status": "OK",
            "detail": f"Contact : {mfr_info['contact']}  |  Hotline : {mfr_info['hotline']}",
            "norm":   f"{manufacturer} Technical Documentation",
        })

    # ── IEEE 519 THD compliance ───────────────────────────────────────
    thd_stat = stats.get("thd")
    if thd_stat:
        thd_mean = thd_stat.get("mean", 0)
        status   = "CRITICAL" if thd_mean > 8 else "WARNING" if thd_mean > 5 else "OK"
        findings.append({
            "label":  "IEEE 519 — THD",
            "value":  f"{thd_mean:.1f}%",
            "status": status,
            "detail": f"Seuil IEEE 519 : < 5%. THD > 5% → échauffement supplémentaire des bobinages.",
            "norm":   "IEEE 519",
        })
        if thd_mean > 8: severity_score += 25
        references += ["IEEE 519"]

    # ── Severity mapping ─────────────────────────────────────────────
    if severity_score >= 60:   severity = "CRITICAL"
    elif severity_score >= 35: severity = "HIGH"
    elif severity_score >= 15: severity = "MEDIUM"
    else:                      severity = "LOW"

    conclusions = {
        "CRITICAL": "Plusieurs non-conformités aux normes ISO/IEC détectées. Intervention urgente requise pour rester dans les tolérances normatives.",
        "HIGH":     "Non-conformité significative aux normes industrielles. Planifier inspection et maintenance sous 7 jours.",
        "MEDIUM":   "Légers dépassements de seuils normatifs. Surveiller et planifier une maintenance préventive.",
        "LOW":      "Équipement conforme aux normes ISO 10816, IEC 60034 et IEEE 519. Poursuivre la surveillance standard.",
    }

    # Deduplicate references
    unique_refs = list(dict.fromkeys(references))

    return {
        "agent_id":   "documentation",
        "title":      "Agent Documentation",
        "icon":       "📚",
        "domain":     "Normes ISO/IEC · Manuels Constructeurs · Procédures",
        "severity":   severity,
        "findings":   findings,
        "conclusion": conclusions[severity],
        "confidence": min(95, 55 + severity_score),
        "norm_refs":  unique_refs[:8],
        "fault_doc":  doc,
    }
