"""Track discovery engine combining AI recommendations, anchors, and search."""

from __future__ import annotations

import random
import sys
from typing import Any

from model_provider import AIProvider
from recommendations import ai_recommend_search_queries
from spotify_api import spotify_search_tracks


def build_discovery_mix(
    spotify_token: str,
    provider: AIProvider,
    source_tracks: list[dict[str, Any]],
    source_artists: list[dict[str, Any]],
    current_top_artists: list[dict[str, Any]],
    *,
    source_week: str,
    target_week: str,
    market: str | None = None,
    temperature: float = 1.0,
) -> list[str]:
    """Build a ~100-track discovery mix.

    Slot 1 — AI-recommended tracks (target 50):
        Ask a GPT model to suggest Spotify search queries based on
        listening data, then execute those queries against Spotify search.
        Gracefully degrades if rate limited.

    Slot 2 — Familiar anchors (up to 15):
        Shuffled source week tracks the listener already knows.

    Slot 3 — Genre/artist search fallback (fill to 100):
        Traditional genre and artist name searches to fill remaining slots.
        Falls back to empty if rate limited.
    """
    known_uris: set[str] = {t["uri"] for t in source_tracks if t.get("uri")}
    discovered: list[str] = []
    discovered_set: set[str] = set()

    def add(uri: str, cap: int) -> bool:
        if (
            uri not in known_uris
            and uri not in discovered_set
            and len(discovered) < cap
        ):
            discovered.append(uri)
            discovered_set.add(uri)
            return True
        return False

    # ── Slot 1: AI-powered recommendations ──────────────────────────
    print("  Slot 1: AI-powered recommendations…", flush=True)
    ai_count = len(discovered)
    try:
        ai_queries = ai_recommend_search_queries(
            provider,
            source_tracks,
            current_top_artists,
            source_week=source_week,
            target_week=target_week,
            temperature=temperature,
            max_queries=30,
        )
        for query in ai_queries:
            if len(discovered) >= 50:
                break
            try:
                for uri in spotify_search_tracks(
                    spotify_token, query, limit=10, market=market,
                ):
                    add(uri, 50)
            except Exception as err:
                print(
                    f"  ⚠ Search failed for query (rate limit?): {err}",
                    file=sys.stderr,
                    flush=True,
                )
                continue
        ai_count = len(discovered)
    except Exception as err:
        print(
            f"  ⚠ AI recommendations failed (rate limit?): {err}",
            file=sys.stderr,
            flush=True,
        )
        ai_count = len(discovered)

    # ── Slot 2: Familiar anchors ────────────────────────────────────
    print("  Slot 2: Familiar anchors…", flush=True)
    anchor_uris = list(dict.fromkeys(
        t["uri"] for t in source_tracks if t.get("uri")
    ))
    random.shuffle(anchor_uris)
    for uri in anchor_uris:
        if uri not in discovered_set and len(discovered) < 65:
            discovered.append(uri)
            discovered_set.add(uri)
    anchor_count = len(discovered) - ai_count

    # ── Slot 3: Genre/artist search fallback ────────────────────────
    print("  Slot 3: Genre/artist search…", flush=True)
    try:
        genres = list(
            dict.fromkeys(
                g for a in current_top_artists for g in a.get("genres", [])
            )
        )
        artist_names = list(
            dict.fromkeys(
                [a["name"] for a in source_artists if a.get("name")]
                + [a["name"] for a in current_top_artists if a.get("name")]
            )
        )
        print(f"  Genre pool: {genres[:8]}", flush=True)
        queries = [f'genre:"{g}"' for g in genres[:8]] + [
            f'artist:"{n}"' for n in artist_names[:8]
        ]
        for query in queries:
            if len(discovered) >= 100:
                break
            try:
                for uri in spotify_search_tracks(
                    spotify_token, query, limit=10, market=market,
                ):
                    add(uri, 100)
            except Exception as err:
                print(
                    f"  ⚠ Genre/artist search failed (rate limit?): {err}",
                    file=sys.stderr,
                    flush=True,
                )
                continue
    except Exception as err:
        print(
            f"  ⚠ Genre/artist search slot failed (rate limit?): {err}",
            file=sys.stderr,
            flush=True,
        )
    search_count = len(discovered) - ai_count - anchor_count

    print(
        f"  Discovery mix: {len(discovered)} tracks "
        f"(ai={ai_count}, anchors={anchor_count}, search={search_count})",
        flush=True,
    )
    return discovered
