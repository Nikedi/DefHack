"""Generate FRAGO orders from subordinate observations."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from ..models import FragoOrder, SensorReading
from ..observation_repository import ObservationRepository


class FragoGenerator:
    """Derive high-level FRAGO recommendations from observations."""

    def __init__(self, repository: ObservationRepository) -> None:
        self._repository = repository

    def create_order(
        self,
        objective: Optional[str] = None,
        keywords: Sequence[str] | None = None,
        limit: int = 5,
    ) -> FragoOrder:
        observations = self._select_observations(keywords, limit)
        return FragoOrder(
            mission_overview=self._build_mission_overview(objective, observations),
            situation=self._build_situation(observations),
            execution=self._build_execution(observations, objective),
            sustainment=self._build_sustainment(observations),
            command_and_signal=self._build_command_and_signal(observations),
        )

    def _select_observations(
        self, keywords: Sequence[str] | None, limit: int
    ) -> List[SensorReading]:
        if keywords:
            return self._repository.search(keywords, limit=limit)
        return self._repository.list_recent(limit=limit)

    def _build_mission_overview(
        self, objective: Optional[str], observations: Sequence[SensorReading]
    ) -> str:
        objective_text = objective or "Disrupt enemy tempo and secure the current defensive line."
        if observations:
            timeframe = observations[0].time.strftime("%H%MZ")
            return (
                f"Objective: {objective_text}. Based on {len(observations)} latest reports "
                f"(most recent at {timeframe})."
            )
        return f"Objective: {objective_text}. No fresh observation data; proceed with standard posture."

    def _build_situation(self, observations: Sequence[SensorReading]) -> str:
        if not observations:
            return "No recent enemy activity reported. Maintain current posture and continue reconnaissance."
        lines: List[str] = ["Friendly reconnaissance feeds indicate:"]
        for obs in observations:
            lines.append(
                f"- {obs.time.strftime('%H:%MZ')} {obs.unit or 'Unknown unit'}: {obs.what} (MGRS {obs.mgrs}, confidence {obs.confidence}%)"
            )
        return "\n".join(lines)

    def _build_execution(
        self, observations: Sequence[SensorReading], objective: Optional[str]
    ) -> str:
        if not observations:
            return (
                "1. Maintain current task organization.\n"
                "2. Continue ISR patrols and update FRAGO upon new contact reports.\n"
                "3. Prepare contingency plans aligned with mission objective."
            )
        main_effort = observations[0]
        supporting = observations[1:3]
        lines = [
            f"1. Main Effort: Task lead company to neutralize threat at {main_effort.mgrs} described as {main_effort.what}.",
            "2. Supporting Efforts:",
        ]
        if supporting:
            for idx, obs in enumerate(supporting, start=1):
                lines.append(
                    f"   {idx}. Provide overwatch on {obs.what} (MGRS {obs.mgrs}); relay live updates."
                )
        else:
            lines.append("   a. Maintain reserve ready for rapid reinforcement.")
        lines.append(
            "3. Coordinating Instructions: Synchronize fires to avoid fratricide; respect current no-fire areas."
        )
        if objective:
            lines.append(f"4. Commander intent emphasis: {objective}.")
        return "\n".join(lines)

    def _build_sustainment(self, observations: Sequence[SensorReading]) -> str:
        if any("logistics" in (obs.what or "").lower() for obs in observations):
            return (
                "Resupply window open for 2 hours. Prioritize anti-armor munitions and Class V resupply at the forward logistics node."
            )
        return (
            "Current sustainment posture adequate. Conduct spot checks on ammunition and CASEVAC routes; report shortages immediately."
        )

    def _build_command_and_signal(self, observations: Sequence[SensorReading]) -> str:
        primary_net = "Command Net 01"
        alt_net = "Alt Net 03"
        reports_required = "SALUTE updates every 15 minutes" if observations else "SALUTE updates hourly"
        return (
            f"Primary/Alt Nets: {primary_net} / {alt_net}.\n"
            f"Reports: {reports_required}.\n"
            "CCIR: Immediate report on enemy indirect fire or air threats."
        )
