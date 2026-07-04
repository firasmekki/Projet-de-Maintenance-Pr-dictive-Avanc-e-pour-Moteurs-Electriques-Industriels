"""MultiAgentService — orchestre les 4 agents spécialisés + coordinateur."""
from __future__ import annotations
from typing import Any

from app.services.agents import (
    documentation_agent,
    electrical_agent,
    vibration_agent,
    thermal_agent,
    coordinator_agent,
)


class MultiAgentService:

    def analyze(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Run all 4 specialist agents then synthesize with coordinator."""
        agents = [
            electrical_agent.analyze(analysis),
            vibration_agent.analyze(analysis),
            thermal_agent.analyze(analysis),
            documentation_agent.analyze(analysis),
        ]
        synthesis = coordinator_agent.synthesize(agents, analysis)
        return {"agents": agents, "synthesis": synthesis}
