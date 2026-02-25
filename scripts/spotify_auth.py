"""Spotify OAuth token management."""

from __future__ import annotations

import base64
import sys

from config import SPOTIFY_ACCOUNTS_BASE
from http_client import http_json

REQUIRED_SCOPES = {
    "user-top-read",
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
    "ugc-image-upload",
}


def spotify_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> tuple[str, set[str]]:
    """Exchange a refresh token for an access token.

    Returns (access_token, granted_scopes).
    """
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = http_json(
        "POST",
        f"{SPOTIFY_ACCOUNTS_BASE}/api/token",
        headers={"Authorization": f"Basic {basic}"},
        form={"grant_type": "refresh_token", "refresh_token": refresh_token},
    )

    granted = set(response.get("scope", "").split())
    print(f"Granted scopes: {granted}", flush=True)
    missing = REQUIRED_SCOPES - granted
    if missing:
        print(
            f"ERROR: Token is missing required scope(s): {', '.join(sorted(missing))}\n"
            f"Re-authorise with scopes: {' '.join(sorted(REQUIRED_SCOPES))}\n"
            f"  https://accounts.spotify.com/authorize?response_type=code"
            f"&client_id={client_id}"
            f"&scope={'%20'.join(sorted(REQUIRED_SCOPES))}"
            f"&redirect_uri=http%3A%2F%2F127.0.0.1%3A8888%2Fcallback",
            file=sys.stderr,
        )
        sys.exit(1)

    return response["access_token"], granted
