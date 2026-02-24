"""AI-powered playlist artwork generation."""

from __future__ import annotations

import base64
import binascii
import io
import os
import sys
import urllib.request
from typing import Any

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from model_provider import AIProvider
from config import (
    DEFAULT_ARTWORK_PROMPT_FILE,
    OPENAI_IMAGE_MODEL,
    OPENAI_IMAGE_QUALITY,
    OPENAI_IMAGE_SIZE,
    SPOTIFY_PLAYLIST_IMAGE_MAX_BYTES,
    read_file_if_exists,
)


def _default_artwork_prompt_template() -> str:
    """Fallback prompt for playlist artwork generation."""
    return (
        "Create square album-cover-style artwork for a weekly Spotify playlist.\n"
        "Target week: {target_week}\n"
        "Source week: {source_week}\n"
        "Top artists: {top_artists}\n"
        "Top tracks: {top_tracks}\n"
        "Style notes: modern, moody, musical, abstract, no text, no logos, "
        "no faces.\n"
        "Output should be suitable as a playlist cover image."
    )


def _build_artwork_prompt(
    top_tracks: list[dict[str, Any]],
    top_artists: list[dict[str, Any]],
    *,
    source_week: str,
    target_week: str,
) -> str:
    """Build the user prompt for image generation."""
    prompt_file = os.getenv("PLAYLIST_ARTWORK_PROMPT_FILE", DEFAULT_ARTWORK_PROMPT_FILE)
    template = read_file_if_exists(prompt_file) or _default_artwork_prompt_template()

    # If template has placeholders, format them; otherwise use as-is
    if "{" in template and "}" in template:
        artist_names = ", ".join(
            dict.fromkeys(
                [a.get("name", "") for a in top_artists if a.get("name")]
                + [
                    artist.get("name", "")
                    for track in top_tracks
                    for artist in track.get("artists", [])
                    if artist.get("name")
                ]
            )
        )
        track_names = ", ".join(
            track.get("name", "") for track in top_tracks[:12] if track.get("name")
        )

        return template.format(
            source_week=source_week,
            target_week=target_week,
            top_artists=artist_names or "Unknown",
            top_tracks=track_names or "Unknown",
        )
    
    return template


def _extract_base64_image(response: dict[str, Any]) -> str | None:
    """Extract base64 image data from an OpenAI-compatible image response."""
    data = response.get("data")
    if not isinstance(data, list) or not data:
        return None

    first = data[0]
    if not isinstance(first, dict):
        return None

    b64_json = first.get("b64_json")
    if isinstance(b64_json, str) and b64_json.strip():
        return b64_json.strip()

    image_url = first.get("url")
    if isinstance(image_url, str) and image_url.strip():
        try:
            with urllib.request.urlopen(image_url) as resp:
                raw = resp.read()
            return base64.b64encode(raw).decode("ascii")
        except Exception as exc:
            print(f"  Artwork fetch failed: {exc}", file=sys.stderr, flush=True)
            return None

    return None


def _compress_image_if_needed(
    image_bytes: bytes,
    max_bytes: int = SPOTIFY_PLAYLIST_IMAGE_MAX_BYTES,
    target_quality: int = 75,
) -> bytes:
    """Compress JPEG image to fit within Spotify's size limit if needed."""
    if len(image_bytes) <= max_bytes:
        return image_bytes

    if not PIL_AVAILABLE:
        print(
            f"  Image too large ({len(image_bytes)} bytes) and PIL not available. "
            f"Install Pillow to compress: pip install Pillow",
            file=sys.stderr,
            flush=True,
        )
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "LA"):
            # Convert RGBA to RGB for JPEG
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else img.split()[1])
            img = rgb_img

        # Try progressive quality reduction
        quality = target_quality
        while quality >= 30:
            compressed_io = io.BytesIO()
            img.save(compressed_io, format="JPEG", quality=quality, optimize=True)
            compressed_bytes = compressed_io.getvalue()

            if len(compressed_bytes) <= max_bytes:
                print(
                    f"  Compressed artwork: {len(image_bytes)} → "
                    f"{len(compressed_bytes)} bytes (quality: {quality})",
                    file=sys.stderr,
                    flush=True,
                )
                return compressed_bytes

            quality -= 5

        print(
            f"  Image compression failed: could not get below {max_bytes} bytes. "
            f"Using original.",
            file=sys.stderr,
            flush=True,
        )
        return image_bytes
    except Exception as err:
        print(
            f"  Image compression error: {err}. Using original.",
            file=sys.stderr,
            flush=True,
        )
        return image_bytes


def generate_playlist_artwork_base64(
    provider: AIProvider,
    top_tracks: list[dict[str, Any]],
    top_artists: list[dict[str, Any]],
    *,
    source_week: str,
    target_week: str,
) -> str | None:
    """Generate playlist artwork and return base64-encoded JPEG bytes.

    Returns None on failure or if image validation fails.
    """
    prompt = _build_artwork_prompt(
        top_tracks,
        top_artists,
        source_week=source_week,
        target_week=target_week,
    )

    print(f"  Artwork AI: calling {OPENAI_IMAGE_MODEL}…", flush=True)

    try:
        response = provider.generate_image(
            prompt,
            model=OPENAI_IMAGE_MODEL,
            size=OPENAI_IMAGE_SIZE,
            quality=OPENAI_IMAGE_QUALITY,
        )
    except Exception as exc:
        print(f"  Artwork AI failed: {exc}", file=sys.stderr, flush=True)
        return None

    image_b64 = _extract_base64_image(response)
    if not image_b64:
        print("  Artwork AI returned no image payload.", file=sys.stderr, flush=True)
        return None

    try:
        image_bytes = base64.b64decode(image_b64, validate=True)
    except (binascii.Error, ValueError):
        print("  Artwork payload was not valid base64.", file=sys.stderr, flush=True)
        return None

    # Compress if needed to fit Spotify's limit
    image_bytes = _compress_image_if_needed(image_bytes)

    if len(image_bytes) > SPOTIFY_PLAYLIST_IMAGE_MAX_BYTES:
        print(
            "  Artwork still too large after compression "
            f"({len(image_bytes)} bytes > {SPOTIFY_PLAYLIST_IMAGE_MAX_BYTES}). "
            "Skipping upload.",
            file=sys.stderr,
            flush=True,
        )
        return None

    return base64.b64encode(image_bytes).decode("ascii")
