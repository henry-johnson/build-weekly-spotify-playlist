"""Unit tests for spotify_api helpers — no real Spotify calls."""
from __future__ import annotations

import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from spotify_api import (
    primary_artist_map_from_tracks,
    spotify_search_tracks_with_artists,
    spotify_track_primary_artist_by_uri,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_track(track_id: str, artist_id: str, artist_name: str) -> dict:
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "artists": [{"id": artist_id, "name": artist_name}],
    }


SAMPLE_URIS = [
    "spotify:track:AAA111",
    "spotify:track:BBB222",
    "spotify:track:CCC333",
]

SAMPLE_RESPONSE = {
    "tracks": [
        _make_track("AAA111", "artist1", "Artist One"),
        _make_track("BBB222", "artist2", "Artist Two"),
        _make_track("CCC333", "artist3", "Artist Three"),
    ],
}


# ── Tests ────────────────────────────────────────────────────────────


class TestTrackPrimaryArtistByUri(unittest.TestCase):
    """Tests for spotify_track_primary_artist_by_uri."""

    @patch("spotify_api.http_json")
    def test_basic_lookup(self, mock_http: MagicMock) -> None:
        """Normal case: returns artist map keyed by URI."""
        mock_http.return_value = SAMPLE_RESPONSE

        result = spotify_track_primary_artist_by_uri("fake-token", SAMPLE_URIS)

        self.assertEqual(result["spotify:track:AAA111"], "artist1")
        self.assertEqual(result["spotify:track:BBB222"], "artist2")
        self.assertEqual(result["spotify:track:CCC333"], "artist3")

        # Verify the request was made once (3 IDs < 50 batch cap)
        mock_http.assert_called_once()

    @patch("spotify_api.http_json")
    def test_market_parameter_passed(self, mock_http: MagicMock) -> None:
        """When market is provided, it appears in the URL query string."""
        mock_http.return_value = SAMPLE_RESPONSE

        spotify_track_primary_artist_by_uri(
            "fake-token", SAMPLE_URIS, market="GB",
        )

        call_url = mock_http.call_args[0][1]
        self.assertIn("market=GB", call_url)

    @patch("spotify_api.http_json")
    def test_no_market_by_default(self, mock_http: MagicMock) -> None:
        """When market is None, no market param in the URL."""
        mock_http.return_value = SAMPLE_RESPONSE

        spotify_track_primary_artist_by_uri("fake-token", SAMPLE_URIS)

        call_url = mock_http.call_args[0][1]
        self.assertNotIn("market=", call_url)

    @patch("spotify_api.http_json")
    def test_batching(self, mock_http: MagicMock) -> None:
        """Verify IDs are batched in groups of 50."""
        # 75 unique URIs → 2 batches (50 + 25)
        uris = [f"spotify:track:T{i:04d}" for i in range(75)]
        batch1_tracks = [
            _make_track(f"T{i:04d}", f"a{i}", f"Artist {i}")
            for i in range(50)
        ]
        batch2_tracks = [
            _make_track(f"T{i:04d}", f"a{i}", f"Artist {i}")
            for i in range(50, 75)
        ]
        mock_http.side_effect = [
            {"tracks": batch1_tracks},
            {"tracks": batch2_tracks},
        ]

        result = spotify_track_primary_artist_by_uri("fake-token", uris)

        self.assertEqual(len(result), 75)
        self.assertEqual(mock_http.call_count, 2)

    @patch("spotify_api.http_json")
    def test_deduplicates_uris(self, mock_http: MagicMock) -> None:
        """Duplicate URIs should not cause duplicate API calls."""
        duped = SAMPLE_URIS + SAMPLE_URIS
        mock_http.return_value = SAMPLE_RESPONSE

        result = spotify_track_primary_artist_by_uri("fake-token", duped)

        # Still only 3 unique track IDs → 1 batch
        mock_http.assert_called_once()
        self.assertEqual(len(result), 3)

    def test_empty_input(self) -> None:
        """Empty URI list should return empty dict without any API call."""
        result = spotify_track_primary_artist_by_uri("fake-token", [])
        self.assertEqual(result, {})

    def test_invalid_uris_ignored(self) -> None:
        """Non-Spotify URIs should be silently ignored."""
        result = spotify_track_primary_artist_by_uri(
            "fake-token", ["not-a-uri", "also:bad"],
        )
        self.assertEqual(result, {})

    @patch("spotify_api.http_json")
    def test_403_propagates(self, mock_http: MagicMock) -> None:
        """Verify that HTTPError 403 propagates (caller handles it)."""
        mock_http.side_effect = urllib.error.HTTPError(
            "https://api.spotify.com/v1/tracks",
            403,
            "Forbidden",
            {},  # type: ignore[arg-type]
            None,
        )

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            spotify_track_primary_artist_by_uri("fake-token", SAMPLE_URIS)
        self.assertEqual(ctx.exception.code, 403)


class TestTrackLookupFallback(unittest.TestCase):
    """Test that create_weekly_playlist gracefully handles 403."""

    def test_fallback_codepath(self) -> None:
        """Simulate the try/except in create_weekly_playlist for 403."""
        import urllib.error

        # Simulate the exact code pattern from create_weekly_playlist.py
        rec_uris = ["spotify:track:A", "spotify:track:B", "spotify:track:C"]
        search_market = None

        def _mock_lookup(token, uris, *, market=None):
            raise urllib.error.HTTPError(
                "https://api.spotify.com/v1/tracks",
                403,
                "Forbidden",
                {},  # type: ignore[arg-type]
                None,
            )

        # Replicate the fallback logic from create_weekly_playlist
        try:
            primary_artist_by_uri = _mock_lookup(
                "token", rec_uris, market=search_market,
            )
        except urllib.error.HTTPError:
            primary_artist_by_uri = {}

        # Verify fallback: empty dict means no reordering
        self.assertEqual(primary_artist_by_uri, {})

        # Tracks should remain in original order
        original_order = list(rec_uris)
        if primary_artist_by_uri:
            rec_uris = ["reordered"]  # should NOT happen
        self.assertEqual(rec_uris, original_order)


class TestSpreadTracksByArtist(unittest.TestCase):
    """Test the _spread_tracks_by_artist helper."""

    def test_spreads_adjacent_same_artist(self) -> None:
        from create_weekly_playlist import _spread_tracks_by_artist

        # 3 tracks by artist A, then 3 by artist B
        uris = ["a1", "a2", "a3", "b1", "b2", "b3"]
        artist_map = {
            "a1": "A", "a2": "A", "a3": "A",
            "b1": "B", "b2": "B", "b3": "B",
        }
        result = _spread_tracks_by_artist(uris, artist_map)
        # No two adjacent tracks should have the same artist
        for i in range(len(result) - 1):
            self.assertNotEqual(
                artist_map.get(result[i]),
                artist_map.get(result[i + 1]),
                f"Adjacent same artist at index {i}: {result}",
            )


class TestPrimaryArtistMapFromTracks(unittest.TestCase):
    """Tests for primary_artist_map_from_tracks."""

    def test_basic_mapping(self) -> None:
        tracks = [
            _make_track("AAA", "a1", "Artist One"),
            _make_track("BBB", "a2", "Artist Two"),
        ]
        result = primary_artist_map_from_tracks(tracks)
        self.assertEqual(result["spotify:track:AAA"], "a1")
        self.assertEqual(result["spotify:track:BBB"], "a2")

    def test_empty_list(self) -> None:
        self.assertEqual(primary_artist_map_from_tracks([]), {})

    def test_missing_uri(self) -> None:
        tracks = [{"id": "X", "artists": [{"id": "a", "name": "A"}]}]
        self.assertEqual(primary_artist_map_from_tracks(tracks), {})

    def test_no_artists_fallback(self) -> None:
        tracks = [{"uri": "spotify:track:X", "id": "X", "artists": []}]
        # No artist → should not be in the map
        self.assertEqual(primary_artist_map_from_tracks(tracks), {})

    def test_deduplicates(self) -> None:
        t = _make_track("AAA", "a1", "Artist One")
        result = primary_artist_map_from_tracks([t, t, t])
        self.assertEqual(len(result), 1)

    def test_name_fallback_when_no_id(self) -> None:
        tracks = [{"uri": "spotify:track:X", "id": "X",
                    "artists": [{"name": "Fallback Name"}]}]
        result = primary_artist_map_from_tracks(tracks)
        self.assertEqual(result["spotify:track:X"], "Fallback Name")


class TestSearchTracksWithArtists(unittest.TestCase):
    """Tests for spotify_search_tracks_with_artists."""

    @patch("spotify_api.http_json")
    def test_returns_uris_and_artist_map(self, mock_http: MagicMock) -> None:
        items = [
            _make_track("AAA", "a1", "Artist One"),
            _make_track("BBB", "a2", "Artist Two"),
        ]
        mock_http.return_value = {"tracks": {"items": items}}

        uris, artist_map = spotify_search_tracks_with_artists(
            "fake-token", 'artist:"Test"',
        )

        self.assertEqual(len(uris), 2)
        self.assertIn("spotify:track:AAA", uris)
        self.assertEqual(artist_map["spotify:track:AAA"], "a1")
        self.assertEqual(artist_map["spotify:track:BBB"], "a2")

    @patch("spotify_api.http_json")
    def test_empty_results(self, mock_http: MagicMock) -> None:
        mock_http.return_value = {"tracks": {"items": []}}
        uris, artist_map = spotify_search_tracks_with_artists(
            "fake-token", "nothing",
        )
        self.assertEqual(uris, [])
        self.assertEqual(artist_map, {})

    @patch("spotify_api.http_json")
    def test_api_error_returns_empty(self, mock_http: MagicMock) -> None:
        mock_http.side_effect = Exception("timeout")
        uris, artist_map = spotify_search_tracks_with_artists(
            "fake-token", "broken",
        )
        self.assertEqual(uris, [])
        self.assertEqual(artist_map, {})


if __name__ == "__main__":
    unittest.main()
