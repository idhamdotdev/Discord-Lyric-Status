# Discord-Lyric-Status

<div align="center">

[![Stars](https://img.shields.io/github/stars/idhamdotdev/Discord-Lyric-Status?style=social)](https://github.com/idhamdotdev/Discord-Lyric-Status/stargazers)
[![Forks](https://img.shields.io/github/forks/idhamdotdev/Discord-Lyric-Status?style=social)](https://github.com/idhamdotdev/Discord-Lyric-Status/network/members)
[![Follow](https://img.shields.io/github/followers/idhamdotdev?label=Follow&style=social)](https://github.com/idhamdotdev)

**Real-time Spotify Lyrics to Discord Custom Status synchronizer.**

</div>

---

`Discord-Lyric-Status` automatically syncs whatever song lyrics you're currently listening to on Spotify straight to your Discord custom status in real-time. It uses multiple lyrics providers to ensure synced lyrics are fetched for almost any track.

## Features

- **Real-Time Sync**: Updates your Discord custom status line-by-line as the song plays.
- **Multi-Provider Search**: Uses `syncedlyrics` under the hood to search across NetEase, Musixmatch, LRCLib, and Megalobiz for maximum lyric availability.
- **Auto-Clear**: Automatically removes the custom status when playback is paused or stopped.
- **One-Click Run**: Includes a Windows batch script (`.bat`) that handles library installation and runs the sync.

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.8+** installed.
- A Spotify Account.
- A Discord Account.

### 2. Configure Credentials
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. **Spotify API Setup**:
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   - Create a new App. Use `http://localhost:8888/callback` as the **Redirect URI**.
   - Copy the Client ID and Client Secret into your `.env` file under `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET`.

3. **Discord Token Setup**:
   - Open Discord in your web browser.
   - Press `F12` (or `Cmd+Option+I` on Mac) to open Developer Tools, and head to the **Network** tab.
   - Send a message in any chat, and search for the `/api/` requests.
   - Look under **Request Headers** for the `Authorization` header value. This is your personal account token.
   - Copy and paste this token into your `.env` file under `DISCORD_TOKEN`. 

---

## Running the App

### Windows (One-Click)
Simply double-click the **`run discord lyric .bat`** file. It will automatically check for and install missing Python packages, then start the program.

### Manual Launch
1. Install dependencies:
   ```bash
   pip install spotipy requests websocket-client python-dotenv syncedlyrics
   ```
2. Run the application:
   ```bash
   python discord-lyric-status.py
   ```

---

## Configuration (.env)

| Key | Description |
| :--- | :--- |
| `SPOTIPY_CLIENT_ID` | Your Spotify developer client identifier. |
| `SPOTIPY_CLIENT_SECRET` | Your Spotify developer client secret. |
| `SPOTIPY_REDIRECT_URI` | Spotify OAuth redirect uri (Default: `http://127.0.0.1:8888/callback`). |
| `DISCORD_TOKEN` | Discord authorization token used to update status. |

---

## Dependencies & Licenses

This project relies on the following third-party open-source libraries:

- **[Spotipy](https://github.com/spotipy-dev/spotipy)** (MIT License) - A lightweight Python library for the Spotify Web API.
- **[syncedlyrics](https://github.com/moehmeni/syncedlyrics)** (MIT License) - Used to fetch and scrape synchronized LRC format lyrics from NetEase, Musixmatch, LRCLib, and Megalobiz.
- **[Requests](https://github.com/psf/requests)** (Apache 2.0 License) - An elegant and simple HTTP library for Python.
- **[websocket-client](https://github.com/websocket-client/websocket-client)** (Apache 2.0 License) - A WebSocket client for Python.
- **[python-dotenv](https://github.com/theofidry/django-dotenv-checker)** (BSD 3-Clause License) - Reads key-value pairs from a `.env` file and sets them as environment variables.
