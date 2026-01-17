from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FairProbability:
    outcome: str
    implied: float
    fair: float
    captured_at: datetime
    confidence: float


def devig(implied_probs: Iterable[float]) -> list[float]:
    total = sum(implied_probs)
    if total == 0:
        return [0 for _ in implied_probs]
    return [prob / total for prob in implied_probs]


def confidence_from_edge(edge: float, time_to_event_hours: float) -> float:
    decay = max(0.1, min(1.0, time_to_event_hours / 72))
    return max(0.0, min(1.0, abs(edge) * decay))


def build_fair_probabilities(
    implied: dict[str, float],
    time_to_event_hours: float,
    captured_at: datetime,
) -> list[FairProbability]:
    fair_probs = devig(implied.values())
    items = list(implied.items())
    results: list[FairProbability] = []
    for (outcome, implied_prob), fair_prob in zip(items, fair_probs, strict=True):
        edge = fair_prob - implied_prob
        results.append(
            FairProbability(
                outcome=outcome,
                implied=implied_prob,
                fair=fair_prob,
                captured_at=captured_at,
                confidence=confidence_from_edge(edge, time_to_event_hours),
            )
        )
    return results
