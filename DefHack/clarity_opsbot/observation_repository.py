"""In-memory repository for subordinate observations (dummy data)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Sequence

from .models import SensorReading


def _build_dummy_observations() -> List[SensorReading]:
    base_time = datetime.now(timezone.utc) - timedelta(hours=1)
    return [
        SensorReading(
            time=base_time + timedelta(minutes=5),
            mgrs="35VLG8472571866",
            what="Platoon-sized infantry element consolidating defensive positions",
            amount=24,
            confidence=85,
            sensor_id=None,
            unit="Alpha Platoon",
            observer_signature="Scout-1",
        ),
        SensorReading(
            time=base_time + timedelta(minutes=18),
            mgrs="35VLG8474371854",
            what="Two MT-LB APCs refueling at tree line",
            amount=2,
            confidence=80,
            sensor_id=None,
            unit="Bravo Squad",
            observer_signature="Raven-3",
        ),
        SensorReading(
            time=base_time + timedelta(minutes=32),
            mgrs="35VLG8475771890",
            what="Mortar section establishing firing point",
            amount=3,
            confidence=70,
            sensor_id=None,
            unit="Charlie Recon",
            observer_signature="Eagle-2",
        ),
        SensorReading(
            time=base_time + timedelta(minutes=44),
            mgrs="35VLG8476171910",
            what="Logistics trucks arriving with ammunition crates",
            amount=4,
            confidence=65,
            sensor_id=None,
            unit="Delta Support",
            observer_signature="Logi-5",
        ),
        SensorReading(
            time=base_time + timedelta(minutes=52),
            mgrs="35VLG8478071955",
            what="Enemy UAV conducting ISR over friendly lines",
            amount=1,
            confidence=90,
            sensor_id=None,
            unit="Foxtrot ADA",
            observer_signature="Skywatch-2",
        ),
    ]


class ObservationRepository:
    """Simple in-memory repository backed by dummy observations."""

    def __init__(self, observations: Sequence[SensorReading] | None = None) -> None:
        self._observations: List[SensorReading] = list(observations or _build_dummy_observations())

    def list_recent(self, limit: int = 5) -> List[SensorReading]:
        """Return the latest observations, most recent first."""
        return sorted(self._observations, key=lambda o: o.time, reverse=True)[:limit]

    def search(self, keywords: Iterable[str], limit: int = 5) -> List[SensorReading]:
        """Return observations matching any of the provided keywords."""
        lowered = [kw.lower() for kw in keywords if kw]
        if not lowered:
            return self.list_recent(limit=limit)
        matches: List[SensorReading] = []
        for obs in self._observations:
            text = " ".join(filter(None, [obs.what, obs.unit or "", obs.observer_signature])).lower()
            if any(kw in text for kw in lowered):
                matches.append(obs)
        matches.sort(key=lambda o: o.time, reverse=True)
        return matches[:limit]
