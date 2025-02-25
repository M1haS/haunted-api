"""
Paranormal Event Classification Engine

Classifies events based on scored axes:
  - kinetic   → poltergeist activity
  - visual    → apparitions / residual
  - thermal   → energy anomalies
  - electronic → intelligent entity / electrical interference
"""

from app.models.models import EventClass, ThreatLevel
from app.schemas.schemas import ClassificationResult

AXIS_LABELS = {
    "kinetic": "Kinetic activity",
    "visual": "Visual manifestation",
    "thermal": "Thermal anomaly",
    "electronic": "Electronic interference",
}

THRESHOLDS = {
    EventClass.POLTERGEIST:  {"kinetic": 0.6},
    EventClass.APPARITION:   {"visual": 0.6},
    EventClass.INFRASOUND:   {"thermal": 0.5, "kinetic": 0.3},
    EventClass.ELECTRICAL:   {"electronic": 0.6},
    EventClass.INTELLIGENT:  {"electronic": 0.5, "visual": 0.4},
    EventClass.RESIDUAL:     {"visual": 0.4, "kinetic": 0.2},
}


def _threat_from_score(score: float) -> ThreatLevel:
    if score < 0.2:
        return ThreatLevel.BENIGN
    elif score < 0.4:
        return ThreatLevel.LOW
    elif score < 0.6:
        return ThreatLevel.MODERATE
    elif score < 0.8:
        return ThreatLevel.HIGH
    return ThreatLevel.EXTREME


def classify_event(
    event_id: int,
    kinetic: float,
    visual: float,
    thermal: float,
    electronic: float,
) -> ClassificationResult:
    axes = {
        "kinetic": kinetic,
        "visual": visual,
        "thermal": thermal,
        "electronic": electronic,
    }

    overall = sum(axes.values()) / 4
    dominant_axis = max(axes, key=axes.get)

    best_class = EventClass.UNKNOWN
    best_confidence = 0.0

    for cls, requirements in THRESHOLDS.items():
        met = all(axes.get(ax, 0) >= threshold for ax, threshold in requirements.items())
        if met:
            confidence = sum(axes[ax] for ax in requirements) / len(requirements)
            if confidence > best_confidence:
                best_confidence = confidence
                best_class = cls

    if best_class == EventClass.UNKNOWN:
        best_confidence = max(overall, 0.05)

    threat = _threat_from_score(overall)

    reasoning_parts = [
        f"{AXIS_LABELS[ax]}: {score:.2f}" for ax, score in axes.items() if score > 0
    ]
    reasoning = (
        f"Dominant axis: {AXIS_LABELS[dominant_axis]}. "
        f"Scores — {', '.join(reasoning_parts)}. "
        f"Overall intensity: {overall:.2f}."
    )

    return ClassificationResult(
        event_id=event_id,
        classification=best_class,
        confidence=round(best_confidence, 3),
        threat_level=threat,
        dominant_axis=dominant_axis,
        reasoning=reasoning,
    )
