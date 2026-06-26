"""Video normalization.

A production implementation would run ASR (e.g. Whisper) over the audio track
and sample frames through a VLM. Here we return a placeholder transcript and any
container metadata we can cheaply read, keeping the pipeline uniform.
"""
import os
from typing import Any


def parse_video(file_path: str) -> dict[str, Any]:
    """Return a normalized representation of a video submission."""
    name = os.path.basename(file_path)
    metadata = {"container": os.path.splitext(name)[1].lstrip(".").lower()}

    transcript = (
        f"[video transcript] Audio/visual content extracted from '{name}'. "
        "No ASR backend configured; structural signals still apply."
    )
    return {"text": transcript, "metadata": metadata, "source": "video"}
