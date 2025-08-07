import pandas as pd
import matplotlib.pyplot as plt
import sys
import numpy as np
import os
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Set up matplotlib for better looking plots
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (10, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

def add_medal_image(ax, x, y, position, size=0.04):
    """Add a medal image from the images/medals/ folder"""
    try:
        # Map position to medal image filename
        medal_files = {1: "1st.png", 2: "2nd.png", 3: "3rd.png"}
        if position not in medal_files:
            return
        
        # Determine the correct medal path based on where we're running from
        if os.path.exists('web'):
            # Running from root directory (deployment context)
            medal_path = f"web/images/medals/{medal_files[position]}"
        else:
            # Running from code directory (command line context)
            medal_path = f"../web/images/medals/{medal_files[position]}"
        
        # Load and add the medal image
        img = plt.imread(medal_path)
        imagebox = OffsetImage(img, zoom=size)
        ab = AnnotationBbox(imagebox, (x, y), frameon=False)
        ax.add_artist(ab)
        
    except Exception as e:
        print(f"Could not load medal image for position {position}: {e}")
        # Fallback to simple text
        ax.text(x, y, f"{position}", fontsize=12, fontweight='bold', ha='center', va='center', 
                color='#333333', bbox=dict(boxstyle="circle,pad=0.3", facecolor='gold' if position==1 else 'silver' if position==2 else '#CD7F32'))

def add_player_image(ax, x, y, player_name, size=0.06):
    """Add a player image from the images/players/ folder"""
    try:
        # Determine the correct player image path based on where we're running from
        if os.path.exists('web'):
            # Running from root directory (deployment context)
            player_image_path = f"web/images/players/{player_name}.png"
        else:
            # Running from code directory (command line context)
            player_image_path = f"../web/images/players/{player_name}.png"
        
        if os.path.exists(player_image_path):
            # Load and add the player image
            img = plt.imread(player_image_path)
            imagebox = OffsetImage(img, zoom=size)
            ab = AnnotationBbox(imagebox, (x, y), frameon=False)
            ax.add_artist(ab)
        else:
            # If no image exists, add a placeholder circle
            circle = plt.Circle((x, y), size*0.5, facecolor='#CCCCCC', edgecolor='#999999', linewidth=2)
            ax.add_patch(circle)
            ax.text(x, y, "?", fontsize=10, fontweight='bold', ha='center', va='center', color='#666666')
            
    except Exception as e:
        print(f"Could not load player image for {player_name}: {e}")
        # Fallback to placeholder circle
        circle = plt.Circle((x, y), size*0.5, facecolor='#CCCCCC', edgecolor='#999999', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, "?", fontsize=10, fontweight='bold', ha='center', va='center', color='#666666')

def get_current_ratings(game_folder):
    """Get current ratings for all players in a game folder"""
    ratings = {}
    has_played = {}  # Track which players have actually played games
    
    # Construct the full path to the database folder
    # Determine the correct database path based on where we're running from
    if os.path.exists('database'):
        # Running from root directory (deployment context)
        database_path = os.path.join('database', game_folder)
    else:
        # Running from code directory (command line context)
        database_path = os.path.join('..', 'database', game_folder)
    
    if not os.path.exists(database_path):
        print(f"Game folder '{database_path}' does not exist!")
        return ratings, has_played
    
    for filename in os.listdir(database_path):
        if filename.endswith('.csv'):
            player_name = filename.replace('.csv', '')
            file_path = os.path.join(database_path, filename)
            
            try:
                data = pd.read_csv(file_path)
                if not data.empty:
                    current_rating = data['rating'].iloc[-1]  # Get the last rating
                    ratings[player_name] = current_rating
                    
                    # Check if player has played any games (more than just "beginning of time")
                    has_played[player_name] = len(data) > 1
                else:
                    # If file is empty, give them starting rating
                    ratings[player_name] = 1200.0
                    has_played[player_name] = False
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                # If there's an error, give them starting rating
                ratings[player_name] = 1200.0
                has_played[player_name] = False
    
    return ratings, has_played

def create_leaderboard(game_folder, excluded_players=None, title=None):
    """Create a leaderboard visualization"""
    if excluded_players is None:
        excluded_players = []
    
    ratings, has_played = get_current_ratings(game_folder)
    
    if not ratings:
        print(f"No player data found in {game_folder}")
        return
    
    # Filter out excluded players
    filtered_ratings = {player: rating for player, rating in ratings.items() 
                       if player.lower() not in [excluded.lower() for excluded in excluded_players]}
    
    if not filtered_ratings:
        print(f"No players remaining after exclusions in {game_folder}")
        return
    
    # Sort players: first by whether they've played games, then by rating
    # Players who have played games come first, sorted by rating (highest first)
    # Players who haven't played games come last, also sorted by rating (highest first)
    sorted_players = sorted(filtered_ratings.items(), 
                          key=lambda x: (has_played[x[0]], x[1]), 
                          reverse=True)
    
    # Create the plot with a clean, simple design
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Set background to white
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Remove all spines and ticks for a clean look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Set up the layout
    y_positions = list(range(len(sorted_players)))
    y_positions.reverse()  # So #1 is at the top
    
    # Define colors for medals
    medal_colors = ['#FFD700', '#C0C0C0', '#CD7F32']  # Gold, Silver, Bronze
    
    # Draw each player's row
    for i, (player, rating) in enumerate(sorted_players):
        y_pos = y_positions[i]
        
        # Choose color based on position and whether they've played
        if not has_played[player]:
            # New player who hasn't played yet - highlight in green
            color = '#90EE90'  # Light green
        elif i == 0:
            color = medal_colors[0]  # Gold
        elif i == 1:
            color = medal_colors[1]  # Silver
        elif i == 2:
            color = medal_colors[2]  # Bronze
        else:
            color = '#E8E8E8'  # Light gray
        
        # Draw background rectangle for the row
        rect = plt.Rectangle((0, y_pos - 0.4), 1, 0.8, facecolor=color, alpha=0.3, edgecolor='none')
        ax.add_patch(rect)
        
        # Add position number
        ax.text(0.05, y_pos, f"{i+1:2d}.", fontsize=14, fontweight='bold', ha='left', va='center')
        
        # Add medal image for top 3
        if i < 3:
            add_medal_image(ax, 0.25, y_pos, i + 1)
        
        # Add player name
        ax.text(0.35, y_pos, player.capitalize(), fontsize=14, fontweight='bold', ha='left', va='center')
        
        # Add player image (on the right side of the name)
        add_player_image(ax, 0.65, y_pos, player)
        
        # Add rating
        ax.text(0.85, y_pos, f"{int(rating):>4d}", fontsize=14, fontweight='bold', ha='right', va='center')
    
    # Set title
    game_name = game_folder.title()
    ax.set_title(f'{game_name} Leaderboard', fontsize=20, fontweight='bold', pad=30, color='#333333')
    
    # Set axis limits
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, len(sorted_players) - 0.5)
    
    plt.tight_layout()
    
    # Save the leaderboard
    # Determine the correct output path based on where we're running from
    if os.path.exists('web'):
        # Running from root directory (deployment context)
        output_file = f'web/{game_folder}_leaderboard.png'
    else:
        # Running from code directory (command line context)
        output_file = f'../web/{game_folder}_leaderboard.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"Leaderboard saved as {output_file}")
    
    # Also print a text version
    print(f"\n{game_name.upper()} LEADERBOARD:")
    print("=" * 40)
    for i, (player, rating) in enumerate(sorted_players):
        print(f"{i+1:2d}. {player.capitalize():<12} {int(rating):>4d}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 leaderboard.py <game_folder> [--exclude player1] [--exclude player2] ...")
        print("Example: python3 leaderboard.py chess")
        print("Example: python3 leaderboard.py chess --exclude anthony")
        print("Example: python3 leaderboard.py chess --exclude anthony --exclude eve")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    # Parse exclude arguments
    excluded_players = []
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--exclude" and i + 1 < len(sys.argv):
            excluded_players.append(sys.argv[i + 1].lower())
            i += 2
        else:
            i += 1
    
    if excluded_players:
        print(f"Excluding players: {', '.join(excluded_players)}")
    
    create_leaderboard(game_folder, excluded_players) 