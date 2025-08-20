# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An ELO rating system web application for tracking scores across multiple games (Chess, Ping Pong, Backgammon). Built with Python Flask backend and vanilla HTML/JS frontend.

## Development Commands

### Starting the server
```bash
# Local development
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### Testing
```bash
python test_simulated_data.py  # Compare test data with main database
```

### Chart generation (manual)
```bash
cd code
python leaderboard.py <game>           # Generate leaderboard chart
python graph.py <player_csv_files>     # Generate ratings progress chart
```

### Player management (backend only)
```bash
cd code
python manage_players.py list <game>
echo "<player>" | python manage_players.py delete <game> <player>
```

## Architecture

### Core Components
- **server.py**: Flask API server serving both static files and REST endpoints
- **code/update.py**: ELO calculation engine and game result processing
- **code/leaderboard.py**: Generates PNG leaderboard charts with player photos
- **code/graph.py**: Creates ratings progress line charts
- **code/config.py**: Game constants (K-factors: chess=40, pingpong=40, backgammon=10)

### Data Storage
- Player data: CSV files in `database/<game>/<player>.csv`
- Each CSV contains: timestamp, opponent, result (1/0), rating_before, rating_after
- Team configurations: `database/teams.json`
- Generated charts: `web/<game>_leaderboard.png` and `web/<game>_ratings_progress.png`

### Frontend Structure
- Static files in `web/` directory
- Game-specific pages: `chess.html`, `pingpong.html`, `backgammon.html`  
- Player images: `web/images/players/<player>.png` (fallback to `default.png`)
- Medal icons: `web/images/medals/1st.png`, `2nd.png`, `3rd.png`

## Key API Endpoints

- `GET /api/health` - Health check
- `POST /api/players/<game>` - Add new player (body: `{"player_name": "name"}`)
- `GET /api/probability-matrix/<game>` - Get head-to-head win probabilities matrix
- `GET /api/<team>/probability-matrix/<game>` - Team-specific probability matrix
- Game submission handled via `submit_game_with_charts()` function

## Important Notes

- Charts are regenerated automatically after game submissions
- Player photos must be placed in `web/images/players/` manually
- The system supports multiple teams via `database/teams.json`
- All game logic uses ELO rating calculations from `code/update.py`
- Production deployment uses Nginx reverse proxy (see SERVER_README.md)