"""Generate AI narrative reports via Ollama/Qwen with template fallback."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_OLLAMA_URL  = "http://host.docker.internal:11434/api/generate"
_OLLAMA_TAGS_URL = "http://host.docker.internal:11434/api/tags"
_QWEN_MODELS = ["qwen2.5:7b", "qwen2.5:1.5b", "qwen:7b", "qwen2:7b"]
_TIMEOUT     = 45.0


class AINarrativeService:
    """Generate a professional diagnostic narrative for an analysis result."""

    def generate(self, filename: str, analysis: dict[str, Any]) -> str:
        try:
            return self._ollama_generate(filename, analysis)
        except Exception as exc:
            logger.info("Ollama unavailable (%s) — using template narrative", exc)
            return self._template_narrative(filename, analysis)

    # ------------------------------------------------------------------
    # Ollama / Qwen path
    # ------------------------------------------------------------------

    def _ollama_generate(self, filename: str, analysis: dict[str, Any]) -> str:
        prompt = self._build_prompt(filename, analysis)
        available = self._detect_model()
        if available is None:
            raise RuntimeError("No Ollama model available")

        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                _OLLAMA_URL,
                json={"model": available, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "").strip()
            if not text:
                raise ValueError("Empty response from Ollama")
            return text

    def _detect_model(self) -> str | None:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(_OLLAMA_TAGS_URL)
                resp.raise_for_status()
                running = {m["name"] for m in resp.json().get("models", [])}
                for candidate in _QWEN_MODELS:
                    if candidate in running:
                        return candidate
        except Exception:
            pass
        return None

    def _build_prompt(self, filename: str, analysis: dict[str, Any]) -> str:
        stats   = analysis.get("statistics", {})
        trends  = analysis.get("trends",     {})
        risk    = analysis.get("risk",        {})
        anomaly = analysis.get("anomaly",     {})
        fault   = analysis.get("fault",       "No Fault")
        health  = analysis.get("health_score", 100)
        sev     = analysis.get("severity",    "LOW")

        def stat_line(key: str) -> str:
            s = stats.get(key)
            if not s:
                return "N/A"
            return f"avg={s['mean']}, max={s['max']}, std={s['std']}"

        # ISO vibration zone
        vib_stats = stats.get("vibration")
        vib_mean  = vib_stats["mean"] if vib_stats else 0
        if vib_mean > 7.1:
            iso_zone = "Zone D (DANGER — arrêt recommandé)"
        elif vib_mean > 4.5:
            iso_zone = "Zone C (ALARME)"
        elif vib_mean > 2.3:
            iso_zone = "Zone B (surveillance)"
        else:
            iso_zone = "Zone A (normal)"

        # Load and pf info
        lo_stat = stats.get("load")
        pf_stat = stats.get("power_factor")
        lo_line = f"avg={lo_stat['mean']:.2f} ({lo_stat['mean']*100:.1f}%)" if lo_stat else "N/A"
        pf_line = f"avg={pf_stat['mean']:.3f}" if pf_stat else "N/A"
        thd_stat = stats.get("thd")
        thd_line = f"avg={thd_stat['mean']:.1f}%" if thd_stat else "N/A"

        # Fault distribution top 3
        fd = analysis.get("fault_distribution", [])
        fd_sorted = sorted(fd, key=lambda x: -x.get("value", 0))
        fd_total  = max(sum(d.get("value", 0) for d in fd_sorted), 1)
        fd_lines  = "\n".join(
            f"  - {d['name']}: {int(d['value']*100/fd_total)}%"
            for d in fd_sorted[:4]
        ) or "  N/A"

        no_fault_instruction = ""
        if fault != "No Fault":
            no_fault_instruction = (
                f"\nCRITICAL INSTRUCTION: The primary fault is '{fault}' with {analysis.get('confidence', 0)}% confidence. "
                f"You MUST write the report focusing on this fault. "
                f"DO NOT say 'no fault detected' or 'normal operation'. "
                f"The motor is NOT operating normally."
            )

        return f"""You are an expert industrial AI engineer specializing in motor diagnostics and predictive maintenance.
Write a professional diagnostic report in English based on the following analysis results.
{no_fault_instruction}

=== MOTOR DIAGNOSTIC DATA ===
Dataset: {filename}
Health Score: {health}/100 — {analysis.get('health_status', 'N/A')}
Primary Fault: {fault} (Confidence: {analysis.get('confidence', 0)}%)
Severity: {sev}
Risk Level: {analysis.get('risk_level', 'N/A')}
ISO 10816 Vibration Zone: {iso_zone}

SENSOR STATISTICS:
- Temperature: {stat_line('temperature')} °C
- Vibration: {stat_line('vibration')} mm/s
- Current: {stat_line('current')} A
- Voltage: {stat_line('voltage')} V
- Power: {stat_line('power')} kW
- Load Factor: {lo_line}
- Power Factor: {pf_line}
- THD: {thd_line}

TRENDS:
- Temperature: {trends.get('temperature', 'STABLE')}
- Vibration: {trends.get('vibration', 'STABLE')}
- Current: {trends.get('current', 'STABLE')}
- Power: {trends.get('power', 'STABLE')}

RISK PREDICTION:
- 7-day failure probability: {risk.get('days_7', 0)}%
- 30-day failure probability: {risk.get('days_30', 0)}%

ANOMALY DETECTION:
- Anomalous readings: {anomaly.get('count', 0)} ({anomaly.get('percentage', 0):.1f}%)

FAULT PROBABILITY DISTRIBUTION:
{fd_lines}
==============================

Write a professional 5-section diagnostic report. Each section is a prose paragraph (NO markdown, NO bullet points, NO headers):
1. ANALYSIS SUMMARY — overall motor condition, health score interpretation
2. KEY OBSERVATIONS — notable sensor readings, trends, ISO zone status
3. FAULT DIAGNOSIS — detailed technical explanation of '{fault}', its causes and mechanisms
4. RISK ASSESSMENT — failure timeline based on {risk.get('days_7', 0)}% 7-day and {risk.get('days_30', 0)}% 30-day probabilities
5. RECOMMENDED ACTIONS — specific maintenance steps with urgency timeline

Be specific and technical. Reference actual values and norms (ISO 10816, IEC 60034)."""

    # ------------------------------------------------------------------
    # Template fallback
    # ------------------------------------------------------------------

    def _template_narrative(self, filename: str, analysis: dict[str, Any]) -> str:
        stats   = analysis.get("statistics", {})
        trends  = analysis.get("trends", {})
        risk    = analysis.get("risk", {})
        anomaly = analysis.get("anomaly", {})
        fault   = analysis.get("fault", "No Fault")
        health  = analysis.get("health_score", 100)
        status  = analysis.get("health_status", "Healthy")
        conf    = analysis.get("confidence", 0)
        sev     = analysis.get("severity", "LOW")
        rec     = analysis.get("recommendation", "")
        r7      = risk.get("days_7", 0)
        r30     = risk.get("days_30", 0)
        n_anom  = anomaly.get("count", 0)
        pct     = anomaly.get("percentage", 0)

        def m(key: str, field: str = "mean") -> str:
            s = stats.get(key)
            return f"{s[field]:.2f}" if s else "N/A"

        def tr(key: str) -> str:
            return trends.get(key, "STABLE").capitalize()

        sections = []

        # Section 1 — Summary
        sections.append(
            f"ANALYSIS SUMMARY\n\n"
            f"The uploaded dataset '{filename}' has been processed through the ORBIT AI diagnostic engine. "
            f"The motor is currently operating at a health score of {health}/100, classified as {status}. "
            f"{'No critical faults were identified during this analysis period.' if fault == 'No Fault' else f'The primary diagnostic finding is {fault} with a confidence level of {conf}% and {sev} severity.'} "
            f"A total of {n_anom} anomalous readings were detected, representing {pct:.1f}% of the dataset."
        )

        # Section 2 — Key Observations
        temp_obs = f"Temperature data averaged {m('temperature')}°C with a peak of {m('temperature', 'max')}°C and shows a {tr('temperature')} trend."
        vib_obs  = f"Vibration levels averaged {m('vibration')} mm/s (peak: {m('vibration', 'max')} mm/s) and are {tr('vibration')}."
        curr_obs = f"Current consumption averaged {m('current')} A with a {tr('current')} trend."
        sections.append(
            f"KEY OBSERVATIONS\n\n"
            f"{temp_obs} {vib_obs} {curr_obs} "
            f"{'Multiple sensors exhibit rising trends simultaneously, which is a strong indicator of accelerating degradation.' if sum(1 for k in ['temperature','vibration','current'] if trends.get(k) == 'RISING') >= 2 else 'Sensor trends are within acceptable variation ranges.'}"
        )

        # Section 3 — Fault Diagnosis
        fault_explanations = {
            "Bearing Wear":     f"Bearing wear is characterised by elevated vibration and temperature readings. The combination of high vibration ({m('vibration')} mm/s average) and elevated temperature ({m('temperature')}°C average) is consistent with mechanical friction in the bearing assembly.",
            "Misalignment":     f"Shaft misalignment is indicated by very high vibration levels ({m('vibration')} mm/s average) while current and temperature remain relatively normal, which is the classic signature of mechanical misalignment.",
            "Unbalance":        f"Rotor unbalance is suggested by high vibration levels ({m('vibration')} mm/s average) with normal thermal and electrical readings, pointing to a mechanical mass distribution issue.",
            "Rotor Fault":      f"Rotor electrical faults manifest as elevated current consumption ({m('current')} A average) with moderate vibration, consistent with rotor bar defects or eccentricity.",
            "Insulation Fault": f"Winding insulation degradation is indicated by high operating temperature ({m('temperature')}°C average) combined with elevated current, suggesting increased resistive losses in the stator winding.",
            "Overload":         f"Motor overload is confirmed by very high current ({m('current')} A average) combined with elevated temperature ({m('temperature')}°C average), indicating the motor is operating beyond its rated capacity.",
            "No Fault":         "No specific fault pattern was detected above the diagnostic confidence threshold. The motor appears to be operating within its normal performance envelope based on the sensor data provided.",
        }
        sections.append(
            f"FAULT DIAGNOSIS\n\n"
            f"{fault_explanations.get(fault, fault_explanations['No Fault'])} "
            f"{'The diagnostic confidence of ' + str(conf) + '% provides ' + ('high' if conf >= 75 else 'moderate') + ' certainty in this assessment.' if fault != 'No Fault' else ''}"
        )

        # Section 4 — Risk Assessment
        urgency = "immediate" if r7 >= 70 else "urgent" if r7 >= 40 else "scheduled" if r7 >= 20 else "routine"
        sections.append(
            f"RISK ASSESSMENT\n\n"
            f"The estimated probability of motor failure is {r7:.1f}% within the next 7 days and {r30:.1f}% within 30 days. "
            f"This represents a {analysis.get('risk_level', 'LOW')} risk level requiring {urgency} attention. "
            f"{'The degrading trend in multiple sensors accelerates the failure timeline and increases the urgency of intervention.' if sum(1 for k in trends.values() if k == 'RISING') >= 2 else 'Current sensor trends are monitored and factored into this risk estimate.'} "
            f"{'If no corrective action is taken, the probability of failure within 30 days is significant.' if r30 >= 50 else 'With appropriate monitoring and maintenance, the risk of near-term failure can be managed.'}"
        )

        # Section 5 — Recommendations
        sections.append(
            f"RECOMMENDED ACTIONS\n\n"
            f"{rec} "
            f"{'Given the current risk level, maintenance should be prioritised and scheduled within the next 48 hours.' if r7 >= 40 else 'Maintenance should be included in the next planned service window.'} "
            f"Increase sensor monitoring frequency to at least once per hour during this period. "
            f"Document all findings and maintenance actions in the motor maintenance log for trend tracking and future reference."
        )

        return "\n\n".join(sections)
