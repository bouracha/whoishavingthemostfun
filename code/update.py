import numpy as np
import pandas as pd
from datetime import datetime
import argparse
import os
from typing import Optional

def update(rating1, rating2, score, K: int = 40):

    score1 = score
    score2 = 1 - score

    ratingDifference = np.abs(rating1 - rating2)

    probabilityOfWeakerPlayerWinning = (1.0 / (1.0 + (10 ** ((ratingDifference * 1.0/ 400)))))

    probabilityOfStrongerPlayerWinning = 1 - probabilityOfWeakerPlayerWinning

    if (rating1 > rating2):
        prob_of_1_winning = probabilityOfStrongerPlayerWinning
        prob_of_2_winning = probabilityOfWeakerPlayerWinning
    else:
        prob_of_1_winning = probabilityOfWeakerPlayerWinning
        prob_of_2_winning = probabilityOfStrongerPlayerWinning


    rating_change1 = (score1 - prob_of_1_winning) * K
    rating_change2 = (score2 - prob_of_2_winning) * K

    if np.abs(rating_change1) < 1 and rating_change1 != 0:
        rating_change1 = rating_change1/np.abs(rating_change1)
    if np.abs(rating_change2) < 1 and rating_change2 != 0:
        rating_change2 = rating_change2/np.abs(rating_change2)

    newRating1 = rating1 + rating_change1
    newRating2 = rating2 + rating_change2

    return round(newRating1), round(newRating2), prob_of_1_winning



def write_new_rating(
    player,
    new_rating,
    opponent,
    result,
    game='chess',
    colour='white',
    team=None,
    timestamp: Optional[str] = None,
):
    """Append a rating row. Optional timestamp overrides the default of now.

    timestamp should be a string formatted as 'YYYY-MM-DD HH:MM:SS' if provided.
    """
    ts = timestamp if timestamp else datetime.now()
    df = pd.DataFrame(np.array(np.expand_dims((new_rating, opponent, result, colour, ts), axis=0)))
    
    # Determine the correct path (database/ or ../database/), with optional team scoping
    database_path = "database" if os.path.exists("database") else "../database"
    if team:
        file_path = f"{database_path}/{team}/{game}/{player}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    else:
        file_path = f"{database_path}/{game}/{player}.csv"
    
    with open(file_path, 'a') as f:
        df.to_csv(f, header=False, index=False)


def read_ratings(player1, player2, game='chess', team=None):
    # Determine the correct path (database/ or ../database/), with optional team scoping
    database_path = "database" if os.path.exists("database") else "../database"
    base_dir = f'{database_path}/{team}/{game}' if team else f'{database_path}/{game}'
    
    data1 = pd.read_csv(f'{base_dir}/{player1}.csv')
    data2 = pd.read_csv(f'{base_dir}/{player2}.csv')

    rating1 = np.array(data1['rating'])
    rating2 = np.array(data2['rating'])

    return rating1, rating2

def make_new_player(
    player_name: str = 'default',
    game: str = 'chess',
    team: Optional[str] = None,
    starting_rating: float = 1200.0,
    starting_timestamp: Optional[str] = None,
):
    import os
    
    # Determine the correct path based on where we're running from, with optional team scoping
    if os.path.exists('database'):
        # Running from root directory (server context)
        if team:
            file_path = f'database/{team}/{game}/{player_name}.csv'
            database_dir = f'database/{team}/{game}'
        else:
            file_path = f'database/{game}/{player_name}.csv'
            database_dir = f'database/{game}'
    else:
        # Running from code directory (command line context)
        if team:
            file_path = f'../database/{team}/{game}/{player_name}.csv'
            database_dir = f'../database/{team}/{game}'
        else:
            file_path = f'../database/{game}/{player_name}.csv'
            database_dir = f'../database/{game}'
    
    # Ensure the game directory exists
    os.makedirs(database_dir, exist_ok=True)
    
    # Only create new player if file doesn't exist
    if not os.path.exists(file_path):
        head = np.array(['rating', 'opponent', 'result', 'colour', 'timestamp'])
        initial_ts = starting_timestamp if starting_timestamp else 'beginning of time'
        df = pd.DataFrame(np.array(np.expand_dims((starting_rating, 'no opponent', 0, 'no colour', initial_ts), axis=0)))
        df.to_csv(file_path, header=head, index=False)
        if starting_timestamp:
            print(
                f"Created new player '{player_name}' for game '{game}' with starting rating {starting_rating} at {starting_timestamp}"
            )
        else:
            print(f"Created new player '{player_name}' for game '{game}' with starting rating {starting_rating}")
    else:
        print(f"Player '{player_name}' already exists for game '{game}' - skipping creation")

def log_result_to_team(player1, player2, result, game, team, probability, timestamp: Optional[str] = None):
    """
    Log a game result to the results.csv file for recent results display.
    Works for both team games and main database games.
    """
    import os
    
    # Determine the correct path based on where we're running from
    database_path = "database" if os.path.exists("database") else "../database"
    
    if team:
        results_file = f"{database_path}/{team}/results.csv"
        # Ensure team directory exists
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
    else:
        results_file = f"{database_path}/results.csv"
    
    # Create headers if file doesn't exist
    if not os.path.exists(results_file):
        headers = ['timestamp', 'game', 'player1', 'player2', 'result', 'probability']
        df_headers = pd.DataFrame(columns=headers)
        df_headers.to_csv(results_file, index=False)
    
    # Prepare the new result entry
    now = datetime.now()
    ts = timestamp if timestamp else now.strftime('%Y-%m-%d %H:%M:%S')
    new_entry = {
        'timestamp': ts,
        'game': game,
        'player1': player1,
        'player2': player2,
        'result': result,
        'probability': f"{probability:.3f}"
    }
    
    # Append to the results file
    df_new = pd.DataFrame([new_entry])
    df_new.to_csv(results_file, mode='a', header=False, index=False)
    
    print(f"Logged result to {results_file}: {player1} vs {player2} ({result}) - probability: {probability:.3f}")

def delete_player(player_name, game='chess', team=None):
    """
    Completely delete a player from the specified game.
    This removes their CSV file and all their rating history.
    
    Args:
        player_name (str): Name of the player to delete
        game (str): The game name (e.g., 'chess', 'pingpong', 'backgammon')
    
    Returns:
        bool: True if player was deleted successfully, False otherwise
    """
    # Determine the correct path (database/ or ../database/), with optional team scoping
    database_path = "database" if os.path.exists("database") else "../database"
    file_path = f"{database_path}/{team}/{game}/{player_name}.csv" if team else f"{database_path}/{game}/{player_name}.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ Player '{player_name}' not found for game '{game}'")
        return False
    
    try:
        # Remove the player's CSV file
        os.remove(file_path)
        print(f"✅ Player '{player_name}' completely deleted from game '{game}'")
        print(f"   Removed file: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting player '{player_name}': {e}")
        return False

def delete_last_entry(game, players, team=None):
    """
    Delete the last entry for each specified player in the given game.
    
    Args:
        game (str): The game name (e.g., 'chess', 'pingpong')
        players (list): List of player names to delete last entry for
    """
    # Determine the correct path (database/ or ../database/)
    database_path = "database" if os.path.exists("database") else "../database"
    
    for player in players:
        file_path = f"{database_path}/{team}/{game}/{player}.csv" if team else f"{database_path}/{game}/{player}.csv"
        
        if not os.path.exists(file_path):
            print(f"Warning: Player '{player}' file not found for game '{game}'")
            continue
            
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Check if there are entries to delete (more than just the initial entry)
            if len(df) <= 1:
                print(f"Warning: Player '{player}' has no game entries to delete (only initial rating remains)")
                continue
                
            # Remove the last row (most recent game)
            df = df.iloc[:-1]
            
            # Save the updated data back to the file
            df.to_csv(file_path, index=False)
            print(f"Deleted last entry for player '{player}' in game '{game}'")
            
        except Exception as e:
            print(f"Error deleting last entry for player '{player}': {e}")

def undo_last_result(team=None):
    """
    Undo the last result from the database by:
    1. Reading the last result from results.csv
    2. Extracting the two player names
    3. Deleting that row from results.csv
    4. Deleting the last row from each player's CSV file
    
    Args:
        team (str): Optional team name. If None, uses main database.
    
    Returns:
        dict: Result summary with success/error info and details of what was undone
    """
    try:
        # Determine the correct path (database/ or ../database/)
        database_path = "database" if os.path.exists("database") else "../database"
        
        # Determine results file path
        if team:
            results_file = f"{database_path}/{team}/results.csv"
        else:
            results_file = f"{database_path}/results.csv"
        
        # Check if results file exists
        if not os.path.exists(results_file):
            return {'error': f'No results file found at {results_file}'}
        
        # Read the results file
        df = pd.read_csv(results_file)
        
        if df.empty:
            return {'error': 'No results found to undo'}
        
        # Get the last result
        last_result = df.iloc[-1]
        timestamp = last_result['timestamp']
        game = last_result['game']
        player1 = last_result['player1']
        player2 = last_result['player2']
        result = last_result['result']
        probability = last_result['probability']
        
        # Remove the last row from results.csv
        df = df.iloc[:-1]
        df.to_csv(results_file, index=False)
        
        # Delete the last entry from each player's CSV file
        players_to_update = [player1, player2]
        deleted_entries = []
        
        for player in players_to_update:
            player_file = f"{database_path}/{team}/{game}/{player}.csv" if team else f"{database_path}/{game}/{player}.csv"
            
            if not os.path.exists(player_file):
                print(f"Warning: Player '{player}' file not found for game '{game}'")
                continue
                
            try:
                # Read the player's CSV file
                player_df = pd.read_csv(player_file)
                
                # Check if there are entries to delete (more than just the initial entry)
                if len(player_df) <= 1:
                    print(f"Warning: Player '{player}' has no game entries to delete (only initial rating remains)")
                    continue
                    
                # Get the last entry details before deleting
                last_entry = player_df.iloc[-1]
                deleted_entries.append({
                    'player': player,
                    'rating': last_entry['rating'],
                    'opponent': last_entry['opponent'],
                    'result': last_entry['result'],
                    'colour': last_entry['colour'],
                    'timestamp': last_entry['timestamp']
                })
                
                # Remove the last row (most recent game)
                player_df = player_df.iloc[:-1]
                
                # Save the updated data back to the file
                player_df.to_csv(player_file, index=False)
                print(f"Deleted last entry for player '{player}' in game '{game}'")
                
            except Exception as e:
                print(f"Error deleting last entry for player '{player}': {e}")
                return {'error': f'Failed to delete entry for player {player}: {e}'}
        
        # Generate updated charts
        generate_charts_backend(game, team)
        
        return {
            'success': True,
            'message': f'Successfully undone last result: {player1} vs {player2} ({result})',
            'undone_result': {
                'timestamp': timestamp,
                'game': game,
                'player1': player1,
                'player2': player2,
                'result': result,
                'probability': probability
            },
            'deleted_entries': deleted_entries
        }
        
    except Exception as e:
        return {'error': f'Failed to undo last result: {e}'}

def submit_game_with_charts(player1, player2, result, game, team=None, timestamp=None):
    """
    Submit a game result and automatically regenerate charts, exactly like the Flask API does.
    
    Args:
        player1: First player name
        player2: Second player name  
        result: Result string ('1-0', '0-1', '1/2-1/2')
        game: Game type ('chess', 'pingpong', 'backgammon')
        team: Optional team name
        timestamp: Optional timestamp string (YYYY-MM-DD HH:MM:SS)
    
    Returns:
        dict: Result summary with success/error info
    """
    try:
        # Validate inputs
        if not player1 or not player2:
            return {'error': 'Both players are required'}
        
        if player1 == player2:
            return {'error': 'Players must be different'}
        
        if result not in ['1-0', '0-1', '1/2-1/2']:
            return {'error': 'Invalid result format'}
        
        # Convert result to score
        if result == '1-0':
            score = 1.0
        elif result == '0-1':
            score = 0.0
        else:  # 1/2-1/2
            score = 0.5
        
        # Read current ratings
        ratings1, ratings2 = read_ratings(player1, player2, game, team=team)
        rating1, rating2 = ratings1[-1], ratings2[-1]
        
        # Calculate new ratings and probability
        from config import get_k_factor
        new_rating1, new_rating2, probability = update(rating1, rating2, score, K=get_k_factor(game))
        
        # Write new ratings with timestamp
        write_new_rating(player1, new_rating1, player2, score, game, colour='white', team=team, timestamp=timestamp)
        write_new_rating(player2, new_rating2, player1, (1-score), game, colour='black', team=team, timestamp=timestamp)
        
        # Log result to recent results
        log_result_to_team(player1, player2, result, game, team, probability, timestamp=timestamp)
        
        # Generate charts (leaderboard and rating progress)
        generate_charts_backend(game, team)
        
        return {
            'success': True,
            'message': f'Result submitted: {player1} vs {player2} ({result})',
            'game': game,
            'player1': player1,
            'player2': player2,
            'result': result,
            'new_rating1': int(new_rating1),
            'new_rating2': int(new_rating2),
            'probability': probability
        }
        
    except Exception as e:
        return {'error': str(e)}

def generate_charts_backend(game, team=None):
    """Generate leaderboard and ratings progress charts, exactly like the Flask API does"""
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        # Determine database path (use the same logic as other functions)
        if os.path.exists('database'):
            db_path = "database"
        else:
            db_path = "../database"
            
        # Determine game directory
        if team:
            game_dir = f"{db_path}/{team}/{game}"
        else:
            game_dir = f"{db_path}/{game}"
        
        # Determine the correct working directory for running scripts
        if os.path.exists('code'):
            # Running from root directory (server context)
            script_cwd = 'code'
        else:
            # Running from code directory (command line context)
            script_cwd = '.'
        
        # Generate leaderboard
        try:
            if team:
                subprocess.run([
                    sys.executable, 'leaderboard.py', f"{team}/{game}"
                ], check=True, capture_output=True, text=True, cwd=script_cwd)
            else:
                subprocess.run([
                    sys.executable, 'leaderboard.py', game
                ], check=True, capture_output=True, text=True, cwd=script_cwd)
        except subprocess.CalledProcessError:
            # Leaderboard might fail if no players exist, that's okay
            pass
        
        # Generate ratings progress chart
        try:
            csv_files = list(Path(game_dir).glob('*.csv'))
            if csv_files:
                # Adjust CSV paths based on the working directory we'll be running from
                if script_cwd == 'code':
                    # Running from code directory, so paths need to go up one level
                    csv_paths = [f"../{csv_file}" for csv_file in csv_files]
                else:
                    # Running from root directory
                    csv_paths = [str(csv_file) for csv_file in csv_files]
                    
                subprocess.run([
                    sys.executable, 'graph.py'
                ] + csv_paths, check=True, capture_output=True, text=True, cwd=script_cwd)
        except subprocess.CalledProcessError:
            # Graph might fail if no actual games played, that's okay
            pass
            
    except Exception as e:
        print(f"Warning: Chart generation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ELO rating system utilities')
    parser.add_argument('--delete_last_entry', action='store_true', 
                       help='Delete the last entry for specified players')
    parser.add_argument('--delete_player', action='store_true',
                       help='Completely delete player(s) and all their data')
    parser.add_argument('--new_player', action='store_true',
                       help='Create new player(s) for the specified game')
    parser.add_argument('--undo_last_result', action='store_true',
                       help='Undo the last result from the database (removes from results.csv and player files)')
    parser.add_argument('--starting_rating', type=float, default=1200.0,
                       help='Starting rating for new players (default: 1200)')
    parser.add_argument('--starting_timestamp', type=str, default=None,
                       help='Optional starting timestamp for new players, format YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--team', type=str, default=None,
                       help='Team name (optional)')
    parser.add_argument('game', type=str, nargs='?', help='Game name (e.g., chess, pingpong) - not needed for undo_last_result')
    parser.add_argument('players', nargs='*', help='Player names - not needed for undo_last_result')
    
    args = parser.parse_args()
    
    if args.undo_last_result:
        result = undo_last_result(team=args.team)
        if result.get('success'):
            print(f"✅ {result['message']}")
            print(f"   Undone: {result['undone_result']['player1']} vs {result['undone_result']['player2']} ({result['undone_result']['result']})")
            print(f"   Game: {result['undone_result']['game']}")
            print(f"   Timestamp: {result['undone_result']['timestamp']}")
        else:
            print(f"❌ {result['error']}")
    elif args.delete_last_entry:
        delete_last_entry(args.game, args.players, team=args.team)
    elif args.delete_player:
        for player in args.players:
            delete_player(player, args.game, team=args.team)
    elif args.new_player:
        for player in args.players:
            make_new_player(
                player,
                args.game,
                team=args.team,
                starting_rating=args.starting_rating,
                starting_timestamp=args.starting_timestamp,
            )
    else:
        print("Usage:")
        print("  Undo last result: python3 update.py --undo_last_result [--team <team_name>]")
        print("  Create new player(s): python3 update.py --new_player <game> <player1> [player2] ...")
        print("                        [--starting_rating <rating>] [--starting_timestamp 'YYYY-MM-DD HH:MM:SS']")
        print("  Delete last entry: python3 update.py --delete_last_entry <game> <player1> [player2] ...")
        print("  Delete player(s): python3 update.py --delete_player <game> <player1> [player2] ...")
        print("")
        print("Examples:")
        print("  python3 update.py --undo_last_result")
        print("  python3 update.py --undo_last_result --team bourached")
        print("  python3 update.py --new_player chess anthony")
        print("  python3 update.py --new_player chess grandmaster --starting_rating 2500 --starting_timestamp '2023-01-01 12:00:00'")
        print("  python3 update.py --new_player pingpong gavin eve dean")
        print("  python3 update.py --delete_last_entry chess dean gavin")
        print("  python3 update.py --delete_player chess testplayer")