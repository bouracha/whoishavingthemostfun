import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import argparse
import os
from typing import Optional


def normalize_timestamp_to_minute(timestamp_str: str) -> str:
    """
    Normalize a timestamp string to minute precision for comparison.
    Handles various timestamp formats and truncates to YYYY-MM-DD HH:MM format.
    
    Args:
        timestamp_str: Timestamp string in various formats
        
    Returns:
        Normalized timestamp string in YYYY-MM-DD HH:MM format
    """
    try:
        # Handle pandas Timestamp objects
        if hasattr(timestamp_str, 'strftime'):
            return timestamp_str.strftime('%Y-%m-%d %H:%M')
        
        # Handle string timestamps
        ts_str = str(timestamp_str).strip()
        
        # Parse different formats
        if '.' in ts_str:
            # Format with microseconds: 2023-12-07 14:30:25.123456
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
        elif len(ts_str) == 19:
            # Format with seconds: 2023-12-07 14:30:25
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        elif len(ts_str) == 16:
            # Already minute format: 2023-12-07 14:30
            return ts_str
        else:
            # Try pandas parsing as fallback
            dt = pd.to_datetime(ts_str)
            
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        # Return original string if parsing fails
        return str(timestamp_str)


def calculate_elo_probability(rating_a: float, rating_b: float) -> float:
    """
    Calculate the probability that player A beats player B based on ELO ratings.
    Uses the standard ELO formula: P(A beats B) = 1 / (1 + 10^((rating_b - rating_a) / 400))
    
    Args:
        rating_a: ELO rating of player A
        rating_b: ELO rating of player B
    
    Returns:
        Probability (0.0 to 1.0) that player A beats player B
    """
    return 1.0 / (1.0 + (10 ** ((rating_b - rating_a) / 400)))

def update(rating1, rating2, score, K: int = 40):
    """Legacy update function - refactored to use shared probability calculation"""
    score1 = score
    score2 = 1 - score

    # Use shared probability calculation function
    prob_of_1_winning = calculate_elo_probability(rating1, rating2)
    prob_of_2_winning = calculate_elo_probability(rating2, rating1)

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
    # Always use UK time (UTC+0 in winter, UTC+1 in summer)
    import time
    uk_time = datetime.utcnow()
    # Add 1 hour for BST (British Summer Time) - March to October
    # Simple heuristic: if month is 3-10, add 1 hour
    if uk_time.month >= 3 and uk_time.month <= 10:
        uk_time = uk_time + timedelta(hours=1)
    ts = timestamp if timestamp else uk_time
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


def count_player_games(player, game='chess', team=None):
    """
    Count the number of games a player has played (excluding the initial rating entry).
    
    Args:
        player (str): Player name
        game (str): Game type
        team (str): Optional team name
    
    Returns:
        int: Number of games played (0 if player doesn't exist)
    """
    try:
        # Determine the correct path (database/ or ../database/), with optional team scoping
        database_path = "database" if os.path.exists("database") else "../database"
        player_file = f"{database_path}/{team}/{game}/{player}.csv" if team else f"{database_path}/{game}/{player}.csv"
        
        if not os.path.exists(player_file):
            return 0
            
        data = pd.read_csv(player_file)
        # Subtract 1 to exclude the initial rating entry
        return max(0, len(data) - 1)
        
    except Exception as e:
        print(f"Error counting games for player '{player}': {e}")
        return 0

def get_adjusted_k_factor(player, game='chess', team=None):
    """
    Get the K-factor for a player, adjusted based on their number of games.
    Players with 20+ games get a reduced K-factor (max of 20).
    
    Args:
        player (str): Player name
        game (str): Game type
        team (str): Optional team name
    
    Returns:
        int: Adjusted K-factor
    """
    from config import get_k_factor
    
    base_k_factor = get_k_factor(game)
    games_played = count_player_games(player, game, team)
    
    # If player has 20+ games, reduce K-factor to max(20, base_k_factor)
    if games_played >= 20:
        return min(20, base_k_factor)
    
    return base_k_factor

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

def log_result_to_team(
    player1,
    player2,
    result,
    game,
    team,
    probability,
    timestamp: Optional[str] = None,
    player1_change: Optional[float] = None,
    player2_change: Optional[float] = None,
    comment: Optional[str] = None,
):
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
    
    # Create headers if file doesn't exist (with change and comments columns)
    if not os.path.exists(results_file):
        headers = [
            'timestamp', 'game', 'player1', 'player2', 'result', 'probability',
            'player1_change', 'player2_change', 'comments'
        ]
        df_headers = pd.DataFrame(columns=headers)
        df_headers.to_csv(results_file, index=False)
    else:
        # Ensure file has the new columns; if missing, backfill them
        try:
            existing = pd.read_csv(results_file)
            changed = False
            if 'player1_change' not in existing.columns:
                existing['player1_change'] = pd.NA
                changed = True
            if 'player2_change' not in existing.columns:
                existing['player2_change'] = pd.NA
                changed = True
            if 'comments' not in existing.columns:
                existing['comments'] = ''
                changed = True
            if changed:
                existing.to_csv(results_file, index=False)
        except Exception:
            # If anything goes wrong, proceed without altering existing file
            pass
    
    # Prepare the new result entry - always use UK time
    uk_time = datetime.utcnow()
    # Add 1 hour for BST (British Summer Time) - March to October
    if uk_time.month >= 3 and uk_time.month <= 10:
        uk_time = uk_time + timedelta(hours=1)
    ts = timestamp if timestamp else uk_time.strftime('%Y-%m-%d %H:%M:%S')
    new_entry = {
        'timestamp': ts,
        'game': game,
        'player1': player1,
        'player2': player2,
        'result': result,
        'probability': f"{probability:.3f}",
        'player1_change': int(round(player1_change)) if player1_change is not None else pd.NA,
        'player2_change': int(round(player2_change)) if player2_change is not None else pd.NA,
        'comments': comment if comment else '',
    }
    
    # Append to the results file
    df_new = pd.DataFrame([new_entry])
    df_new.to_csv(results_file, mode='a', header=False, index=False)
    
    print(
        f"Logged result to {results_file}: {player1} vs {player2} ({result}) - probability: {probability:.3f}, "
        f"changes: ({new_entry['player1_change']}, {new_entry['player2_change']})"
    )

def log_deleted_result(player1, player2, result, game, team=None, probability=None, original_timestamp=None, deletion_timestamp=None):
    """
    Log a deleted game result to the deleted.csv file for audit purposes.
    Works for both team games and main database games.
    """
    import os
    
    # Determine the correct path based on where we're running from
    database_path = "database" if os.path.exists("database") else "../database"
    
    if team:
        deleted_file = f"{database_path}/{team}/deleted.csv"
        # Ensure team directory exists
        os.makedirs(os.path.dirname(deleted_file), exist_ok=True)
    else:
        deleted_file = f"{database_path}/deleted.csv"
    
    # Create headers if file doesn't exist
    if not os.path.exists(deleted_file):
        headers = ['original_timestamp', 'deletion_timestamp', 'game', 'player1', 'player2', 'result', 'probability']
        df_headers = pd.DataFrame(columns=headers)
        df_headers.to_csv(deleted_file, index=False)
    
    # Prepare the deletion entry - always use UK time
    uk_time = datetime.utcnow()
    # Add 1 hour for BST (British Summer Time) - March to October
    if uk_time.month >= 3 and uk_time.month <= 10:
        uk_time = uk_time + timedelta(hours=1)
    deletion_ts = deletion_timestamp if deletion_timestamp else uk_time.strftime('%Y-%m-%d %H:%M:%S')
    
    new_entry = {
        'original_timestamp': original_timestamp,
        'deletion_timestamp': deletion_ts,
        'game': game,
        'player1': player1,
        'player2': player2,
        'result': result,
        'probability': f"{probability:.3f}" if probability is not None else "0.500"
    }
    
    # Append to the deleted file
    df_new = pd.DataFrame([new_entry])
    df_new.to_csv(deleted_file, mode='a', header=False, index=False)
    
    print(f"Logged deleted result to {deleted_file}: {player1} vs {player2} ({result}) - deleted at {deletion_ts}")

def log_pending_result(
    player1,
    player2,
    result,
    game,
    team,
    probability,
    timestamp: Optional[str] = None,
    player1_change: Optional[float] = None,
    player2_change: Optional[float] = None,
    comment: Optional[str] = None,
):
    """
    Log a game result to the pending_results.csv file for admin approval.
    Works for both team games and main database games.
    """
    import os
    
    # Determine the correct path based on where we're running from
    database_path = "database" if os.path.exists("database") else "../database"
    
    if team:
        pending_file = f"{database_path}/{team}/pending_results.csv"
        # Ensure team directory exists
        os.makedirs(os.path.dirname(pending_file), exist_ok=True)
    else:
        pending_file = f"{database_path}/pending_results.csv"
        # Ensure main database directory exists
        os.makedirs(database_path, exist_ok=True)
    
    # Create headers if file doesn't exist (same structure as results.csv + admin notes)
    if not os.path.exists(pending_file):
        headers = [
            'timestamp', 'game', 'player1', 'player2', 'result', 'probability',
            'player1_change', 'player2_change', 'comments', 'submission_timestamp', 'notes_to_admin'
        ]
        df_headers = pd.DataFrame(columns=headers)
        df_headers.to_csv(pending_file, index=False)
    else:
        # Ensure file has all columns; if missing, backfill them
        try:
            existing = pd.read_csv(pending_file)
            changed = False
            required_columns = ['player1_change', 'player2_change', 'comments', 'submission_timestamp', 'notes_to_admin']
            for col in required_columns:
                if col not in existing.columns:
                    if col == 'submission_timestamp':
                        existing[col] = pd.NA
                    elif col in ['comments', 'notes_to_admin']:
                        existing[col] = ''
                    else:
                        existing[col] = pd.NA
                    changed = True
            if changed:
                existing.to_csv(pending_file, index=False)
        except Exception:
            # If anything goes wrong, proceed without altering existing file
            pass
    
    # Prepare the pending result entry - always use UK time
    uk_time = datetime.utcnow()
    # Add 1 hour for BST (British Summer Time) - March to October
    if uk_time.month >= 3 and uk_time.month <= 10:
        uk_time = uk_time + timedelta(hours=1)
    
    game_timestamp = timestamp if timestamp else uk_time.strftime('%Y-%m-%d %H:%M:%S')
    submission_timestamp = uk_time.strftime('%Y-%m-%d %H:%M:%S')
    
    new_entry = {
        'timestamp': game_timestamp,
        'game': game,
        'player1': player1,
        'player2': player2,
        'result': result,
        'probability': f"{probability:.3f}",
        'player1_change': int(round(player1_change)) if player1_change is not None else pd.NA,
        'player2_change': int(round(player2_change)) if player2_change is not None else pd.NA,
        'comments': comment if comment else '',
        'submission_timestamp': submission_timestamp,
        'notes_to_admin': '',
    }
    
    # Append to the pending results file
    df_new = pd.DataFrame([new_entry])
    df_new.to_csv(pending_file, mode='a', header=False, index=False)
    
    print(
        f"Logged pending result to {pending_file}: {player1} vs {player2} ({result}) - "
        f"probability: {probability:.3f}, submitted at {submission_timestamp}"
    )

def approve_pending_results(team=None):
    """
    Approve all pending results by processing them in chronological order.
    Reads from pending_results.csv and processes each result using submit_game_with_charts().
    
    Args:
        team (str): Optional team name. If None, uses main database.
    
    Returns:
        dict: Result summary with success/error info and processing details
    """
    try:
        # Determine the correct path based on where we're running from
        database_path = "database" if os.path.exists("database") else "../database"
        
        # Determine pending results file path
        if team:
            pending_file = f"{database_path}/{team}/pending_results.csv"
        else:
            pending_file = f"{database_path}/pending_results.csv"
        
        # Check if pending results file exists
        if not os.path.exists(pending_file):
            return {'success': True, 'message': 'No pending results to approve', 'processed_count': 0}
        
        # Read the pending results file
        df = pd.read_csv(pending_file)
        
        if df.empty:
            return {'success': True, 'message': 'No pending results to approve', 'processed_count': 0}
        
        # Sort by submission timestamp to process in chronological order (oldest first)
        # Use timestamp as fallback if submission_timestamp is not available
        if 'submission_timestamp' in df.columns:
            df['sort_timestamp'] = pd.to_datetime(df['submission_timestamp'], format='mixed')
        else:
            df['sort_timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
        
        df_sorted = df.sort_values('sort_timestamp', ascending=True)
        
        processed_results = []
        failed_results = []
        
        for index, row in df_sorted.iterrows():
            try:
                # Extract result data
                player1 = row['player1']
                player2 = row['player2']
                result = row['result']
                game = row['game']
                timestamp = row['timestamp']
                
                # Process the result using existing logic (comment will be handled separately)
                # Don't generate charts for each individual result - we'll do it once at the end
                result_data = submit_game_without_charts(
                    player1=player1,
                    player2=player2,
                    result=result,
                    game=game,
                    team=team,
                    timestamp=timestamp
                )
                
                # After successful processing, copy comment from pending to results
                if (result_data.get('success') and 'comments' in row and row['comments'] 
                    and isinstance(row['comments'], str) and row['comments'].strip()):
                    try:
                        database_path = "database" if os.path.exists("database") else "../database"
                        results_file = f"{database_path}/{team}/results.csv" if team else f"{database_path}/results.csv"
                        
                        if os.path.exists(results_file):
                            results_df = pd.read_csv(results_file)
                            if not results_df.empty:
                                # Update the last result (most recent) with the pending comment
                                results_df.loc[results_df.index[-1], 'comments'] = row['comments'].strip()
                                results_df.to_csv(results_file, index=False)
                    except Exception as e:
                        print(f"Warning: Could not transfer comment: {e}")
                
                if result_data.get('success'):
                    processed_results.append({
                        'player1': player1,
                        'player2': player2,
                        'result': result,
                        'game': game,
                        'timestamp': timestamp
                    })
                    print(f"✅ Approved: {player1} vs {player2} ({result}) in {game}")
                else:
                    failed_results.append({
                        'player1': player1,
                        'player2': player2,
                        'result': result,
                        'game': game,
                        'error': result_data.get('error', 'Unknown error')
                    })
                    print(f"❌ Failed to approve: {player1} vs {player2} ({result}) - {result_data.get('error')}")
                    
            except Exception as e:
                failed_results.append({
                    'player1': row.get('player1', 'Unknown'),
                    'player2': row.get('player2', 'Unknown'),
                    'result': row.get('result', 'Unknown'),
                    'game': row.get('game', 'Unknown'),
                    'error': str(e)
                })
                print(f"❌ Exception processing result: {e}")
        
        # Clear the pending results file if all results were processed successfully
        if len(failed_results) == 0:
            # Remove the entire file
            os.remove(pending_file)
            print(f"✅ Cleared pending results file: {pending_file}")
        else:
            # Keep failed results in the file for retry
            failed_df = df_sorted[df_sorted.apply(
                lambda row: any(
                    failed['player1'] == row['player1'] and 
                    failed['player2'] == row['player2'] and
                    failed['result'] == row['result'] and
                    failed['game'] == row['game']
                    for failed in failed_results
                ), axis=1
            )]
            failed_df.to_csv(pending_file, index=False)
            print(f"⚠️  Kept {len(failed_results)} failed results in {pending_file}")
        
        # Ensure we have the correct count
        total_pending = len(df_sorted)
        processed_count = len(processed_results)
        failed_count = len(failed_results)
        
        return {
            'success': True,
            'message': f'Processed {processed_count} pending results successfully',
            'processed_count': processed_count,
            'failed_count': failed_count,
            'total_pending': total_pending,
            'processed_results': processed_results,
            'failed_results': failed_results
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to approve pending results: {e}'}

def delete_pending_result(index, team=None):
    """
    Delete a specific pending result by index.
    
    Args:
        index (int): Index of the result to delete (0-based)
        team (str): Optional team name. If None, uses main database.
    
    Returns:
        dict: Result summary with success/error info
    """
    try:
        # Determine the correct path based on where we're running from
        database_path = "database" if os.path.exists("database") else "../database"
        
        # Determine pending results file path
        if team:
            pending_file = f"{database_path}/{team}/pending_results.csv"
        else:
            pending_file = f"{database_path}/pending_results.csv"
        
        # Check if pending results file exists
        if not os.path.exists(pending_file):
            return {'success': False, 'error': 'No pending results file found'}
        
        # Read the pending results file
        df = pd.read_csv(pending_file)
        
        if df.empty:
            return {'success': False, 'error': 'No pending results to delete'}
        
        # Validate index
        if index < 0 or index >= len(df):
            return {'success': False, 'error': f'Invalid index {index}. Valid range: 0-{len(df)-1}'}
        
        # Get the result being deleted for logging
        deleted_result = df.iloc[index]
        deleted_info = {
            'player1': deleted_result['player1'],
            'player2': deleted_result['player2'],
            'result': deleted_result['result'],
            'game': deleted_result['game'],
            'timestamp': deleted_result['timestamp']
        }
        
        # Remove the result at the specified index
        df = df.drop(df.index[index])
        
        # Save the updated file
        if df.empty:
            # Remove the file if no results remain
            os.remove(pending_file)
            print(f"✅ Deleted last pending result, removed file: {pending_file}")
        else:
            # Save the remaining results
            df.to_csv(pending_file, index=False)
            print(f"✅ Deleted pending result at index {index}, {len(df)} results remaining")
        
        return {
            'success': True,
            'message': f'Deleted pending result: {deleted_info["player1"]} vs {deleted_info["player2"]} ({deleted_info["result"]})',
            'deleted_result': deleted_info,
            'remaining_count': len(df)
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to delete pending result: {e}'}

def clear_all_pending_results(team=None):
    """
    Clear all pending results by removing the pending_results.csv file.
    
    Args:
        team (str): Optional team name. If None, uses main database.
    
    Returns:
        dict: Result summary with success/error info
    """
    try:
        # Determine the correct path based on where we're running from
        database_path = "database" if os.path.exists("database") else "../database"
        
        # Determine pending results file path
        if team:
            pending_file = f"{database_path}/{team}/pending_results.csv"
        else:
            pending_file = f"{database_path}/pending_results.csv"
        
        # Check if pending results file exists
        if not os.path.exists(pending_file):
            return {'success': True, 'message': 'No pending results file to clear', 'deleted_count': 0}
        
        # Read the file to get count before deletion
        try:
            df = pd.read_csv(pending_file)
            deleted_count = len(df)
        except Exception:
            deleted_count = 0
        
        # Remove the file
        os.remove(pending_file)
        print(f"✅ Cleared all pending results: {deleted_count} results deleted")
        
        return {
            'success': True,
            'message': f'Cleared all pending results ({deleted_count} results deleted)',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to clear pending results: {e}'}

def add_admin_note_to_pending(index, note, team=None):
    """
    Add an admin note to a specific pending result by index.
    
    Args:
        index (int): Index of the result to add note to (0-based)
        note (str): The note to add for the admin
        team (str): Optional team name. If None, uses main database.
    
    Returns:
        dict: Result summary with success/error info
    """
    try:
        # Determine the correct path based on where we're running from
        database_path = "database" if os.path.exists("database") else "../database"
        
        # Determine pending results file path
        if team:
            pending_file = f"{database_path}/{team}/pending_results.csv"
        else:
            pending_file = f"{database_path}/pending_results.csv"
        
        # Check if pending results file exists
        if not os.path.exists(pending_file):
            return {'success': False, 'error': 'No pending results file found'}
        
        # Read the pending results file
        df = pd.read_csv(pending_file)
        
        if df.empty:
            return {'success': False, 'error': 'No pending results found'}
        
        # Validate index
        if index < 0 or index >= len(df):
            return {'success': False, 'error': f'Invalid index {index}. Valid range: 0-{len(df)-1}'}
        
        # Add the note to the specified result
        current_note = df.loc[index, 'notes_to_admin'] if 'notes_to_admin' in df.columns else ''
        if pd.isna(current_note) or current_note == '':
            df.loc[index, 'notes_to_admin'] = note.strip()
        else:
            # Append to existing note
            df.loc[index, 'notes_to_admin'] = f"{current_note}; {note.strip()}"
        
        # Save the updated file
        df.to_csv(pending_file, index=False)
        
        # Get result info for logging
        result_info = {
            'player1': df.iloc[index]['player1'],
            'player2': df.iloc[index]['player2'],
            'result': df.iloc[index]['result'],
            'game': df.iloc[index]['game'],
            'timestamp': df.iloc[index]['timestamp']
        }
        
        print(f"✅ Added admin note to pending result at index {index}: {note}")
        
        return {
            'success': True,
            'message': f'Admin note added to pending result: {result_info["player1"]} vs {result_info["player2"]} ({result_info["result"]})',
            'result_info': result_info,
            'note': note
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to add admin note: {e}'}

def format_comment_for_storage(comment, commenter_name):
    """
    Format a comment in the same way as add_comment_to_result() does.
    Returns a string representation of a list containing the formatted comment.
    """
    if not comment or not commenter_name:
        return ''
    
    new_comment = f'"{comment}" - {commenter_name}'
    comments_list = [new_comment]
    return str(comments_list)

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
        
        # Log the deleted result to deleted.csv before removing it
        log_deleted_result(
            player1=player1,
            player2=player2,
            result=result,
            game=game,
            team=team,
            probability=probability,
            original_timestamp=timestamp
        )
        
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

def submit_game_with_charts(player1, player2, result, game, team=None, timestamp=None, comment=None):
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
        rating1, rating2 = float(ratings1[-1]), float(ratings2[-1])
        
        # Get adjusted K-factors for each player
        k_factor1 = get_adjusted_k_factor(player1, game, team)
        k_factor2 = get_adjusted_k_factor(player2, game, team)
        
        # Calculate expected scores using the shared ELO probability function
        expected_score1 = calculate_elo_probability(rating1, rating2)
        expected_score2 = calculate_elo_probability(rating2, rating1)
        
        # Calculate rating changes using individual K-factors
        actual_score1 = score
        actual_score2 = 1 - score
        rating_change1 = (actual_score1 - expected_score1) * k_factor1
        rating_change2 = (actual_score2 - expected_score2) * k_factor2
        
        # Store the probability for player1 (same as original function)
        probability = expected_score1
        
        # Apply the changes
        new_rating1 = rating1 + rating_change1
        new_rating2 = rating2 + rating_change2
        
        # Write new ratings with timestamp
        write_new_rating(player1, new_rating1, player2, score, game, colour='white', team=team, timestamp=timestamp)
        write_new_rating(player2, new_rating2, player1, (1-score), game, colour='black', team=team, timestamp=timestamp)
        
        # Log result to recent results (persist per-game rating deltas)
        log_result_to_team(
            player1,
            player2,
            result,
            game,
            team,
            probability,
            timestamp=timestamp,
            player1_change=rating_change1,
            player2_change=rating_change2,
            comment=comment,
        )
        
        
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

def submit_game_without_charts(player1, player2, result, game, team=None, timestamp=None, comment=None):
    """
    Submit a game result WITHOUT generating charts (for batch processing).
    This is identical to submit_game_with_charts but skips the chart generation step.
    
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
        rating1, rating2 = float(ratings1[-1]), float(ratings2[-1])
        
        # Get adjusted K-factors for each player
        k_factor1 = get_adjusted_k_factor(player1, game, team)
        k_factor2 = get_adjusted_k_factor(player2, game, team)
        
        # Calculate expected scores using the shared ELO probability function
        expected_score1 = calculate_elo_probability(rating1, rating2)
        expected_score2 = calculate_elo_probability(rating2, rating1)
        
        # Calculate rating changes using individual K-factors
        actual_score1 = score
        actual_score2 = 1 - score
        rating_change1 = (actual_score1 - expected_score1) * k_factor1
        rating_change2 = (actual_score2 - expected_score2) * k_factor2
        
        # Store the probability for player1 (same as original function)
        probability = expected_score1
        
        # Apply the changes
        new_rating1 = rating1 + rating_change1
        new_rating2 = rating2 + rating_change2
        
        # Write new ratings with timestamp
        write_new_rating(player1, new_rating1, player2, score, game, colour='white', team=team, timestamp=timestamp)
        write_new_rating(player2, new_rating2, player1, (1-score), game, colour='black', team=team, timestamp=timestamp)
        
        # Log result to recent results (persist per-game rating deltas)
        log_result_to_team(
            player1,
            player2,
            result,
            game,
            team,
            probability,
            timestamp=timestamp,
            player1_change=rating_change1,
            player2_change=rating_change2,
            comment=comment,
        )
        
        # NOTE: Charts are NOT generated here - they will be generated once at the end
        
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

def add_comment_to_result(timestamp=None, comment=None, commenter_name=None, team=None, offset=0, index=0):
    """
    Add a comment to an existing game result in results.csv.
    Comments are stored as a list of strings in the format: ["comment text - CommenterName"]
    
    Args:
        timestamp (str): Legacy timestamp parameter (optional)
        comment (str): The comment text
        commenter_name (str): Name of the person making the comment
        team (str): Optional team name
        offset (int): Offset from the API call (for pagination)
        index (int): Index within the current page
    
    Returns:
        dict: Result with success/error info
    """
    try:
        # Determine the correct path based on where we're running from
        database_path = "database" if os.path.exists("database") else "../database"
        
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
            return {'error': 'No results found'}
        
        # Position-based matching: API shows results in reverse chronological order (newest first)
        # So offset=0, index=0 corresponds to the last row in the CSV
        # offset=0, index=1 corresponds to the second-to-last row, etc.
        
        # Calculate the actual row index in the dataframe
        # Total rows - 1 (for 0-based indexing) - offset - index
        total_rows = len(df)
        row_index = total_rows - 1 - offset - index
        
        # Validate the calculated index
        if row_index < 0 or row_index >= total_rows:
            return {'error': f'Invalid result position: offset={offset}, index={index} (total results: {total_rows})'}
        
        # For backward compatibility, also validate timestamp if provided
        if timestamp:
            actual_timestamp = df.iloc[row_index]['timestamp']
            # Normalize both timestamps to minute precision for comparison
            normalized_provided = normalize_timestamp_to_minute(timestamp)
            normalized_actual = normalize_timestamp_to_minute(actual_timestamp)
            if normalized_provided != normalized_actual:
                return {'error': f'Timestamp mismatch at position offset={offset}, index={index}. Expected "{normalized_provided}", but found "{normalized_actual}"'}
        
        # Get existing comments (handle both empty and populated cases)
        existing_comments = df.at[row_index, 'comments']
        
        # Parse existing comments
        if pd.isna(existing_comments) or existing_comments == '' or existing_comments == '[]':
            comments_list = []
        else:
            try:
                # Try to parse as a list
                import ast
                comments_list = ast.literal_eval(existing_comments) if isinstance(existing_comments, str) else existing_comments
                if not isinstance(comments_list, list):
                    comments_list = []
            except (ValueError, SyntaxError):
                # If parsing fails, treat as empty
                comments_list = []
        
        # Add new comment
        new_comment = f'"{comment}" - {commenter_name}'
        comments_list.append(new_comment)
        
        # Update the comments field
        df.at[row_index, 'comments'] = str(comments_list)
        
        # Save back to CSV
        df.to_csv(results_file, index=False)
        
        return {
            'success': True,
            'message': f'Comment added successfully by {commenter_name}',
            'comment': new_comment,
            'timestamp': df.iloc[row_index]['timestamp']
        }
        
    except Exception as e:
        return {'error': f'Failed to add comment: {e}'}


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