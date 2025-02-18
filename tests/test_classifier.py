import pytest
from app.services.classifier import classify_event
from app.models.models import EventClass, ThreatLevel


def test_poltergeist_classification():
    result = classify_event(1, kinetic=0.8, visual=0.1, thermal=0.1, electronic=0.1)
    assert result.classification == EventClass.POLTERGEIST
    assert result.dominant_axis == "kinetic"


def test_apparition_classification():
    result = classify_event(2, kinetic=0.1, visual=0.9, thermal=0.1, electronic=0.1)
    assert result.classification == EventClass.APPARITION


def test_electrical_classification():
    result = classify_event(3, kinetic=0.1, visual=0.1, thermal=0.1, electronic=0.8)
    assert result.classification == EventClass.ELECTRICAL


def test_unknown_low_scores():
    result = classify_event(4, kinetic=0.1, visual=0.1, thermal=0.1, electronic=0.1)
    assert result.classification == EventClass.UNKNOWN
    assert result.threat_level == ThreatLevel.BENIGN


def test_extreme_threat():
    result = classify_event(5, kinetic=0.95, visual=0.9, thermal=0.9, electronic=0.9)
    assert result.threat_level == ThreatLevel.EXTREME


def test_confidence_range():
    result = classify_event(6, kinetic=0.7, visual=0.3, thermal=0.2, electronic=0.1)
    assert 0.0 <= result.confidence <= 1.0


def test_reasoning_not_empty():
    result = classify_event(7, kinetic=0.5, visual=0.5, thermal=0.0, electronic=0.0)
    assert len(result.reasoning) > 10
