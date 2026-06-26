"""Normalization layer: converts non-text media into analysable text."""
from app.normalization.image_parser import parse_image
from app.normalization.video_parser import parse_video

__all__ = ["parse_image", "parse_video", "normalize"]


def normalize(text: str | None = None, file_path: str | None = None) -> dict:
    """Normalize any submission into a text transcript plus extracted metadata.

    Returns ``{"text": str, "metadata": dict, "source": str}``.
    """
    if file_path:
        lowered = file_path.lower()
        if lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
            return parse_image(file_path)
        if lowered.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            return parse_video(file_path)
    return {"text": text or "", "metadata": {}, "source": "text"}
