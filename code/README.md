# ELO Rating System

A comprehensive ELO rating system for tracking player performance across multiple games. Features include rating calculations, visualizations, leaderboards, and data management tools.

## Quick Start

### 1. Submit Game Results
```bash
python3 main.py --game "chess" --player1 "dean" --player2 "eid" --score 0.0
```

**Parameters:**
- `--game`: Game type (e.g., "chess", "pingpong")
- `--player1`: First player (considered "white")
- `--player2`: Second player (considered "black") 
- `--score`: Result from player1's perspective (1.0 = player1 wins, 0.0 = player1 loses, 0.5 = draw)

**Example:**
```bash
# Dean beats Eid
python3 main.py --game "chess" --player1 "dean" --player2 "eid" --score 1.0

# Draw between Anthony and Gavin
python3 main.py --game "chess" --player1 "anthony" --player2 "gavin" --score 0.5
```

### 2. View Rating Progression Graph
```bash
python3 graph.py "chess/dean.csv" "chess/eid.csv" "chess/anthony.csv"
```

**Features:**
- Shows rating progression over time for all specified players
- Automatically extends timeline to include all games
- Displays player names directly on the lines
- Shows dots for start points, each game, and end points
- Saves as `web/chess_ratings_progress.png` (or appropriate game name)

**Example:**
```bash
# View all chess players
python3 graph.py chess/dean.csv chess/eid.csv chess/grace.csv chess/gavin.csv chess/oliver.csv chess/>

```

### 3. Generate Leaderboard
```bash
python3 leaderboard.py chess
```

**Features:**
- Shows current ratings for all players in the game
- Includes medal images for top 3 players
- Highlights new players (who haven't played yet) in green
- Displays player images from `images/players/` folder
- Saves as `web/chess_leaderboard.png`

**Options:**
```bash
# Exclude specific players
python3 leaderboard.py chess --exclude anthony

# Multiple exclusions
python3 leaderboard.py chess --exclude anthony --exclude gavin
```

## Player Management

### Add New Players
```bash
python3 new_player.py
```

**How it works:**
1. Edit `new_player.py` to specify new players and games
2. Run the script to create player files
3. Players start with 1200 rating

**Example `new_player.py` content:**
```python
make_new_player("gavin", "chess")
make_new_player("oliver", "chess")
make_new_player("gavin", "pingpong")
```

### Delete Last Game Entry
```bash
python3 update.py --delete_last_entry chess dean gavin
```

**Use cases:**
- Undo incorrect game results
- Remove test games
- Fix data entry errors

**Example:**
```bash
# Delete last entry for 2 players
python3 update.py --delete_last_entry chess dean gavin

# Delete last entry for multiple players
python3 update.py --delete_last_entry chess dean gavin anthony eve
```

## File Structure

```
ELO/
├── main.py              # Submit game results
├── graph.py             # Generate rating progression graphs
├── leaderboard.py       # Generate leaderboards
├── new_player.py        # Add new players
├── update.py            # ELO calculations and utilities
├── chess/               # Chess game data
│   ├── dean.csv
│   ├── eid.csv
│   ├── anthony.csv
│   └── ...
├── pingpong/            # Ping pong game data
│   ├── dean.csv
│   ├── anthony.csv
│   └── ...
├── web/                 # Generated visualizations
│   ├── chess_ratings_progress.png
│   ├── chess_leaderboard.png
│   └── ...
└── images/              # Custom images
    ├── medals/          # Medal images (1st.png, 2nd.png, 3rd.png)
    └── players/         # Player photos (player_name.png)
```

## Data Format

Each player's CSV file contains:
- `rating`: Current ELO rating
- `opponent`: Opponent's name
- `result`: Game result (1.0 = win, 0.0 = loss, 0.5 = draw)
- `colour`: Player color (white/black)
- `timestamp`: When the game was played

## ELO Rating System

- **Starting Rating**: 1200 for all new players
- **K-Factor**: 40 (rating change multiplier)
- **Calculation**: Standard ELO formula with probability-based expected scores

## Visualization Features

### Rating Graphs
- **Dynamic Timeline**: Automatically adjusts from hours to days as needed
- **Player Names**: Displayed directly on lines (no legend needed)
- **Game Dots**: Shows start point, each game, and end point
- **Inactive Players**: Shown with dashed lines and transparency
- **Total Games**: Displayed in title

### Leaderboards
- **Medal System**: Gold, silver, bronze for top 3
- **New Player Highlighting**: Green background for players who haven't played
- **Player Images**: Custom photos from `images/players/` folder
- **Exclusion Options**: Remove specific players from leaderboard
- **Tie Breaking**: Players who have played games rank above those who haven't

## Customization

### Adding Player Images
1. Place PNG files in `images/players/` folder
2. Name files exactly as player names (e.g., `dean.png`, `anthony.png`)
3. Images will appear next to player names on leaderboards

### Adding Medal Images
1. Place PNG files in `images/medals/` folder
2. Name files as `1st.png`, `2nd.png`, `3rd.png`
3. Medals will appear for top 3 players on leaderboards

### Adding New Games
1. Create a new folder (e.g., `basketball/`)
2. Add players using `new_player.py`
3. Start submitting results with `--game "basketball"`

## Troubleshooting

### Common Issues
- **ModuleNotFoundError**: Install required packages with `pip3 install --break-system-packages numpy pandas matplotlib`
- **File not found**: Ensure game folder exists before adding players
- **No games to delete**: Players with only initial rating can't have entries deleted

### Data Recovery
- All data is stored in CSV files in game folders
- Use `--delete_last_entry` to undo recent games
- Player files can be manually edited if needed

## Examples

### Complete Workflow
```bash
# 1. Add new players
python3 new_player.py

# 2. Submit some games
python3 main.py --game "chess" --player1 "dean" --player2 "anthony" --score 1.0
python3 main.py --game "chess" --player1 "gavin" --player2 "dean" --score 0.0

# 3. View progress
python3 graph.py chess/dean.csv chess/anthony.csv chess/gavin.csv

# 4. Check leaderboard
python3 leaderboard.py chess

# 5. Undo last game if needed
python3 update.py --delete_last_entry chess gavin dean
```
