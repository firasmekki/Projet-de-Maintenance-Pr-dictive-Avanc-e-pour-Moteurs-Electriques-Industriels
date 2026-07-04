"""Chatbot service: streams Qwen/Ollama responses for industrial Q&A."""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_OLLAMA_HOST     = "http://host.docker.internal:11434"
_OLLAMA_GENERATE = f"{_OLLAMA_HOST}/api/generate"
_OLLAMA_TAGS     = f"{_OLLAMA_HOST}/api/tags"
_QWEN_MODELS     = [
    "qwen3:8b", "qwen3:4b", "qwen2.5:7b",
    "qwen2.5:1.5b", "qwen:7b", "qwen2:7b",
]

_SYSTEM_PROMPT = """Tu es ORBIT AI, un expert virtuel en maintenance industrielle et diagnostic de moteurs électriques.

Tu maîtrises :
- Défauts moteurs : usure roulements, désalignement, déséquilibre rotor, défauts rotor, défauts isolation, surcharge, dégradation précoce
- Analyse électrique : tension, courant, puissance, facteur de puissance, THD, déséquilibre
- Analyse vibratoire : RMS, FFT, spectres, normes ISO 10816 / ISO 20816
- Analyse thermique : températures roulement, stator, ambiante
- Normes : ISO 10816, ISO 20816, IEC 60034, IEEE 112
- Maintenance préventive et prédictive, évaluation des risques

Règles de réponse :
- Toujours en français
- Technique, précis et argumenté
- Basé sur les données réelles si disponibles
- Orienté vers des actions concrètes
- Maximum 3-4 paragraphes concis"""


class ChatService:

    def stream_response(
        self,
        message:  str,
        history:  list[dict[str, str]],
        context:  dict[str, Any] | None,
        filename: str | None = None,
    ) -> Iterator[str]:
        """Yield SSE-formatted data chunks."""
        try:
            yield from self._ollama_stream(message, history, context, filename)
        except Exception as exc:
            logger.info("Ollama unavailable (%s) — template fallback", exc)
            text = self._template_fallback(message, context)
            yield f"data: {json.dumps({'token': text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    # ── Ollama streaming ────────────────────────────────────────────────

    def _ollama_stream(
        self,
        message:  str,
        history:  list[dict[str, str]],
        context:  dict[str, Any] | None,
        filename: str | None,
    ) -> Iterator[str]:
        model = self._detect_model()
        if model is None:
            raise RuntimeError("No Ollama model available")

        prompt  = self._build_prompt(message, history, context, filename)
        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)

        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST", _OLLAMA_GENERATE,
                json={"model": model, "prompt": prompt, "stream": True},
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        data  = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                        if data.get("done"):
                            yield f"data: {json.dumps({'done': True})}\n\n"
                            return
                    except json.JSONDecodeError:
                        continue

    def _detect_model(self) -> str | None:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp   = client.get(_OLLAMA_TAGS)
                resp.raise_for_status()
                models = {m["name"] for m in resp.json().get("models", [])}
                for candidate in _QWEN_MODELS:
                    if candidate in models:
                        return candidate
        except Exception:
            pass
        return None

    # ── Prompt builder ──────────────────────────────────────────────────

    def _build_prompt(
        self,
        message:  str,
        history:  list[dict[str, str]],
        context:  dict[str, Any] | None,
        filename: str | None,
    ) -> str:
        parts = [_SYSTEM_PROMPT]

        # ── RAG: inject relevant knowledge ──────────────────────────────
        try:
            from app.knowledge.base import search, format_for_prompt
            kb_results = search(message, top_k=2)
            if kb_results:
                parts.append(format_for_prompt(kb_results))
        except Exception:
            pass

        if context:
            parts.append(self._format_context(context, filename))

        for turn in history[-8:]:
            role = "Utilisateur" if turn["role"] == "user" else "ORBIT AI"
            parts.append(f"{role}: {turn['content']}")

        parts.append(f"Utilisateur: {message}")
        parts.append("ORBIT AI:")
        return "\n\n".join(parts)

    def _format_context(self, ctx: dict[str, Any], filename: str | None) -> str:
        analysis = ctx.get("analysis", ctx)
        stats    = analysis.get("statistics", {})
        trends   = analysis.get("trends",     {})
        risk     = analysis.get("risk",       {})
        anomaly  = analysis.get("anomaly",    {})
        timeline = analysis.get("health_timeline", [])
        xai      = analysis.get("xai", [])
        rul      = analysis.get("rul", {})
        rf       = analysis.get("risk_factors", [])
        root_c   = analysis.get("root_causes", [])

        def stat(key: str) -> str:
            s = stats.get(key)
            return f"moy={s['mean']:.1f}, max={s['max']:.1f}" if s else "N/D"

        lines = ["=== DONNÉES MOTEUR ANALYSÉ ==="]
        if filename:
            lines.append(f"Fichier : {filename}")
        lines += [
            f"Score Santé     : {analysis.get('health_score', 'N/D')}/100 — {analysis.get('health_status', 'N/D')}",
            f"Défaut Détecté  : {analysis.get('fault', 'N/D')} (confiance {analysis.get('confidence', 0)}%)",
            f"Sévérité        : {analysis.get('severity', 'N/D')}",
            f"Zone ISO 10816  : {analysis.get('iso_zone', 'N/D')}",
            f"RUL estimé      : {rul.get('value', 'N/D')}",
            f"Température     : {stat('temperature')} °C  |  tendance : {trends.get('temperature', 'N/D')}",
            f"Vibration       : {stat('vibration')} mm/s |  tendance : {trends.get('vibration', 'N/D')}",
            f"Courant         : {stat('current')} A       |  tendance : {trends.get('current', 'N/D')}",
        ]

        pf_s = stats.get("power_factor")
        lo_s = stats.get("load")
        if pf_s:   lines.append(f"Cos φ           : {pf_s['mean']:.3f}")
        if lo_s:   lines.append(f"Charge          : {lo_s['mean']*100:.1f}%")

        lines += [
            f"Risque 7 jours  : {risk.get('days_7', 0):.1f}%",
            f"Risque 30 jours : {risk.get('days_30', 0):.1f}%",
            f"Anomalies       : {anomaly.get('count', 0)} lectures ({anomaly.get('percentage', 0):.1f}%)",
        ]

        if root_c:
            lines.append(f"Causes racines  : {' | '.join(root_c)}")
        if xai:
            top3 = ", ".join(f"{x['feature']} ({x['contribution']}%)" for x in xai[:3])
            lines.append(f"XAI Top-3       : {top3}")
        if rf:
            lines.append(f"Facteurs risque : {' | '.join(rf[:3])}")
        if timeline:
            tl_str = " → ".join(t["phase"] for t in timeline)
            lines.append(f"Chronologie     : {tl_str}")

        lines.append("==============================")
        return "\n".join(lines)

    # ── Template fallback (Ollama absent) ───────────────────────────────

    def _template_fallback(self, message: str, context: dict[str, Any] | None) -> str:
        msg = message.lower()

        if context:
            analysis = context.get("analysis", context)
            fault    = analysis.get("fault", "No Fault")
            health   = analysis.get("health_score", 100)
            risk     = analysis.get("risk", {})
            r7, r30  = risk.get("days_7", 0), risk.get("days_30", 0)
            trends   = analysis.get("trends", {})
            rising   = [k for k, v in trends.items() if v == "RISING"]

            if any(k in msg for k in ["risque", "danger", "panne", "défaillance", "if i do nothing"]):
                urg = "une intervention urgente dans les 48h" if r7 >= 70 else \
                      "une maintenance planifiée dans les 7 jours" if r7 >= 40 else \
                      "une surveillance renforcée et maintenance dans le mois"
                fault_note = ""
                if fault not in ("No Fault", "Early Degradation"):
                    fault_note = f"Le défaut détecté ({fault}) va s'aggraver progressivement sans intervention."
                return (
                    f"Basé sur l'analyse en cours, le risque de défaillance est de **{r7:.1f}%** à 7 jours "
                    f"et **{r30:.1f}%** à 30 jours (score santé : {health}/100).\n\n"
                    f"Si aucune action n'est prise, les tendances actuelles ({', '.join(rising) or 'stables'}) "
                    f"suggèrent une dégradation continue. La recommandation est {urg}.\n\n"
                    f"{fault_note}"
                )

            if any(k in msg for k in ["plan", "action", "faire", "maintenance", "30 jours", "intervention"]):
                return (
                    f"**Plan d'action recommandé — 30 jours :**\n\n"
                    f"**Semaine 1** : Augmenter la fréquence de surveillance (toutes les 4h). "
                    f"Inspection visuelle de {fault if fault not in ('No Fault',) else 'tous les composants'}. "
                    f"Vérifier l'état des roulements et la lubrification.\n\n"
                    f"**Semaine 2** : Maintenance préventive ciblée. "
                    f"{'Remplacement ou inspection des roulements.' if 'Bearing' in fault else 'Vérification alignement et équilibrage.'} "
                    f"Test de résistance d'isolation si température élevée.\n\n"
                    f"**Semaines 3-4** : Validation post-intervention. Mesures vibratoires avant/après. "
                    f"Mise à jour du carnet de maintenance. Ajustement du seuil d'alarme si nécessaire."
                )

            if any(k in msg for k in ["consomm", "courant", "électrique", "puissance", "énergie"]):
                return (
                    f"La surconsommation électrique peut avoir plusieurs causes :\n\n"
                    f"1. **Surcharge mécanique** — le moteur travaille au-delà de sa capacité nominale\n"
                    f"2. **Défaut rotor** — barres cassées créant des pertes supplémentaires (hausse courant + vibrations 2×slip)\n"
                    f"3. **Défaut isolation** — fuites courant dans les bobinages (hausse température)\n"
                    f"4. **Déséquilibre tension** — asymétrie entre phases amplifie les courants\n\n"
                    f"{'Le défaut détecté (' + fault + ') est cohérent avec cette surconsommation.' if fault != 'No Fault' else 'Analyser le spectre des courants (FFT) pour identifier la cause précise.'}"
                )

            if any(k in msg for k in ["vibr", "bruit", "choc"]):
                return (
                    f"Les vibrations élevées détectées (tendance : {trends.get('vibration', 'STABLE')}) "
                    f"peuvent indiquer :\n\n"
                    f"- **Déséquilibre** : vibrations à la fréquence de rotation (1×)\n"
                    f"- **Désalignement** : vibrations à 2× la fréquence de rotation + axiales\n"
                    f"- **Usure roulements** : fréquences BPFI/BPFO caractéristiques\n"
                    f"- **Jeu mécanique** : harmoniques multiples\n\n"
                    f"Selon ISO 10816, pour un moteur > 15 kW : zone A < 2.3 mm/s, zone B 2.3–4.5, zone C (alerte) > 4.5 mm/s."
                )

        # Réponses génériques sans contexte
        if any(k in msg for k in ["roulement", "bearing"]):
            return (
                "L'usure des roulements est le défaut mécanique le plus fréquent (≈40% des défaillances moteur). "
                "Elle se manifeste par une augmentation progressive des vibrations aux fréquences caractéristiques "
                "BPFI (bague intérieure), BPFO (bague extérieure) et BSF (billes), "
                "accompagnée d'une élévation de température par frottement.\n\n"
                "Selon ISO 10816, un niveau > 7 mm/s RMS est critique (Zone D). "
                "La durée de vie L10 se calcule selon la charge, la vitesse et la viscosité du lubrifiant. "
                "La lubrification représente 80% de la durée de vie du roulement."
            )
        if any(k in msg for k in ["iso", "norme", "standard", "10816", "20816"]):
            return (
                "Principales normes pour les moteurs industriels :\n\n"
                "**ISO 10816 / ISO 20816** : Seuils vibratoires par classe de machine. "
                "Pour moteurs > 15 kW sur paliers rigides : Zone A < 2.3, B < 4.5, C < 7.1, D > 7.1 mm/s.\n\n"
                "**IEC 60034** : Caractéristiques électriques des machines tournantes (classes de rendement IE1-IE4).\n\n"
                "**IEEE 112** : Méthodes de mesure du rendement des moteurs asynchrones.\n\n"
                "**ISO 13373** : Surveillance vibratoire et analyse de l'état des machines."
            )
        if any(k in msg for k in ["désalign", "alignement", "misalign"]):
            return (
                "Le désalignement est causé par un mauvais positionnement angulaire ou parallèle entre le moteur "
                "et la charge entraînée. Sa signature vibratoire est caractéristique :\n\n"
                "- Vibrations dominantes à 2× la fréquence de rotation (2×RPM)\n"
                "- Composante axiale importante (ratio axiale/radiale > 0.5)\n"
                "- Harmoniques à 1×, 2×, 3×RPM selon le type de désalignement\n\n"
                "Correction : alignement laser ± 0.05 mm. "
                "Un désalignement non corrigé accélère l'usure des roulements et des accouplements."
            )

        return (
            "Je suis ORBIT AI, votre expert en maintenance industrielle. "
            "Je peux vous aider à :\n\n"
            "• **Analyser un défaut** : roulement, désalignement, déséquilibre, surcharge...\n"
            "• **Évaluer les risques** : probabilité de panne, urgence d'intervention\n"
            "• **Planifier la maintenance** : plan d'action sur 7, 30 jours\n"
            "• **Interpréter les mesures** : vibrations, courant, température\n"
            "• **Appliquer les normes** : ISO 10816, IEC 60034, IEEE 112\n\n"
            "Importez et analysez un dataset pour obtenir des réponses basées sur vos données réelles."
        )
