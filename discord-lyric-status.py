"""
╔══════════════════════════════════════════════════════════════╗
║        SPOTIFY LYRICS → DISCORD STATUS SYNC                 ║
║        Real-time lyric lines as your Discord status         ║
╚══════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS:
──────────────────
1. Install dependencies:
      pip install spotipy requests websocket-client python-dotenv syncedlyrics

2. Create a Spotify App at https://developer.spotify.com/dashboard
   - Redirect URI: http://localhost:8888/callback

3. Create a `.env` file in the same directory (or copy `.env.example` to `.env`):
   - Copy your Spotify Client ID and Client Secret into the `.env` file
   - Get your Discord token: Open Discord in browser → F12 → Network tab → Send message → Look for request to /api/ → Find "Authorization" header
   - Paste your Discord token into the `.env` file (keep it secret!)

4. Fetch lyrics via syncedlyrics (aggregates NetEase, Musixmatch, LRCLib, Megalobiz)

5. Run:  python discord-lyric-status.py
"""

import os
import sys
import time
import json
import threading
import subprocess

# Automatically install missing dependencies
required_packages = ["spotipy", "requests", "websocket-client", "python-dotenv", "syncedlyrics"]
missing_packages = []
for pkg in required_packages:
    try:
        import_name = "dotenv" if pkg == "python-dotenv" else pkg
        __import__(import_name)
    except ImportError:
        missing_packages.append(pkg)

if missing_packages:
    print(f"Missing required libraries detected. Installing: {', '.join(missing_packages)}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        print("Libraries installed successfully!\n")
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        print("Please run manually: pip install spotipy requests websocket-client python-dotenv syncedlyrics")
        sys.exit(1)

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import syncedlyrics

# Load .env file using python-dotenv if available, or fallback manually
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Simple manual fallback to parse .env file
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

# ─────────────────────────────────────────────
#  🔧 CONFIGURATION — Loaded from environment
# ─────────────────────────────────────────────

SPOTIPY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID", "")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "")
SPOTIPY_REDIRECT_URI  = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

DISCORD_TOKEN         = os.getenv("DISCORD_TOKEN", "")

# Optional: emoji shown before the lyric in Discord status
LYRIC_EMOJI = "🎵"

# How often to check Spotify for position (seconds)
POLL_INTERVAL = 1.0

# ─────────────────────────────────────────────
#  Spotify Setup
# ─────────────────────────────────────────────

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-read-playback-state user-read-currently-playing",
    cache_path=".spotify_cache"
))

# ─────────────────────────────────────────────
#  Lyrics fetching (syncedlyrics — aggregates multiple services)
# ─────────────────────────────────────────────

_lyrics_cache: dict = {}

def fetch_lyrics(title: str, artist: str) -> list[dict] | None:
    """
    Returns a list of timed lyric lines using syncedlyrics:
      [{"time": 12.34, "text": "Some lyric line"}, ...]
    Returns None if not found.
    """
    key = f"{title}||{artist}"
    if key in _lyrics_cache:
        return _lyrics_cache[key]

    try:
        # Search for synced lyrics using multiple providers
        synced_raw = syncedlyrics.search(f"{title} {artist}", synced_only=True)
        if not synced_raw:
            _lyrics_cache[key] = None
            return None

        lines = []
        for line in synced_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: [mm:ss.xx] lyric text or [hh:mm:ss.xx] lyric text
            if line.startswith("[") and "]" in line:
                tag, _, text = line.partition("]")
                tag = tag.lstrip("[")
                try:
                    parts = tag.split(":")
                    if len(parts) == 3:
                        h, m, s = parts
                        t = int(h) * 3600 + int(m) * 60 + float(s)
                    elif len(parts) == 2:
                        m, s = parts
                        t = int(m) * 60 + float(s)
                    else:
                        continue
                    lines.append({"time": t, "text": text.strip()})
                except ValueError:
                    pass

        _lyrics_cache[key] = lines if lines else None
        return _lyrics_cache[key]

    except Exception as e:
        print(f"[Lyrics] Error: {e}")
        _lyrics_cache[key] = None
        return None


def get_current_lyric(lyrics: list[dict], position_ms: int) -> str:
    """Return the lyric line that should be showing right now."""
    position_s = position_ms / 1000
    current = ""
    for line in lyrics:
        if line["time"] <= position_s:
            current = line["text"]
        else:
            break
    return current

# ─────────────────────────────────────────────
#  Discord Status Update
# ─────────────────────────────────────────────

DISCORD_API = "https://discord.com/api/v9"

def set_discord_status(text: str, emoji: str = LYRIC_EMOJI):
    """Update your Discord custom status via the API."""
    headers = {
        "Authorization": DISCORD_TOKEN,
        "Content-Type": "application/json",
    }

    # Truncate to Discord's 128-char limit
    if len(text) > 124:
        text = text[:121] + "..."

    payload = {
        "custom_status": {
            "text": f"{emoji} {text}" if text else "",
            "emoji_name": None,
        }
    }

    try:
        r = requests.patch(
            f"{DISCORD_API}/users/@me/settings",
            headers=headers,
            json=payload,
            timeout=5,
        )
        if r.status_code not in (200, 204):
            print(f"[Discord] Status update failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[Discord] Error: {e}")


def clear_discord_status():
    """Remove the custom status when the song stops."""
    set_discord_status("", emoji="")

# ─────────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════╗")
    print("║  Spotify Lyrics → Discord Status     ║")
    print("╚══════════════════════════════════════╝")
    print("Running... Press Ctrl+C to stop.\n")

    last_lyric      = None
    last_track_id   = None
    current_lyrics  = None

    try:
        while True:
            try:
                playback = sp.current_playback()

                # Nothing playing
                if not playback or not playback.get("is_playing"):
                    if last_lyric is not None:
                        print("[Status] Playback stopped — clearing status")
                        clear_discord_status()
                        last_lyric = None
                        last_track_id = None
                    time.sleep(POLL_INTERVAL * 2)
                    continue

                track    = playback["item"]
                track_id = track["id"]
                title    = track["name"]
                artist   = track["artists"][0]["name"]
                position = playback["progress_ms"]

                # New song — fetch fresh lyrics
                if track_id != last_track_id:
                    print(f"[Now Playing] {title} — {artist}")
                    current_lyrics = fetch_lyrics(title, artist)
                    last_track_id  = track_id
                    last_lyric     = None

                    if current_lyrics:
                        print(f"[Lyrics] Loaded {len(current_lyrics)} lines ✓")
                    else:
                        print("[Lyrics] Not found for this track")

                # Update status with current lyric
                if current_lyrics:
                    lyric = get_current_lyric(current_lyrics, position)

                    if lyric != last_lyric:
                        if lyric:
                            print(f"[Status] → {lyric}")
                            set_discord_status(lyric)
                        else:
                            clear_discord_status()
                        last_lyric = lyric

            except spotipy.exceptions.SpotifyException as e:
                print(f"[Spotify] Error: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"[Error] {e}")
                time.sleep(3)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[Stopped] Clearing Discord status...")
        clear_discord_status()
        print("Done. Bye!")


if __name__ == "__main__":
    # Quick config sanity check
    missing = []
    if not SPOTIPY_CLIENT_ID:
        missing.append("SPOTIPY_CLIENT_ID")
    if not SPOTIPY_CLIENT_SECRET:
        missing.append("SPOTIPY_CLIENT_SECRET")
    if not DISCORD_TOKEN:
        missing.append("DISCORD_TOKEN")

    if missing:
        print("⚠️  Please configure these values in your .env file:")
        for m in missing:
            print(f"   • {m}")
        exit(1)

    main()