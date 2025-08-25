import pandas as pd
import sys
import numpy as np
import datetime
import os
import json
from collections import defaultdict

def get_middle_rating(times, ratings):
    """Get the rating at the middle of the time series"""
    if len(times) == 0:
        return None
    
    # Get the middle index
    middle_index = len(times) // 2
    return times[middle_index], ratings[middle_index]

def bucket_player_data(times, ratings, bucket_boundaries, starting_rating, current_rating):
    """
    Bucket player data into time intervals and compute statistics.
    Returns bucket centers, means, and ranges.
    Ensures the final point shows the actual current rating.
    """
    if not times:
        return [], [], []
    
    bucket_means = []
    bucket_ranges = []
    bucket_centers = []
    
    for i in range(len(bucket_boundaries) - 1):
        start_time = bucket_boundaries[i]
        end_time = bucket_boundaries[i + 1]
        bucket_center = start_time + (end_time - start_time) / 2
        
        # Check if this is the final bucket
        is_final_bucket = (i == len(bucket_boundaries) - 2)
        
        # Collect ratings in this time bucket
        bucket_ratings = []
        for t, r in zip(times, ratings):
            if start_time <= t < end_time:
                bucket_ratings.append(r)
        
        if bucket_ratings:
            if is_final_bucket:
                # For the final bucket, use the actual current rating
                mean_rating = current_rating
                rating_range = 0  # No range for final point - it's a precise rating
            else:
                # For other buckets, use the average
                mean_rating = np.mean(bucket_ratings)
                rating_range = np.max(bucket_ratings) - np.min(bucket_ratings)
        else:
            # Use previous bucket's mean or starting rating
            if bucket_means:
                if is_final_bucket:
                    # For final bucket with no data, use current rating
                    mean_rating = current_rating
                    rating_range = 0  # No range for final point
                else:
                    mean_rating = bucket_means[-1]
                    rating_range = 0
            else:
                mean_rating = starting_rating
                rating_range = 0
        
        bucket_centers.append(bucket_center)
        bucket_means.append(mean_rating)
        bucket_ranges.append(rating_range)
    
    return bucket_centers, bucket_means, bucket_ranges

def plot_rating(filepath, label):
    """Load and return rating data from a CSV file"""
    try:
        data = pd.read_csv(filepath)
        
        # Get current rating from the entire CSV file (last row)
        current_rating = float(data['rating'].iloc[-1]) if not data.empty else 1200
        
        # Skip initial entry and entries without opponents
        mask = (data['opponent'] != 'no opponent') & (data['opponent'].notna())
        game_data = data[mask]
        
        if game_data.empty:
            return [], [], label, 1200, current_rating
        
        times = []
        ratings = game_data['rating'].values
        
        # Convert timestamp strings to datetime objects
        for timestamp_str in game_data['timestamp']:
            if timestamp_str == 'beginning of time':
                continue
            try:
                # Try different timestamp formats
                if '.' in timestamp_str:
                    # Format with microseconds: 2023-12-07 14:30:25.123456
                    dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    # Format without microseconds: 2023-12-07 14:30:25
                    dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                times.append(dt)
            except ValueError as e:
                print(f"Warning: Could not parse timestamp '{timestamp_str}': {e}")
                continue
        
        # Ensure times and ratings have same length
        min_length = min(len(times), len(ratings))
        times = times[:min_length]
        ratings = ratings[:min_length]
        
        # Get starting rating (from first row, before games)
        starting_rating = data['rating'].iloc[0] if not data.empty else 1200
        
        return times, ratings, label, starting_rating, current_rating
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return [], [], label, 1200, 1200

def create_ratings_progress_json(csv_files):
    """Create ratings progress data in JSON format for Plotly.js"""
    
    # Collect all data first
    all_times = []
    all_ratings = []
    player_data = {}
    
    # Process each CSV file
    for csv_file in csv_files:
        times, ratings, player_name, starting_rating, current_rating = plot_rating(csv_file, csv_file)
        if times:  # Only include players with game data
            all_times.extend(times)
            all_ratings.extend(ratings)
            player_data[player_name] = (times, ratings, starting_rating, current_rating)
    
    if not all_times:
        return {"error": "No valid game data found"}
    
    # Determine game and team info from first CSV file
    first_arg = csv_files[0]
    team_name = None
    if '/database/' in first_arg:
        parts = first_arg.split('/database/')[1].split('/')
        if len(parts) >= 2 and parts[0] not in ['chess', 'pingpong', 'backgammon']:
            team_name = parts[0]
            game_type = parts[1].title()
        else:
            game_type = parts[0].title()
    elif 'database' in first_arg:
        path_parts = first_arg.split('/')
        if len(path_parts) >= 3 and path_parts[1] not in ['chess', 'pingpong', 'backgammon']:
            team_name = path_parts[1]
            game_type = path_parts[2].title()
        elif len(path_parts) >= 2:
            game_type = path_parts[1].title()
        else:
            game_type = "Unknown"
    else:
        game_type = first_arg.split('/')[0].title()
    
    # Calculate time boundaries and total games
    first_game_time = min(all_times)
    last_game_time = max(all_times)
    total_games = len(all_times) // 2  # Each game involves 2 players
    
    # Create time buckets for smoothing
    num_buckets = min(20, max(5, total_games // 3))
    time_delta = (last_game_time - first_game_time) / num_buckets
    bucket_boundaries = []
    for i in range(num_buckets + 1):
        bucket_boundaries.append(first_game_time + i * time_delta)
    
    # Define colors for chart visualization
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # Process each player's data
    players_series = []
    player_index = 0
    
    for label, (times, ratings, starting_rating, current_rating) in player_data.items():
        if times:  # Player has games
            # Bucket the player's data
            bucket_centers, bucket_means, bucket_ranges = bucket_player_data(
                times, ratings, bucket_boundaries, starting_rating, current_rating
            )
            
            if bucket_centers:
                color = colors[player_index % len(colors)]
                
                # Format player name
                player_name = label.split('/')[-1] if '/' in label else label
                display_name = player_name.replace('_', ' ').title()
                display_name = display_name.replace(' Q', ' (-♛)')
                
                # Check if player is inactive
                is_inactive = times[-1] != last_game_time
                
                # Convert times to ISO strings for JSON serialization
                x_data = [t.isoformat() for t in bucket_centers]
                y_data = [int(rating) for rating in bucket_means]  # Floor round all chart data
                range_data = [int(r) for r in bucket_ranges]  # Floor round range data
                
                # Use the actual current rating from the CSV file
                # current_rating is already passed from plot_rating function
                
                players_series.append({
                    'name': display_name,
                    'player': player_name,
                    'x': x_data,
                    'y': y_data,
                    'ranges': range_data,
                    'color': color,
                    'current_rating': int(current_rating),
                    'starting_rating': int(starting_rating),  # Floor round starting rating
                    'games_played': len(times),
                    'is_inactive': is_inactive
                })
                
                player_index += 1
    
    return {
        'title': f'{game_type} Ratings Progress',
        'game': game_type.lower(),
        'team': team_name,
        'players': players_series,
        'total_players': len(players_series),
        'total_games': total_games,
        'time_range': {
            'start': first_game_time.isoformat(),
            'end': last_game_time.isoformat()
        }
    }

if __name__ == "__main__":
    # Check for JSON and stdout modes
    json_mode = '--json' in sys.argv
    stdout_mode = '--stdout' in sys.argv
    
    # Remove flags from arguments for processing
    csv_files = [arg for arg in sys.argv[1:] if arg not in ['--json', '--stdout']]
    
    if not csv_files:
        print("Usage: python3 graph.py <player1.csv> [player2.csv] ... [--json] [--stdout]")
        print("Example: python3 graph.py ../database/chess/magnus_carlsen.csv ../database/chess/bobby_fischer.csv --json")
        print("Example: python3 graph.py ../database/chess/magnus_carlsen.csv --json --stdout")
        sys.exit(1)
    
    # Generate JSON data
    data = create_ratings_progress_json(csv_files)
    
    if stdout_mode:
        # Output JSON to stdout for programmatic use
        print(json.dumps(data, indent=2))
    else:
        # File output (existing behavior)
        # Determine game type from first CSV for file naming
        first_csv = csv_files[0]
        if 'chess' in first_csv:
            game_type = 'chess'
        elif 'pingpong' in first_csv:
            game_type = 'pingpong'
        elif 'backgammon' in first_csv:
            game_type = 'backgammon'
        else:
            game_type = 'game'
        
        # Determine output path and team info
        team_info = None
        if '/database/' in first_csv:
            parts = first_csv.split('/database/')[1].split('/')
            if len(parts) >= 2 and parts[0] not in ['chess', 'pingpong', 'backgammon']:
                team_info = parts[0]
        elif 'database' in first_csv:
            path_parts = first_csv.split('/')
            if len(path_parts) >= 3 and path_parts[1] not in ['chess', 'pingpong', 'backgammon']:
                team_info = path_parts[1]
        
        # Generate output filename
        if team_info:
            if os.path.exists('web'):
                os.makedirs(f'web/{team_info}', exist_ok=True)
                output_file = f'web/{team_info}/{game_type}_ratings_progress.json'
            else:
                os.makedirs(f'../web/{team_info}', exist_ok=True)
                output_file = f'../web/{team_info}/{game_type}_ratings_progress.json'
        else:
            if os.path.exists('web'):
                output_file = f'web/{game_type}_ratings_progress.json'
            else:
                output_file = f'../web/{game_type}_ratings_progress.json'
        
        # Write JSON output
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Ratings progress JSON saved as {output_file}", file=sys.stderr)
        
        # Print summary
        if "error" not in data:
            print(f"\n{data['title']}:", file=sys.stderr)
            print("=" * 40, file=sys.stderr)
            for player_data in data['players']:
                name = player_data['name']
                current_rating = int(player_data['current_rating'])
                games_played = player_data['games_played']
                print(f"{name:<20} {current_rating:>4d} ({games_played} games)", file=sys.stderr)