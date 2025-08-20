import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to reduce memory usage
import matplotlib.pyplot as plt
import sys
import numpy as np
import datetime
import os
from collections import defaultdict

# Set up matplotlib for better looking plots
try:
    plt.style.use('seaborn-v0_8')
except:
    plt.style.use('default')  # Fallback for older matplotlib versions
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['figure.dpi'] = 150  # Balanced DPI for good quality and reasonable file size
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = [
    'DejaVu Sans',
    'Arial Unicode MS',
    'Symbola',
    'FreeSerif',
    'Noto Sans Symbols'
]

def get_middle_rating(times, ratings):
    """Get the rating at the middle of the time series"""
    if len(times) == 0:
        return None
    
    # Get the middle index
    middle_index = len(times) // 2
    return times[middle_index], ratings[middle_index]

def bucket_player_data(times, ratings, bucket_boundaries, starting_rating):
    """
    Bucket player data into time intervals and compute statistics.
    Returns bucket centers, means, and standard deviations.
    """
    if not times:
        return [], [], []
    
    bucket_means = []
    bucket_stds = []
    bucket_centers = []
    
    # Initialize the last known rating as the starting rating
    last_known_rating = starting_rating
    
    for i in range(len(bucket_boundaries) - 1):
        bucket_start = bucket_boundaries[i]
        bucket_end = bucket_boundaries[i + 1]
        bucket_center = bucket_start + (bucket_end - bucket_start) / 2
        
        # Find all ratings in this bucket
        bucket_ratings = []
        for j, t in enumerate(times):
            if bucket_start <= t < bucket_end:
                bucket_ratings.append(ratings[j])
                last_known_rating = ratings[j]  # Update last known rating
        
        # If we have data in this bucket, use it
        if bucket_ratings:
            bucket_means.append(np.mean(bucket_ratings))
            bucket_stds.append(np.std(bucket_ratings) if len(bucket_ratings) > 1 else 0)
            bucket_centers.append(bucket_center)
        # Otherwise, use the last known rating (forward fill)
        else:
            # Only add a point if we've seen at least one game
            if last_known_rating is not None and times[0] <= bucket_end:
                bucket_means.append(last_known_rating)
                bucket_stds.append(0)  # No variance if no games in bucket
                bucket_centers.append(bucket_center)
    
    return bucket_centers, bucket_means, bucket_stds



name = sys.argv[0]



def plot_rating(path_to_file, label):
  data = pd.read_csv(path_to_file)

  rating = np.array(data['rating'])
  timestamp = np.array(data['timestamp'])
  print(label, rating[-1])

  time_list = []
  valid_ratings = []
  starting_rating = None
  
  for i, ts in enumerate(timestamp):
    if ts == "beginning of time":
      # Store the starting rating but don't add to timeline yet
      starting_rating = rating[i]
      continue
    else:
      try:
        date = datetime.datetime.strptime(ts[:-7], "%Y-%m-%d %H:%M:%S")
        # Store the full datetime object for flexible scaling
        time_list.append(date)
        valid_ratings.append(rating[i])
      except ValueError:
        # Skip invalid timestamps
        continue

  if time_list:  # Only plot if we have valid data
    return time_list, valid_ratings, label[:-4], starting_rating
  else:
    return [], [], label[:-4], starting_rating


# Collect all data first
all_times = []
all_ratings = []
all_labels = []
player_data = {}  # Store each player's data separately

print("Number of datasets: ", len(sys.argv)-1)
for i in range(1, len(sys.argv)):
  dataset = sys.argv[i]
  times, ratings, label, starting_rating = plot_rating(dataset, dataset)
  all_times.extend(times)
  all_ratings.extend(ratings)
  all_labels.extend([label] * len(times))
  player_data[label] = (times, ratings, starting_rating)

# Determine game and optional team from the first argument
first_arg = sys.argv[1]
team_name = None
if '/database/' in first_arg:
    parts = first_arg.split('/database/')[1].split('/')
    if len(parts) >= 2 and parts[0] not in ['chess', 'pingpong', 'backgammon']:
        # Expect path like team/game/player.csv
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
    # Fallback
    game_type = first_arg.split('/')[0].title()



# Plot all data
if all_times:
    # Convert to matplotlib dates
    import matplotlib.dates as mdates
    
    # Find the very first game time across all players
    first_game_time = min(all_times)
    last_game_time = max(all_times)
    
    # Calculate the center of the time axis
    time_center = first_game_time + (last_game_time - first_game_time) / 2
    
    # Determine time scale automatically
    time_span = last_game_time - first_game_time
    
    # Count total games across all players
    total_games = 0
    for player, (times, ratings, starting_rating) in player_data.items():
        # The times list already excludes "beginning of time", so count all timestamps
        total_games += len(times)
    
    # Since each game involves 2 players, divide by 2 to get actual number of games
    total_games = total_games // 2
    
    # Create time buckets (approximately 20 buckets, but ensure at least 5)
    num_buckets = min(20, max(5, total_games // 3))
    
    # Create bucket boundaries
    time_delta = (last_game_time - first_game_time) / num_buckets
    bucket_boundaries = []
    for i in range(num_buckets + 1):
        bucket_boundaries.append(first_game_time + i * time_delta)
    
    plt.xlabel("Date")
    plt.title(f"{game_type} ({total_games} total games)")
    
    # Smart x-axis formatting based on time span
    ax = plt.gca()
    if time_span.days <= 7:
        # Less than a week: show day and time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    elif time_span.days <= 30:
        # Less than a month: show day and month
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, time_span.days // 10)))
    elif time_span.days <= 365:
        # Less than a year: show month and day
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator(bymonthday=[1, 15]))
    else:
        # More than a year: show year and month
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, time_span.days // 365)))
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Define a nice color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # Plot each player's data, starting from the first game time
    last_game_time = max(all_times)
    
    # Get all player names from command line arguments
    all_requested_players = []
    for arg in sys.argv[1:]:
        player_name = arg.split('/')[-1].replace('.csv', '')
        all_requested_players.append(player_name)
    
    # Count total players for name positioning
    total_players = len(player_data) + sum(1 for player in all_requested_players 
                                         if player not in player_data or not player_data[player][0])
    
    # Setting for whether to show standard deviation (can be adjusted)
    show_std_dev = True  # Set to False to disable error bars
    
    # Plot active players first
    player_index = 0
    for i, (label, (times, ratings, starting_rating)) in enumerate(player_data.items()):
        if times:  # Player has games
            color = colors[i % len(colors)]
            
            # Bucket the player's data
            bucket_centers, bucket_means, bucket_stds = bucket_player_data(
                times, ratings, bucket_boundaries, starting_rating
            )
            
            if bucket_centers:  # Only plot if we have bucketed data
                # Check if this player has been inactive (no recent games)
                is_inactive = times[-1] != last_game_time
                
                # Convert bucket centers to matplotlib dates
                mpl_times = [mdates.date2num(t) for t in bucket_centers]
                
                # Get the exact current rating and time
                current_rating = ratings[-1]  # Last actual rating
                current_time = mdates.date2num(last_game_time)  # Use global last game time
                
                # Extract just the player name from the label (remove path) and format properly
                player_name = label.split('/')[-1] if '/' in label else label
                player_name = player_name.replace('_', ' ').title()
                # Replace any " Q" with " (-♛)" (space + Q becomes space + brackets + queen)
                player_name = player_name.replace(' Q', ' (-♛)')
                
                # Plot the line first (make inactive players more transparent)
                alpha = 0.7 if is_inactive else 1.0
                plt.plot(mpl_times, bucket_means, '-', color=color, linewidth=2.5, alpha=alpha)
                
                # Plot error bars for standard deviation if enabled and we have variance
                if show_std_dev and any(std > 0 for std in bucket_stds):
                    # Only show error bars where std > 0
                    error_times = []
                    error_means = []
                    error_stds = []
                    for j, std in enumerate(bucket_stds):
                        if std > 0:
                            error_times.append(mpl_times[j])
                            error_means.append(bucket_means[j])
                            error_stds.append(std)
                    
                    if error_times:
                        plt.errorbar(error_times, error_means, yerr=error_stds, 
                                   fmt='none', color=color, alpha=alpha * 0.3, 
                                   capsize=3, capthick=1)
                
                # Plot dots at bucket centers (smaller for historical points)
                plt.plot(mpl_times, bucket_means, 'o', color=color, markersize=5, 
                        markerfacecolor=color, markeredgecolor='white', 
                        markeredgewidth=1.5, alpha=alpha)
                
                # Add exact current rating point (larger marker to emphasize)
                plt.plot(current_time, current_rating, 'o', color=color, markersize=8, 
                        markerfacecolor=color, markeredgecolor='white', 
                        markeredgewidth=2, alpha=alpha, zorder=10)
                
                # Connect last bucket to current rating if they're different
                if mpl_times and abs(mpl_times[-1] - current_time) > 0.1:  # Different times
                    plt.plot([mpl_times[-1], current_time], [bucket_means[-1], current_rating], 
                            '-', color=color, linewidth=2.5, alpha=alpha)
                
                # Add player name at the middle of their line
                if len(mpl_times) > 0:
                    middle_x, middle_y = get_middle_rating(mpl_times, bucket_means)
                    if middle_x is not None:
                        # Place text above the line
                        plt.annotate(player_name, xy=(middle_x, middle_y), xytext=(5, 15), 
                                    textcoords='offset points', fontsize=20, fontweight='bold',
                                    color=color, alpha=alpha, ha='left', va='bottom')
    
    # Plot inactive players (only those who have no games at all)
    inactive_count = 0
    for player in all_requested_players:
        # Check if this player has any games by looking for their data in player_data
        player_has_games = False
        for label in player_data.keys():
            if player in label:  # Check if player name is in the label
                player_has_games = True
                break
        
        if not player_has_games:  # Only plot if player has no games
            # Get their last rating from the CSV file
            try:
                # Determine base database directory depending on runtime
                base_db = 'database' if os.path.exists('database') else '../database'
                # Use detected game and optional team
                if team_name:
                    player_csv = f"{base_db}/{team_name}/{game_type.lower()}/{player}.csv"
                else:
                    player_csv = f"{base_db}/{game_type.lower()}/{player}.csv"
                data = pd.read_csv(player_csv)
                last_rating = data['rating'].iloc[-1]  # Get the last rating entry
            except:
                last_rating = 1200.0  # Default if file doesn't exist or is empty
            
            # Create flat line from first game time to last game time at their last rating
            times_flat = [first_game_time, last_game_time]
            ratings_flat = [last_rating, last_rating]
            
            # Convert to matplotlib dates
            mpl_times = [mdates.date2num(t) for t in times_flat]
            color = colors[(len(player_data) + inactive_count) % len(colors)]
            
            # Plot the dashed line first
            plt.plot(mpl_times, ratings_flat, '--', color=color, linewidth=2, alpha=0.7)
            
            # Plot dots at start and end points
            plt.plot(mpl_times, ratings_flat, 'o', color=color, markersize=6, markerfacecolor=color, markeredgecolor='white', markeredgewidth=1.5, alpha=0.7)
            
            # Add player name at a smart position along the line
            if len(mpl_times) > 0:
                # Place text roughly at the center
                mid_index = len(mpl_times)//2
                best_x, best_y = mpl_times[mid_index], ratings_flat[mid_index]
                display_name = player.replace('_', ' ').title()
                # Replace any " Q" with " (-♛)" (space + Q becomes space + brackets + queen)
                display_name = display_name.replace(' Q', ' (-♛)')
                plt.annotate(display_name, xy=(best_x, best_y), xytext=(5, 15), 
                           textcoords='offset points', fontsize=20, fontweight='bold',
                           color=color, alpha=0.7, ha='left', va='bottom')
                player_index += 1
            inactive_count += 1

plt.ylabel("Rating", fontsize=14, fontweight='bold')
# Get the current xlabel text and apply styling
current_xlabel = plt.gca().get_xlabel()
plt.xlabel(current_xlabel, fontsize=14, fontweight='bold')
# Get the current title text and apply styling
current_title = plt.gca().get_title()
plt.title(current_title, fontsize=16, fontweight='bold', pad=20)

# No legend needed since names are on the lines

# Add some padding and improve layout
plt.tight_layout()

# Save with high quality in web folder with game name, optionally under team directory
# Determine the correct output path based on where we're running from
game_file = f'{game_type.lower()}_ratings_progress.png'
if os.path.exists('web'):
    if team_name:
        os.makedirs(f'web/{team_name}', exist_ok=True)
        output_file = f'web/{team_name}/{game_file}'
    else:
        output_file = f'web/{game_file}'
else:
    if team_name:
        os.makedirs(f'../web/{team_name}', exist_ok=True)
        output_file = f'../web/{team_name}/{game_file}'
    else:
        output_file = f'../web/{game_file}'

    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()  # Close the figure to free memory