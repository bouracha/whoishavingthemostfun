# ELO Rating System Server

This Flask server provides a web API for managing players and generating charts for the ELO rating system.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Server:**
   ```bash
   python3 server.py
   ```

3. **Access the Application:**
   - Open your browser to: http://localhost:5000
   - The server will serve the web interface and handle API requests

## Features

### Web Interface
- **Point-and-click player management** - Add players with a simple modal form
- **Automatic chart generation** - Charts are regenerated when players are added
- **Real-time feedback** - Success/error messages for all operations
- **Responsive design** - Works on desktop and mobile

### API Endpoints

#### Get Players
```
GET /api/players/<game>
```
Returns list of players for a specific game.

#### Add Player
```
POST /api/players/<game>
Content-Type: application/json

{
  "player_name": "john"
}
```
Adds a new player to the specified game.

#### Remove Player
```
DELETE /api/players/<game>/<player_name>
```
Removes a player from the specified game.

#### Regenerate Charts
```
POST /api/charts/<game>/generate
```
Manually regenerate leaderboard and ratings charts.

## Directory Structure

```
whoishavingthemostfun/
├── server.py           # Flask server
├── requirements.txt    # Python dependencies
├── database/          # Player data (CSV files)
│   ├── chess/
│   └── pingpong/
├── web/               # Frontend files
│   ├── index.html
│   ├── chess.html
│   └── pingpong.html
└── code/              # Backend scripts
    ├── leaderboard.py
    ├── graph.py
    └── update.py
```

## Usage

1. Start the server with `python3 server.py`
2. Open http://localhost:5000 in your browser
3. Navigate to Chess or Ping Pong pages
4. Click "➕ Add Player" to add new players
5. Charts will automatically update after adding players

## Security Notes

- The server runs in debug mode for development
- Input validation prevents malicious player names
- CORS is enabled for frontend-backend communication
- Server-side script execution is controlled and sandboxed