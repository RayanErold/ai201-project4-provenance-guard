"""Weighted confidence voting and transparency-label generation.

Final confidence S = 0.5*LLM + 0.3*Stylometric + 0.2*Metadata.

Uncertainty bands:
    0.00 - 0.40  -> Likely Human
    0.41 - 0.69  -> Uncertain (creator manual review)
    0.70 - 1.00  -> Likely AI-Generated
"""
from typing import Any

WEIGHTS = {"llm": 0.5, "stylometric": 0.3, "metadata": 0.2}

LABELS = {
    "ai": "This content shows strong indicators of being AI-generated.",
    "uncertain": "Attribution inconclusive. Contextual verification recommended.",
    "human": "This content displays human-typical stylistic variation.",
}


def weighted_confidence(signals: dict[str, float]) -> float:
    """Combine signal scores via weighted average. Returns float in [0, 1]."""
    total_weight = sum(WEIGHTS[k] for k in signals if k in WEIGHTS)
    if total_weight == 0:
        return 0.5
    score = sum(signals[k] * WEIGHTS[k] for k in signals if k in WEIGHTS)
    return round(score / total_weight, 4)


def attribution_for(confidence: float) -> str:
    """Map a confidence score to a coarse attribution category."""
    if confidence <= 0.40:
        return "likely_human"
    if confidence < 0.70:
        return "uncertain"
    return "likely_ai"


def label_generator(confidence: float) -> str:
    """Return the human-facing transparency label for a confidence score."""
    attribution = attribution_for(confidence)
    if attribution == "likely_ai":
        return LABELS["ai"]
    if attribution == "uncertain":
        return LABELS["uncertain"]
    return LABELS["human"]


def classify(signals: dict[str, float]) -> dict[str, Any]:
    """Full classification result from raw signal scores."""
    confidence = weighted_confidence(signals)
    return {
        "confidence": confidence,
        "attribution": attribution_for(confidence),
        "label": label_generator(confidence),
        "signals": signals,
    }
