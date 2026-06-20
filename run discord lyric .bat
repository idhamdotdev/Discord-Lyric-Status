@echo off
echo Installing/upgrading required python libraries...
pip install spotipy requests websocket-client python-dotenv syncedlyrics
echo.
echo Starting Spotify Lyrics - Discord Status Sync...
python discord-lyric-status.py
pause