"""Agent Coordinateur — fusionne les conclusions des agents spécialisés."""
from __future__ import annotations
from typing import Any

_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
_SEVERITY_FR   = {"LOW": "FAIBLE", "MEDIUM": "MOYEN", "HIGH": "ÉLEVÉ", "CRITICAL": "CRITIQUE"}

_FAULT_FR = {
    "No Fault":          "Aucun Défaut",
    "Early Degradation": "Dégradation Précoce",
    "Bearing Wear":      "Usure des Roulements",
    "Misalignment":      "Désalignement",
    "Unbalance":         "Déséquilibre Rotor",
    "Rotor Fault":       "Défaut Rotor",
    "Insulation Fault":  "Défaut d'Isolation",
    "Overload":          "Surcharge",
}


def synthesize(agent_results: list[dict[str, Any]], analysis: dict[str, Any]) -> dict[str, Any]:
    fault        = analysis.get("fault", "No Fault")
    health       = analysis.get("health_score", 100)
    risk_7d      = analysis.get("risk", {}).get("days_7", 0)
    risk_30d     = analysis.get("risk", {}).get("days_30", 0)
    confidence   = analysis.get("confidence", 0)

    # ── Determine overall severity ────────────────────────────────────
    severities = [_SEVERITY_RANK.get(a["severity"], 0) for a in agent_results]
    max_sev    = max(severities, default=0)

    # ── Escalation: if 2+ agents are HIGH or CRITICAL → force CRITICAL ──
    high_plus = sum(1 for sv in severities if sv >= 2)
    if high_plus >= 2 and max_sev < 3:
        max_sev = 3
    overall_sev = ["LOW", "MEDIUM", "HIGH", "CRITICAL"][max_sev]

    # ── Priority agent (highest severity) ────────────────────────────
    priority_idx   = severities.index(max(severities))
    priority_agent = agent_results[priority_idx]

    # ── Agent consensus ───────────────────────────────────────────────
    warning_agents   = [a for a in agent_results if _SEVERITY_RANK.get(a["severity"], 0) >= 2]
    n_warning        = len(warning_agents)
    agent_titles     = [a["title"] for a in warning_agents]

    # ── Timeline recommendation ───────────────────────────────────────
    if overall_sev == "CRITICAL" or risk_7d >= 70:
        timeline = "48 heures"
        urgency  = "IMMÉDIATE"
        verdict  = "ARRÊT PRÉVENTIF RECOMMANDÉ"
        color    = "red"
    elif overall_sev == "HIGH" or risk_7d >= 40:
        timeline = "7 jours"
        urgency  = "URGENTE"
        verdict  = "INTERVENTION REQUISE"
        color    = "orange"
    elif overall_sev == "MEDIUM" or risk_7d >= 20:
        timeline = "30 jours"
        urgency  = "PLANIFIÉE"
        verdict  = "MAINTENANCE PRÉVENTIVE"
        color    = "yellow"
    else:
        timeline = "Prochaine révision"
        urgency  = "SURVEILLANCE"
        verdict  = "ÉTAT NOMINAL"
        color    = "green"

    # ── Synthesis narrative ───────────────────────────────────────────
    fault_fr   = _FAULT_FR.get(fault, fault)
    agents_str = " et ".join(agent_titles) if agent_titles else "aucun agent"

    if n_warning == 0:
        narrative = (
            f"Les trois agents spécialisés ne détectent aucune anomalie significative. "
            f"Le moteur fonctionne dans les limites des normes ISO et IEC. "
            f"Score de santé : {health}/100. Risque 30 jours : {risk_30d:.1f}%."
        )
    elif n_warning == 1:
        narrative = (
            f"L'agent {agent_titles[0]} détecte une anomalie ({_SEVERITY_FR.get(overall_sev, overall_sev)}). "
            f"Le défaut identifié est : {fault_fr} avec une confiance de {confidence}%. "
            f"Une intervention {urgency.lower()} dans les {timeline} est recommandée."
        )
    else:
        narrative = (
            f"Consensus multi-agent : {agents_str} convergent vers une anomalie {_SEVERITY_FR.get(overall_sev, overall_sev)}. "
            f"Défaut principal identifié : {fault_fr} (confiance {confidence}%). "
            f"La convergence de {n_warning} agents renforce la fiabilité du diagnostic. "
            f"Intervention {urgency.lower()} dans les {timeline}."
        )

    # ── Action plan ───────────────────────────────────────────────────
    action_plans = {
        "No Fault":          ["Maintenir la surveillance normale", "Prochaine inspection à la révision planifiée"],
        "Early Degradation": ["Augmenter fréquence de mesure (toutes les 4h)", "Inspection préventive dans 30j", "Vérifier lubrification et équilibrage"],
        "Bearing Wear":      ["Inspecter roulements et lubrification", "Mesure vibratoire FFT", "Planifier remplacement si Zone C"],
        "Misalignment":      ["Alignement laser (± 0,05 mm)", "Inspection accouplement", "Vérifier soft foot"],
        "Unbalance":         ["Équilibrage dynamique (ISO 1940-1 G2.5)", "Nettoyer aubes ventilateur", "Vérifier fixations"],
        "Rotor Fault":       ["Analyse MCSA (Motor Current Signature Analysis)", "Inspection barres de cage", "Test de résistance rotor"],
        "Insulation Fault":  ["Test résistance d'isolation (Megohmmètre > 100 MΩ)", "Vérifier refroidissement", "Séchage si humidité détectée"],
        "Overload":          ["Réduire la charge mécanique", "Vérifier dimensionnement moteur", "Inspecter équipement entraîné"],
    }
    actions = action_plans.get(fault, action_plans["No Fault"])

    # ── Consensus table ───────────────────────────────────────────────
    consensus_table = [
        {
            "agent":      a["title"],
            "icon":       a["icon"],
            "severity":   a["severity"],
            "severity_fr": _SEVERITY_FR.get(a["severity"], a["severity"]),
            "confidence": a["confidence"],
        }
        for a in agent_results
    ] + [{
        "agent":      "Coordinateur",
        "icon":       "🎯",
        "severity":   overall_sev,
        "severity_fr": _SEVERITY_FR.get(overall_sev, overall_sev),
        "confidence": confidence,
        "is_coordinator": True,
    }]

    return {
        "verdict":            verdict,
        "urgency":            urgency,
        "color":              color,
        "overall_severity":   overall_sev,
        "timeline":           timeline,
        "priority_agent":     priority_agent["agent_id"],
        "narrative":          narrative,
        "action_plan":        actions,
        "n_agents_warning":   n_warning,
        "n_agents_total":     len(agent_results),
        "consensus_fault":    fault_fr,
        "consensus_confidence": confidence,
        "consensus_table":    consensus_table,
        "high_plus":          high_plus,
    }
