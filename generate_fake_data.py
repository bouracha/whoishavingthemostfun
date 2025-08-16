#!/usr/bin/env python3
"""
Generate fake game results for famous chess players across chess, pingpong, and backgammon.
This populates the default/homepage database (not team-specific).
"""

import random
import sys
import os
import subprocess
from datetime import datetime, timedelta

# Add the code directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))
from update import make_new_player, read_ratings, update, submit_game_with_charts, write_new_rating, log_result_to_team, get_adjusted_k_factor
from config import get_k_factor

# Famous chess players to use across all games
FAMOUS_PLAYERS = [
    'magnus_carlsen',
    'bobby_fischer', 
    'garry_kasparov',
    'jose_capablanca',
    'anatoly_karpov',
    'vladimir_kramnik',
    'viswanathan_anand',
    'mikhail_tal',
    'boris_spassky',
    'paul_morphy',
    'alexander_alekhine',
    'emanuel_lasker',
    'wilhelm_steinitz',
    'mikhail_botvinnik',
    'tigran_petrosian'
]

GAMES = ['chess', 'pingpong', 'backgammon']

def reset_homepage_results_and_players():
    """Delete all homepage results.csv and existing players for all games."""
    base_db = os.path.join(os.path.dirname(__file__), 'database')
    # Remove homepage results.csv
    results_path = os.path.join(base_db, 'results.csv')
    if os.path.exists(results_path):
        os.remove(results_path)
    # Remove all players' CSVs per game
    for game in GAMES:
        game_dir = os.path.join(base_db, game)
        if os.path.exists(game_dir):
            for fn in os.listdir(game_dir):
                if fn.endswith('.csv'):
                    os.remove(os.path.join(game_dir, fn))

PEAK_CHESS = {
    'magnus_carlsen': 2882,
    'garry_kasparov': 2851,
    'bobby_fischer': 2785,
    'viswanathan_anand': 2817,
    'vladimir_kramnik': 2811,
    'anatoly_karpov': 2780,
    'mikhail_tal': 2706,
    'mikhail_botvinnik': 2720,  # historical estimates
    'jose_capablanca': 2725,     # historical estimates
    'alexander_alekhine': 2730,  # historical estimates
    'tigran_petrosian': 2706,
    'boris_spassky': 2706,
    'emanuel_lasker': 2780,      # historical estimates
    'paul_morphy': 2690,         # historical estimates
    'wilhelm_steinitz': 2750,    # historical estimates
}

def create_players_for_all_games():
    """Create all players for all games with specified starting ratings."""
    print("Creating players for all games...")

    for game in GAMES:
        print(f"\n📋 Creating players for {game}:")
        for player in FAMOUS_PLAYERS:
            try:
                if game == 'chess':
                    starting = float(PEAK_CHESS.get(player, 2400))
                else:
                    starting = random.uniform(700, 2200)
                make_new_player(player, game, starting_rating=starting)
                print(f"  ✅ {player} ({int(starting)})")
            except Exception as e:
                print(f"  ❌ {player}: {e}")

def generate_realistic_matchups(players, num_games):
    """Generate realistic matchups with some players being more active than others"""
    matchups = []
    
    # Create weighted player list (top players play more often)
    weighted_players = []
    for i, player in enumerate(players):
        # Earlier players in the list (Magnus, Bobby, etc.) get more weight
        weight = len(players) - i
        weighted_players.extend([player] * weight)
    
    for _ in range(num_games):
        # Pick two different players
        player1 = random.choice(weighted_players)
        player2 = random.choice(weighted_players)
        
        # Ensure they're different
        attempts = 0
        while player1 == player2 and attempts < 10:
            player2 = random.choice(weighted_players)
            attempts += 1
        
        if player1 != player2:
            matchups.append((player1, player2))
    
    return matchups

def generate_realistic_result(player1, player2):
    """Generate a realistic result based on player 'strength' (position in famous players list)"""
    # Get player indices (earlier = stronger)
    try:
        idx1 = FAMOUS_PLAYERS.index(player1)
        idx2 = FAMOUS_PLAYERS.index(player2)
    except ValueError:
        # If player not in list, random result
        return random.choice([1.0, 0.5, 0.0])
    
    # Calculate strength difference (lower index = stronger)
    strength_diff = idx2 - idx1  # positive if player1 is stronger
    
    # Convert to probability (stronger player has higher win chance)
    base_prob = 0.5
    strength_factor = strength_diff * 0.03  # 3% per position difference
    win_prob = base_prob + strength_factor
    
    # Clamp between 0.1 and 0.9
    win_prob = max(0.1, min(0.9, win_prob))
    
    # Generate result based on probability
    rand = random.random()
    if rand < win_prob:
        return 1.0  # Player 1 wins
    elif rand < win_prob + 0.15:  # 15% draw chance
        return 0.5  # Draw
    else:
        return 0.0  # Player 2 wins

def simulate_games_for_game_type(game_type: str, total_games: int = 100):
    """Simulate games using backend probability from current ratings.
    - Generate total_games timestamps over the last year
    - For each timestamp in chronological order, simulate a game between two random players
      and decide the result using the Elo win probability from current ratings.
    """
    print(f"\n🎮 Simulating {total_games} games for {game_type}...")

    # Prepare timestamps
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)

    # Build a global list of planned timestamps (total_games total)
    all_stamps = []
    for _ in range(total_games):
        timestamp = one_year_ago + timedelta(seconds=random.random() * (now - one_year_ago).total_seconds())
        all_stamps.append(timestamp)
    # Sort all timestamps
    all_stamps.sort()

    # For each timestamp, pick two distinct players and simulate a game based on current ratings
    for i, ts in enumerate(all_stamps, 1):
        p1, p2 = random.sample(FAMOUS_PLAYERS, 2)

        # Read current ratings
        r1_arr, r2_arr = read_ratings(p1, p2, game_type)
        r1, r2 = r1_arr[-1], r2_arr[-1]

        # Use backend update() probability (we only need prob of p1 winning)
        # Call update with score=1.0 to compute prob based on current ratings; ignore new ratings
        _, _, p1_win_prob = update(r1, r2, score=1.0)

        # Decide outcome
        rnd = random.random()
        if rnd < p1_win_prob:
            score = 1.0
            opp_score = 0.0
        elif rnd < p1_win_prob + 0.10:  # 10% draw chance
            score = 0.5
            opp_score = 0.5
        else:
            score = 0.0
            opp_score = 1.0

        # Use the backend function that replicates the Flask API behavior
        # Format timestamp to match manual entries (with microseconds) - spread over past year
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S.%f')
        result_str = "1-0" if score == 1.0 else ("1/2-1/2" if score == 0.5 else "0-1")
        
        # Use the backend functions directly for efficiency (no chart generation per game)
        # Read current ratings and calculate new ones
        ratings1, ratings2 = read_ratings(p1, p2, game_type)
        rating1, rating2 = ratings1[-1], ratings2[-1]
        
        # Get adjusted K-factors for each player
        k_factor1 = get_adjusted_k_factor(p1, game_type)
        k_factor2 = get_adjusted_k_factor(p2, game_type)
        
        # Calculate expected score and probability
        rating_diff = rating1 - rating2
        probability = 1.0 / (1.0 + (10 ** (rating_diff / 400)))
        
        # Calculate rating changes using individual K-factors
        # Player 1's rating change
        expected_score1 = probability
        actual_score1 = score
        rating_change1 = (actual_score1 - expected_score1) * k_factor1
        
        # Player 2's rating change (opposite direction)
        expected_score2 = 1 - probability
        actual_score2 = 1 - score
        rating_change2 = (actual_score2 - expected_score2) * k_factor2
        
        # Apply the changes
        new_rating1 = rating1 + rating_change1
        new_rating2 = rating2 + rating_change2
        
        # Write new ratings with properly formatted timestamp (spread over past year)
        write_new_rating(p1, new_rating1, p2, score, game_type, colour='white', timestamp=ts_str)
        write_new_rating(p2, new_rating2, p1, (1-score), game_type, colour='black', timestamp=ts_str)
        
        # Log result to recent results (with properly formatted timestamp)
        log_result_to_team(p1, p2, result_str, game_type, None, probability, timestamp=ts_str)
        
        # Mock response for consistency
        response = {
            'success': True,
            'player1': p1,
            'player2': p2, 
            'result': result_str
        }
        
        if not response.get('success'):
            print(f"    ❌ Game submission failed for game {i}: {response.get('error')}")
            continue

        # Print meaningful progress info
        p1_display = p1.replace('_', ' ').title()
        p2_display = p2.replace('_', ' ').title()
        
        if i % 10 == 0 or i <= 5:  # Show first 5 and every 10th game
            print(f"  Game {i:3d}: {p1_display} vs {p2_display} ({result_str}) - {game_type}")
        elif i % 25 == 0:
            print(f"  Progress: {i}/{len(all_stamps)} games completed for {game_type}")

def generate_charts_for_all_games():
    """Generate leaderboards and rating charts for all games"""
    print("\n📊 Generating charts for all games...")
    
    original_cwd = os.getcwd()
    code_dir = os.path.join(os.path.dirname(__file__), 'code')
    os.chdir(code_dir)
    
    try:
        for game in GAMES:
            print(f"\n  📈 Generating charts for {game}...")
            
            # Generate leaderboard
            try:
                subprocess.run([
                    sys.executable, 'leaderboard.py', game
                ], check=True, capture_output=True, text=True)
                print(f"    ✅ Leaderboard generated")
            except subprocess.CalledProcessError as e:
                print(f"    ❌ Leaderboard failed: {e.stderr}")
            
            # Generate ratings progress chart
            try:
                # Find all CSV files for this game
                import glob
                csv_files = glob.glob(f"../database/{game}/*.csv")
                
                if csv_files:
                    subprocess.run([
                        sys.executable, 'graph.py'
                    ] + csv_files, check=True, capture_output=True, text=True)
                    print(f"    ✅ Ratings progress generated")
                else:
                    print(f"    ⚠️  No CSV files found for {game}")
                    
            except subprocess.CalledProcessError as e:
                print(f"    ❌ Ratings progress failed: {e.stderr}")
    
    finally:
        os.chdir(original_cwd)

def main():
    print("🏆 Generating Fake Chess Legends Data")
    print("=" * 50)
    
    # Set random seed for reproducible results (comment out for true randomness)
    random.seed(42)
    
    try:
        # Step 1: Reset homepage results and players
        reset_homepage_results_and_players()
        # Step 2: Create all players with specified starting ratings
        create_players_for_all_games()
        
        # Step 3: Simulate 100 total games per game type over last year
        for game in GAMES:
            simulate_games_for_game_type(game, total_games=100)
        
        # Step 4: Final chart generation to ensure everything is up-to-date
        generate_charts_for_all_games()
        
        print("\n" + "=" * 50)
        print("🎉 Fake data generation completed!")
        print("\nYou can now:")
        print("1. Visit http://localhost:8080 to see the populated homepage")
        print("2. Check individual game pages: /chess, /pingpong, /backgammon")
        print("3. View the generated leaderboards and rating progressions")
        print("\nFamous players included:")
        for i, player in enumerate(FAMOUS_PLAYERS, 1):
            print(f"  {i:2d}. {player.replace('_', ' ').title()}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        raise

if __name__ == "__main__":
    main()
