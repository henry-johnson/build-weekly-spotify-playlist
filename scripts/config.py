"""Shared constants and environment helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Spotify ─────────────────────────────────────────────────────────
SPOTIFY_ACCOUNTS_BASE = "https://accounts.spotify.com"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_PLAYLIST_DESCRIPTION_MAX = 300
SPOTIFY_PLAYLIST_IMAGE_MAX_BYTES = 256 * 1024

# ── OpenAI API ──────────────────────────────────────────────────
OPENAI_API_BASE_URL = "https://api.openai.com/v1"
OPENAI_TEXT_MODEL_DESCRIPTION = "gpt-5.2"  # For playlist descriptions
OPENAI_TEXT_MODEL_RECOMMENDATIONS = "gpt-5.2"  # For music recommendations
OPENAI_IMAGE_MODEL = "chatgpt-image-latest"
OPENAI_IMAGE_SIZE = "1024"  # Size in pixels (will be formatted as 1024x1024)
OPENAI_IMAGE_QUALITY = "auto"  # "low", "medium", "high", "auto"

# Temperature settings (gpt-5.2 supports 0.0-2.0)
OPENAI_TEMPERATURE_DESCRIPTION = 1.2  # Higher = more creative/witty descriptions
OPENAI_TEMPERATURE_RECOMMENDATIONS = 0.8  # Lower = more focused search queries

# ── Prompt files ────────────────────────────────────────────────────
DEFAULT_USER_PROMPT_FILE = "prompts/playlist_description_prompt.md"
DEFAULT_RECOMMENDATIONS_PROMPT_FILE = "prompts/recommendations_prompt.md"
DEFAULT_ARTWORK_PROMPT_FILE = "prompts/playlist_artwork_prompt.md"

# ── Retry config ────────────────────────────────────────────────────
MAX_RETRIES = 10  # Increased for rate limit tolerance
RETRY_BACKOFF = 2.0  # seconds
MAX_RETRY_WAIT_SECONDS = 120.0  # Increased to handle heavy rate limiting


def require_env(name: str) -> str:
    """Return an environment variable or exit with an error."""
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def read_file_if_exists(path: str) -> str | None:
    """Read a text file if it exists, else return None."""
    file_path = Path(path)
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8")
