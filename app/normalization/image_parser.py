"""Image normalization.

Converts an image into analysable text using a Vision-Language Model (VLM).
The VLM produces (a) a rich descriptive caption that the LLM/stylometric signals
can analyse, and (b) a note on any visual artifacts typical of AI generation.
EXIF metadata is also extracted to feed the metadata signal.

If no VLM backend is configured (no API key / library / network), the parser
fails safe to a placeholder transcript so the rest of the pipeline still runs.
"""
import base64
import mimetypes
import os
from typing import Any

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:  # pragma: no cover
    Image = None
    TAGS = {}

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


VISION_PROMPT = (
    "Describe this image in detail for an AI-content provenance system. "
    "Write 3-5 sentences covering subject, composition, lighting and texture. "
    "Then add one final sentence noting any artifacts that suggest AI generation "
    "(e.g. malformed hands, nonsensical text, impossible geometry, over-smooth "
    "skin, watermark-like patterns). Respond in plain prose."
)


def _extract_exif(path: str) -> dict[str, Any]:
    if Image is None:
        return {}
    try:
        with Image.open(path) as img:
            raw = img.getexif()
            return {TAGS.get(tag_id, tag_id): str(val) for tag_id, val in raw.items()}
    except Exception:
        return {}


def _encode_data_url(path: str) -> str | None:
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    try:
        with open(path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def _vlm_caption(path: str) -> str | None:
    """Caption the image via Groq vision. Returns None if unavailable/failed."""
    api_key = os.getenv("GROQ_API_KEY")
    if Groq is None or not api_key or api_key == "your_groq_api_key_here":
        return None

    data_url = _encode_data_url(path)
    if not data_url:
        return None

    model = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    client = Groq(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def parse_image(file_path: str) -> dict[str, Any]:
    """Return a normalized representation of an image submission."""
    metadata = _extract_exif(file_path)
    name = os.path.basename(file_path)

    caption = _vlm_caption(file_path)
    if caption:
        transcript = f"[image transcript of '{name}'] {caption}"
        metadata["vlm_captioned"] = True
    else:
        transcript = (
            f"[image transcript] Visual content extracted from '{name}'. "
            "No VLM backend available; metadata-based signals still apply."
        )
        metadata["vlm_captioned"] = False

    return {"text": transcript, "metadata": metadata, "source": "image"}
