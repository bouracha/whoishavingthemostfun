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
Server runs on http://localhost:8080

### Testing
```bash
python test_simulated_data.py  # Compare test data with main database
```

### Chart data generation (manual)
```bash
cd code
python leaderboard.py <game> --json    # Generate JSON data for interactive charts
python graph.py <player_csv_files> --json  # Generate JSON data for ratings progress
```

### Player and game management
```bash
cd code
python manage_players.py list <game>
echo "<player>" | python manage_players.py delete <game> <player>

# Game result management
python update.py --undo_last_result [--team <team>]  # Undo last game result
python update.py --new_player <game> <player>        # Create new player
python update.py --delete_player <game> <player>     # Delete player completely
```

## Architecture

### Core Components
- **server.py**: Flask API server (1400+ lines) - serves static files and comprehensive REST API
- **code/update.py**: ELO calculation engine and game result processing (1200+ lines)
  - Handles rating calculations with adjustable K-factors
  - Manages pending results system for admin approval
  - Contains undo functionality and audit logging
- **code/leaderboard.py**: Generates JSON leaderboard data for interactive charts
- **code/graph.py**: Creates JSON ratings progress data for interactive charts
- **code/config.py**: Game constants and K-factor configuration

### Data Storage Structure
- **Player data**: CSV files in `database/<game>/<player>.csv`
  - Format: rating, opponent, result, colour, timestamp
- **Results history**: `database/results.csv` with full game history and commentary
- **Pending results**: `database/pending_results.csv` for admin approval workflow
- **Team support**: `database/<team>/` directories for multi-tenant setup
- **Team configs**: `database/teams.json` with hashed passwords
- **Chart data**: `web/<game>_leaderboard.json` and `web/<game>_ratings_progress.json` (generated on-demand)

### Frontend Structure
- **Static files**: `web/` directory with vanilla HTML/JS/CSS
- **Common pages**: `index.html`, `game.html` (shared template)
- **Team pages**: `/t/<team>/<game>` routes for multi-tenant access
- **Assets**: Player images in `web/images/players/`, medal icons in `web/images/medals/`

## Key API Endpoints

### Main Database APIs
- `GET /api/health` - Health check
- `GET /api/players/<game>` - List players for a game
- `POST /api/players/<game>` - Add new player (body: `{"player_name": "name"}`)
- `DELETE /api/players/<game>/<player>` - Remove player
- `POST /api/results/<game>` - Submit game result (creates pending result)
- `GET /api/recent-results` - Get recent game results with pagination
- `GET /api/probability-matrix/<game>` - Head-to-head win probability matrix
- `POST /api/undo-last-result` - Undo the most recent game result

### Team-Specific APIs
- `POST /api/auth/login` - Team authentication
- `POST /api/auth/logout` - Logout from team
- `GET/POST /api/<team>/players/<game>` - Team player management
- `POST /api/<team>/results/<game>` - Submit team game result
- `GET /api/<team>/recent-results` - Team recent results
- `GET /api/<team>/probability-matrix/<game>` - Team probability matrix

### Admin APIs (Pending Results System)
- `GET /api/pending-results` - View pending results awaiting approval
- `POST /api/approve-all-pending` - Approve all pending results
- `DELETE /api/pending-results/<index>` - Delete specific pending result
- `DELETE /api/pending-results` - Clear all pending results
- `POST /api/pending-results/<index>/admin-note` - Add admin note to pending result

### Chart APIs
- `GET /api/charts/<game>/leaderboard` - JSON leaderboard data
- `GET /api/charts/<game>/ratings-progress` - JSON ratings progress data
- `POST /api/charts/<game>/generate` - Regenerate charts manually

## Important Development Notes

### Game Logic & Rating System
- Uses standard ELO rating calculations with adjustable K-factors per game
- K-factors: chess=40, pingpong=40, backgammon=10 (configured in `code/config.py`)
- Players with 20+ games get reduced K-factor (max 20) for rating stability
- Supports draws (result='1/2-1/2') in addition to wins/losses

### Pending Results System
- All game submissions go to pending queue first (`pending_results.csv`)
- Admin must approve results before they affect ratings and charts
- Includes commentary generation and comment system for each result
- Undo functionality removes from both `results.csv` and player CSV files

### Multi-tenant Architecture
- Teams isolated via `database/<team>/` directories
- Team authentication using hashed passwords in `database/teams.json`
- Each team has separate player pools, results, and charts
- URLs: `/t/<team>/<game>` for team-specific pages

### Chart Generation
- **Dynamic generation only** - JSON data generated on-demand via API endpoints
- **Interactive charts** rendered client-side using Plotly.js
- **No file storage** - chart data served directly from memory
- **Real-time updates** - charts update instantly when data changes

### File Paths & Context Awareness
- Scripts detect running context: root directory (server) vs `code/` directory (CLI)
- Database paths adjust automatically: `database/` or `../database/`
- Player images fallback to `web/images/players/default.png` if specific image missing
- Chart scripts support `--stdout` flag for in-memory server integration

### Production Deployment
- Uses Nginx reverse proxy (see SERVER_README.md)
- Supports HTTPS via Let's Encrypt certificates
- Flask serves on localhost:8080, Nginx forwards from 80/443