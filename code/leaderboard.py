import pandas as pd
import sys
import os
import json

def get_current_ratings(game_folder):
    """Read current ratings from player CSV files"""
    # Determine the correct database path based on where we're running from
    database_path = "database" if os.path.exists("database") else "../database"
    
    # Build full path to the game folder
    game_dir = os.path.join(database_path, game_folder)
    
    if not os.path.exists(game_dir):
        print(f"Game directory not found: {game_dir}")
        return {}, {}, {}
    
    ratings = {}
    games_played = {}
    unique_opponents = {}

    for filename in os.listdir(game_dir):
        if filename.endswith('.csv'):
            player_name = filename[:-4]
            filepath = os.path.join(game_dir, filename)

            try:
                df = pd.read_csv(filepath)
                if not df.empty:
                    current_rating = df['rating'].iloc[-1]
                    ratings[player_name] = current_rating

                    # Count games played (rows minus initial rating row)
                    games_played[player_name] = len(df) - 1

                    # Count unique opponents (exclude "no opponent" initial row)
                    opponents = df['opponent'].dropna().unique()
                    opponents = [o for o in opponents if o != 'no opponent']
                    unique_opponents[player_name] = len(opponents)
            except Exception as e:
                print(f"Error reading file {filepath}: {e}")

    return ratings, games_played, unique_opponents

def create_leaderboard_json(game_folder, excluded_players=None):
    """Create leaderboard data in JSON format for Plotly.js"""
    if excluded_players is None:
        excluded_players = []

    ratings, games_played, unique_opponents = get_current_ratings(game_folder)

    if not ratings:
        return {"error": f"No player data found in {game_folder}"}

    # Filter out excluded players
    filtered_ratings = {player: rating for player, rating in ratings.items()
                       if player.lower() not in [excluded.lower() for excluded in excluded_players]}

    if not filtered_ratings:
        return {"error": f"No players remaining after exclusions in {game_folder}"}

    # Find max games and max unique opponents (for badges)
    filtered_players = list(filtered_ratings.keys())
    max_games = max(games_played.get(p, 0) for p in filtered_players)
    max_opponents = max(unique_opponents.get(p, 0) for p in filtered_players)

    # Sort players: first by whether they've played games, then by rating
    sorted_players = sorted(filtered_ratings.items(),
                          key=lambda x: (games_played[x[0]] > 0, x[1]),
                          reverse=True)

    # Prepare data for Plotly
    players_data = []
    for i, (player, rating) in enumerate(sorted_players):
        # Format player name
        display_name = player.replace('_', ' ').title()
        display_name = display_name.replace(' Q', ' (-♛)')

        # Determine status and color
        player_games = games_played[player]
        player_opponents = unique_opponents.get(player, 0)
        if player_games == 0:
            status = "new"
            color = "#90EE90"  # Light green
        elif i == 0:
            status = "gold"
            color = "#FFD700"  # Gold
        elif i == 1:
            status = "silver"
            color = "#C0C0C0"  # Silver
        elif i == 2:
            status = "bronze"
            color = "#CD7F32"  # Bronze
        else:
            status = "regular"
            color = "#E8E8E8"  # Light gray

        # Determine badges (ties allowed)
        badges = []
        if player_games > 0 and player_games == max_games:
            badges.append("most_games")  # ⭐
        if player_opponents > 0 and player_opponents == max_opponents:
            badges.append("most_opponents")  # 🤝

        players_data.append({
            "position": i + 1,
            "player": player,
            "display_name": display_name,
            "rating": int(rating),
            "games_played": player_games,
            "unique_opponents": player_opponents,
            "badges": badges,
            "has_played": player_games > 0,  # Backwards compatibility
            "status": status,
            "color": color
        })
    
    # Generate title
    if '/' in game_folder:
        team, game_only = game_folder.split('/', 1)
        game_name = game_only.title()
    else:
        game_only = game_folder
        game_name = game_folder.title()
    
    return {
        "title": f'{game_name} Leaderboard',
        "game": game_only,
        "team": team if '/' in game_folder else None,
        "players": players_data,
        "total_players": len(players_data)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 leaderboard.py <game_folder> [--exclude player1] [--json] [--output filename] [--stdout]")
        print("Example: python3 leaderboard.py chess --json")
        print("Example: python3 leaderboard.py chess --json --output leaderboard.json")
        print("Example: python3 leaderboard.py chess --json --stdout")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    # Parse arguments
    excluded_players = []
    json_output = False
    output_file = None
    stdout_output = False
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--exclude" and i + 1 < len(sys.argv):
            excluded_players.append(sys.argv[i + 1].lower())
            i += 2
        elif sys.argv[i] == "--json":
            json_output = True
            i += 1
        elif sys.argv[i] == "--stdout":
            stdout_output = True
            i += 1
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if excluded_players:
        print(f"Excluding players: {', '.join(excluded_players)}", file=sys.stderr)
    
    # Generate JSON data
    data = create_leaderboard_json(game_folder, excluded_players)
    
    if stdout_output:
        # Output JSON to stdout for programmatic use
        print(json.dumps(data, indent=2))
    else:
        # File output (existing behavior)
        # Determine output file path
        if not output_file:
            # Auto-generate filename based on game_folder
            if '/' in game_folder:
                team, game_only = game_folder.split('/', 1)
                if os.path.exists('web'):
                    os.makedirs(f'web/{team}', exist_ok=True)
                    output_file = f'web/{team}/{game_only}_leaderboard.json'
                else:
                    os.makedirs(f'../web/{team}', exist_ok=True)
                    output_file = f'../web/{team}/{game_only}_leaderboard.json'
            else:
                if os.path.exists('web'):
                    output_file = f'web/{game_folder}_leaderboard.json'
                else:
                    output_file = f'../web/{game_folder}_leaderboard.json'
        
        # Write JSON file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Leaderboard JSON saved as {output_file}", file=sys.stderr)
        
        # Also print a summary
        if "error" not in data:
            print(f"\n{data['title']}:", file=sys.stderr)
            print("=" * 40, file=sys.stderr)
            for player_data in data['players']:
                player_name = player_data['display_name']
                rating = player_data['rating']
                position = player_data['position']
                print(f"{position:2d}. {player_name:<20} {rating:>4d}", file=sys.stderr)