# Multi-User Setup Guide

This script supports multiple Spotify users creating playlists simultaneously.

## Option B: GitHub Secrets Per User (Recommended)

Each user's credentials are stored as separate GitHub repository secrets.

### Setup Instructions

1. **Get Spotify Credentials for Each User**
   - Each user needs their own:
     - `SPOTIFY_CLIENT_ID`
     - `SPOTIFY_CLIENT_SECRET`
     - `SPOTIFY_REFRESH_TOKEN`
   - [See Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

2. **Add Secrets to GitHub Repository**
   - Go to: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - For each user, add three secrets:

     **For user "henry":**
     - Name: `SPOTIFY_USER_HENRY_CLIENT_ID`
     - Value: `(henry's client ID)`
     - Name: `SPOTIFY_USER_HENRY_CLIENT_SECRET`
     - Value: `(henry's client secret)`
     - Name: `SPOTIFY_USER_HENRY_REFRESH_TOKEN`
     - Value: `(henry's refresh token)`

     **For additional users** (repeat this pattern):
     - Name: `SPOTIFY_USER_{USERNAME_UPPERCASE}_CLIENT_ID`
     - Name: `SPOTIFY_USER_{USERNAME_UPPERCASE}_CLIENT_SECRET`
     - Name: `SPOTIFY_USER_{USERNAME_UPPERCASE}_REFRESH_TOKEN`

3. **Add OpenAI Key**
   - Name: `OPENAI_API_KEY`
   - Value: `sk-...` (shared across all users)

4. **Update Workflow** (if usernames differ)
   - Edit `.github/workflows/build-weekly-spotify-playlist.yml`
   - Add/modify the `env:` section to match your usernames:
     ```yaml
     SPOTIFY_USER_HENRY_CLIENT_ID: ${{ secrets.SPOTIFY_USER_HENRY_CLIENT_ID }}
     SPOTIFY_USER_HENRY_CLIENT_SECRET: ${{ secrets.SPOTIFY_USER_HENRY_CLIENT_SECRET }}
     SPOTIFY_USER_HENRY_REFRESH_TOKEN: ${{ secrets.SPOTIFY_USER_HENRY_REFRESH_TOKEN }}
     # Add more users following the same pattern
     ```

### How It Works

- Workflow runs Monday at **3 AM UTC**
- Script discovers all `SPOTIFY_USER_*` environment variables
- For each unique username found, creates a weekly playlist
- Playlist name: "Weekly Discovery — {YYYY-WW}"
- Each user gets their own independent playlists

### Example Output

```
Found 1 user(s): henry

============================================================
Creating playlist for: henry
============================================================
Authenticating with Spotify…
Fetching listening data…
Building discovery track mix…
Generating playlist description with AI…
Generating playlist artwork with AI…
✓ Playlist created: Weekly Discovery — 2026-08
✓ All checks passed! Ready to deploy.
```

### Troubleshooting

**Missing users or credentials warning:**

- Check that all three secrets are present for each user
- Secret names must match pattern: `SPOTIFY_USER_{USERNAME}_*`
- Username is extracted from the secret name (uppercase part after `SPOTIFY_USER_`)

**Workflow not running:**

- Verify `OPENAI_API_KEY` secret exists
- Check workflow is enabled: Settings → Actions → General

**No playlists created:**

- Check GitHub Actions logs for error details
- Ensure Spotify refresh tokens are still valid
