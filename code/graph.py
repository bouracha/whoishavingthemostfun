import pandas as pd
import matplotlib.pyplot as plt
import sys
import numpy as np
import datetime

# Set up matplotlib for better looking plots
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

def get_middle_rating(times, ratings):
    """Get the rating at the middle of the time series"""
    if len(times) == 0:
        return None
    
    # Get the middle index
    middle_index = len(times) // 2
    return times[middle_index], ratings[middle_index]

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
    
    # Determine game type from the first argument
    game_type = sys.argv[1].split('/')[0].title()
    
    # Count total games across all players
    total_games = 0
    for player, (times, ratings, starting_rating) in player_data.items():
        # Subtract 1 from each player's game count to exclude the "beginning of time" entry
        total_games += max(0, len(times) - 1)
    
    plt.xlabel("Time")
    plt.title(f"{game_type} ({total_games} total games)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    
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
    
    # Plot active players first
    player_index = 0
    for i, (label, (times, ratings, starting_rating)) in enumerate(player_data.items()):
        if times:  # Player has games
            color = colors[i % len(colors)]
            
            # Check if this player was in the first game
            was_in_first_game = times[0] == first_game_time
            
            if was_in_first_game:
                # Player was in the first game - add their starting rating at first game time
                times_with_start = [first_game_time] + times
                ratings_with_start = [starting_rating] + ratings
            else:
                # Player wasn't in the first game - add a starting point at first game time
                # This creates a flat line from first game time to their first actual game
                times_with_start = [first_game_time] + times
                ratings_with_start = [starting_rating] + ratings
            
            # Add ending point at last game time if player's last game wasn't the most recent
            if times_with_start[-1] != last_game_time:
                # Extend to the most recent time with their current rating
                times_with_end = times_with_start + [last_game_time]
                ratings_with_end = ratings_with_start + [ratings_with_start[-1]]  # Current rating
            else:
                times_with_end = times_with_start
                ratings_with_end = ratings_with_start
            
            # Check if this player has been inactive (no recent games)
            is_inactive = times_with_start[-1] != last_game_time
            
            # Convert to matplotlib dates
            mpl_times = [mdates.date2num(t) for t in times_with_end]
            # Extract just the player name from the label (remove path) and capitalize
            player_name = label.split('/')[-1] if '/' in label else label
            player_name = player_name.capitalize()
            
            # Plot the line first (make inactive players more transparent)
            alpha = 0.7 if is_inactive else 1.0
            plt.plot(mpl_times, ratings_with_end, '-', color=color, linewidth=2.5, alpha=alpha)
            
                        # Plot dots at all key points (start, each game, end)
            plt.plot(mpl_times, ratings_with_end, 'o', color=color, markersize=8, markerfacecolor=color, markeredgecolor='white', markeredgewidth=2, alpha=alpha)
            
            # Add player name at the middle of their line
            if len(mpl_times) > 0:
                middle_x, middle_y = get_middle_rating(mpl_times, ratings_with_end)
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
                data = pd.read_csv(f"../database/chess/{player}.csv")
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
                # Find position for the name based on player index
                best_x, best_y = find_name_position(mpl_times, ratings_flat, player_index, total_players, mdates.date2num(time_center))
                if best_x is not None:
                    # Place text above the line with vertical offset
                    plt.annotate(player.capitalize(), xy=(best_x, best_y), xytext=(5, 15), 
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

# Save with high quality in web folder with game name
plt.savefig(f'../web/{game_type.lower()}_ratings_progress.png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()  # Close the figure to free memory