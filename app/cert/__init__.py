"""Provenance certificates: "Verified Human" badge management."""
from typing import Any


def issue_certificate(audit_store, creator_id: str) -> dict[str, Any]:
    """Mark a creator as a verified human and return the certificate."""
    audit_store.set_certificate(creator_id, verified=True)
    return {"creator_id": creator_id, "verified_human": True}


def check_certificate(audit_store, creator_id: str | None) -> dict[str, Any]:
    """Return the verification badge for a creator, if any."""
    verified = bool(creator_id) and audit_store.is_verified_human(creator_id)
    return {
        "creator_id": creator_id,
        "verified_human": verified,
        "badge": "✔ Verified Human" if verified else None,
    }
