"""API endpoints for Provenance Guard.

    POST /submit     -> classify content
    POST /appeal     -> open an appeal / mark under_review
    GET  /log        -> recent audit entries
    GET  /dashboard  -> analytics metrics
    POST /certify    -> issue a "Verified Human" certificate (stretch feature)
    GET  /health     -> liveness probe
"""
import os
import tempfile
import uuid
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app import limiter
from app.cert import check_certificate, issue_certificate
from app.dashboard import build_metrics
from app.normalization import normalize
from app.scoring import classify
from app.signals import run_signals

bp = Blueprint("routes", __name__)


def _save_upload(uploaded) -> str:
    """Persist a multipart upload to a temp directory and return its path."""
    upload_dir = os.path.join(tempfile.gettempdir(), "provenance_guard_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = secure_filename(uploaded.filename) or "upload"
    path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{safe_name}")
    uploaded.save(path)
    return path


def require_api_key(fn):
    """Reject requests lacking a valid X-API-Key header."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if key != current_app.config["API_KEY"]:
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)

    return wrapper


@bp.get("/")
def index():
    """Serve the single-page UI."""
    return send_from_directory(current_app.static_folder, "index.html")


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/submit")
@require_api_key
@limiter.limit("10 per minute")
def submit():
    """Classify submitted content and persist the decision.

    Accepts either JSON (``text`` / ``file`` path) or a multipart/form-data
    upload with an actual ``file`` field (for images/video from the browser).
    """
    uploaded = request.files.get("file")
    if uploaded and uploaded.filename:
        # Multipart upload from the browser: persist to a temp path, then parse.
        form = request.form
        text = form.get("text") or None
        creator_id = form.get("creator_id", "anonymous")
        extra_metadata = {}
        file_path = _save_upload(uploaded)
    else:
        data = request.get_json(silent=True) or {}
        text = data.get("text")
        creator_id = data.get("creator_id", "anonymous")
        file_path = data.get("file")
        extra_metadata = data.get("metadata") or {}

    if not text and not file_path:
        return jsonify({"error": "must provide 'text' or 'file'"}), 400

    normalized = normalize(text=text, file_path=file_path)
    metadata = {**normalized.get("metadata", {}), **extra_metadata}

    signals = run_signals(normalized["text"], metadata)
    result = classify(signals)

    content_id = str(uuid.uuid4())
    audit = current_app.audit
    audit.upsert_content(
        content_id=content_id,
        creator_id=creator_id,
        attribution=result["attribution"],
        confidence=result["confidence"],
        label=result["label"],
        status="classified",
    )
    audit.log_event(
        content_id,
        "submission",
        {
            "creator_id": creator_id,
            "source": normalized["source"],
            **result,
        },
    )

    badge = check_certificate(audit, creator_id)
    return jsonify(
        {
            "content_id": content_id,
            "attribution": result["attribution"],
            "confidence": result["confidence"],
            "label": result["label"],
            "signals": result["signals"],
            "source": normalized["source"],
            "certificate": badge,
        }
    )


@bp.post("/appeal")
@require_api_key
@limiter.limit("10 per minute")
def appeal():
    """Open an appeal: set the content to under_review and log the reasoning."""
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    reasoning = data.get("reasoning", "")

    if not content_id:
        return jsonify({"error": "must provide 'content_id'"}), 400

    audit = current_app.audit
    if not audit.get_content(content_id):
        return jsonify({"error": "content_id not found"}), 404

    audit.update_status(content_id, "under_review")
    audit.log_event(content_id, "appeal", {"reasoning": reasoning, "status": "under_review"})

    return jsonify({"content_id": content_id, "status": "under_review", "reasoning": reasoning})


@bp.get("/log")
@require_api_key
def log():
    limit = request.args.get("limit", default=50, type=int)
    return jsonify({"entries": current_app.audit.recent_events(limit)})


@bp.get("/dashboard")
@require_api_key
def dashboard():
    return jsonify(build_metrics(current_app.audit))


@bp.post("/certify")
@require_api_key
def certify():
    """Issue a 'Verified Human' certificate for a creator (stretch feature)."""
    data = request.get_json(silent=True) or {}
    creator_id = data.get("creator_id")
    if not creator_id:
        return jsonify({"error": "must provide 'creator_id'"}), 400
    return jsonify(issue_certificate(current_app.audit, creator_id))


@bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "rate limit exceeded", "detail": str(e.description)}), 429
