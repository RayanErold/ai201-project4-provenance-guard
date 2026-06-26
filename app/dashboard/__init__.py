"""Analytics aggregation for the /dashboard endpoint."""
from collections import Counter
from typing import Any


def build_metrics(audit_store) -> dict[str, Any]:
    """Aggregate content-status records into real-time analytics metrics."""
    content = audit_store.all_content()
    total = len(content)

    attribution_counts = Counter(c.get("attribution") for c in content)
    status_counts = Counter(c.get("status") for c in content)

    under_review = status_counts.get("under_review", 0)
    appeal_rate = round(under_review / total, 4) if total else 0.0

    confidences = [c["confidence"] for c in content if c.get("confidence") is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

    return {
        "total_submissions": total,
        "attribution_breakdown": dict(attribution_counts),
        "status_breakdown": dict(status_counts),
        "appeal_rate": appeal_rate,
        "average_confidence": avg_confidence,
    }
