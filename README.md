# Who Is Having The Most Fun — ELO Rating System

A simple, production-ready web app to track ELO ratings across multiple games (Chess, Ping Pong, Backgammon).

Monica Geller once asked: “If we're not keeping score, how do we know who's having the most fun?” This app answers that—with leaderboards, rating progress charts, and an easy way to add players.

## Architecture Overview

- **Frontend (static)**: `web/` served by Nginx (prod) or Flask (dev)
  - Pages: `index.html`, `chess.html`, `pingpong.html`, `backgammon.html`
  - Images: `web/images/`
- **Backend (API)**: Python Flask in `server.py`
  - Endpoints: `GET /api/health`, `POST /api/players/<game>`
  - Generates charts via `code/leaderboard.py` and `code/graph.py`
- **Data**: CSV files per player under `database/<game>/<player>.csv`
- **Production**: EC2 + Nginx reverse proxy + Let’s Encrypt (HTTPS)

## Quickstart (Local)

1) Python 3.9+ recommended
2) From project root:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```
3) Open: `http://localhost:8080`

Notes
- The homepage shows a banner only if the API is offline.
- Add players from `chess.html`, `pingpong.html`, `backgammon.html` via the modal.

## Quickstart (Production Overview)

Deployed on an EC2 instance using:
- Nginx (ports 80/443) proxying to Flask on `127.0.0.1:8080`
- Let’s Encrypt (Certbot) for HTTPS certificates
- Flask started by `update.sh`

See `SERVER_README.md` for a step‑by‑step runbook (install, configure Nginx, obtain certs, logs, renewals).

## Directory Structure (annotated)

```
whoishavingthemostfun/
  web/                 # Static frontend pages and generated charts (PNG)
  code/                # Python logic for charts and utilities
  database/            # CSV files per game/player (not tracked by git)
  server.py            # Flask API and static server (dev)
  manage_players.py    # Backend-only player management (list/delete)
  SERVER_README.md     # Production deployment/runbook
  README.md            # You are here
```

## API Overview

- `GET /api/health`
  - Response: `{ "status": "healthy", "message": "ELO server is running" }`

- `POST /api/players/<game>` (Body: JSON)
  - Request: `{ "player_name": "anthony" }`
  - Response: `{ "status": "success" | "error", "message": "..." }`
  - Games: `chess`, `pingpong`, `backgammon`

The frontend JS uses same-origin relative paths, so it runs identically on localhost and in production.

## Data Model

- Each player has a CSV: `database/<game>/<player>.csv`
- New players start at game-default rating; charts regenerate after updates
- Chart generators:
  - `code/leaderboard.py <game>` → `web/<game>_leaderboard.png`
  - `code/graph.py <csv...>` → `web/<game>_ratings_progress.png`

## Operations

- Update & restart on EC2:
```
cd ~/site
./update.sh
```
- Logs: `tail -f server.log` (Flask), `/var/log/nginx/*.log` (Nginx)
- Player management (backend-only):
```
python3 manage_players.py list <game>
echo "<player>" | python3 manage_players.py delete <game> <player>
```

## Configuration & Constants

- Game constants live in `code/config.py`
  - K-factor defaults: chess=40, pingpong=40, backgammon=10

## Troubleshooting (Top Issues)

- “Server Offline” banner: API not reachable (Flask not running or blocked network)
- Port conflicts: kill old Flask (`pkill -f "python.*server.py"`) or change port
- Paths when running scripts manually: run from project root
- HTTPS issues: verify Nginx 80/443 open, certbot installed, and `server_name` matches domain

## Security & Privacy

- HTTPS via Let’s Encrypt in production
- CSVs and generated charts are excluded from git for privacy/size

## Credits

Built for friends and family score‑keeping. “If we’re not keeping score…” 😉

