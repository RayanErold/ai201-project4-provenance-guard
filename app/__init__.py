"""Provenance Guard application factory.

Wires together the Flask app, rate limiter, audit store and API routes.
"""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.audit import AuditStore

load_dotenv()

# Module-level limiter so routes can reference decorators at import time.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://",
)


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Provenance Guard Flask application."""
    app = Flask(__name__)
    app.config["API_KEY"] = os.getenv("APP_API_KEY", "dev-local-key")
    app.config["DATABASE_PATH"] = os.getenv("DATABASE_PATH", "provenance_guard.db")

    if config:
        app.config.update(config)

    # Shared audit store (SQLite-backed structured logger).
    app.audit = AuditStore(app.config["DATABASE_PATH"])
    app.audit.init_db()

    limiter.init_app(app)

    from app.routes import bp as routes_bp

    app.register_blueprint(routes_bp)

    return app
