"""
Test data fixtures and helper functions for creating test scenarios.
"""

import os
import tempfile
import shutil
import pandas as pd
from datetime import datetime, timedelta


class TestDataManager:
    """Manages test data creation and cleanup."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def create_temp_database(self):
        """Create a temporary database directory with sample data."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        # Create game directories
        for game in ['chess', 'pingpong', 'backgammon']:
            game_dir = os.path.join(temp_dir, game)
            os.makedirs(game_dir, exist_ok=True)
        
        return temp_dir
    
    def create_sample_player(self, database_dir, game, player_name, num_games=5):
        """Create a sample player CSV file with realistic data."""
        game_dir = os.path.join(database_dir, game)
        player_file = os.path.join(game_dir, f"{player_name}.csv")
        
        # Generate sample game data
        data = []
        current_rating = 1200
        current_date = datetime.now() - timedelta(days=num_games)
        
        # Initial rating
        data.append([current_rating, 'initial', 1.0, 'white', current_date])
        
        # Generate games with random outcomes
        opponents = ['alice', 'bob', 'charlie', 'diana', 'eve']
        for i in range(num_games):
            current_date += timedelta(days=1)
            opponent = opponents[i % len(opponents)]
            
            # Simulate win/loss (60% win rate for variety)
            result = 1.0 if i % 5 < 3 else 0.0
            
            # Simple rating change simulation
            if result == 1.0:
                current_rating += 15 + (i * 2)
            else:
                current_rating -= 10 + (i * 1)
            
            data.append([current_rating, opponent, result, 'white', current_date])
        
        # Save to CSV
        df = pd.DataFrame(data, columns=['rating', 'opponent', 'result', 'color', 'date'])
        df.to_csv(player_file, index=False)
        
        return player_file
    
    def cleanup(self):
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs = []


# Sample test scenarios
TEST_SCENARIOS = {
    'equal_ratings': {
        'player1_rating': 1500,
        'player2_rating': 1500,
        'expected_change': 20,  # With K=40
        'description': 'Equal ratings should result in 20 point swing'
    },
    'upset_victory': {
        'player1_rating': 1200,  # Lower rated player
        'player2_rating': 1600,  # Higher rated player
        'result': 1.0,  # Player 1 wins (upset)
        'description': 'Lower rated player beating higher rated should give large rating gain'
    },
    'expected_victory': {
        'player1_rating': 1600,  # Higher rated player
        'player2_rating': 1200,  # Lower rated player  
        'result': 1.0,  # Player 1 wins (expected)
        'description': 'Higher rated player beating lower rated should give small rating gain'
    },
    'draw_scenario': {
        'player1_rating': 1500,
        'player2_rating': 1500,
        'result': 0.5,  # Draw
        'description': 'Draw between equal players should result in no rating change'
    }
}

# Sample player names for different games
SAMPLE_PLAYERS = {
    'chess': ['magnus', 'garry', 'bobby', 'anatoly', 'vladimir'],
    'pingpong': ['ma_long', 'fan_zhendong', 'xu_xin', 'timo_boll', 'dimitrij'],
    'backgammon': ['mochy', 'falafel', 'nack', 'stick', 'zorba']
}

# K-factor test cases
K_FACTOR_TESTS = [
    {'game': 'chess', 'expected_k': 40},
    {'game': 'pingpong', 'expected_k': 40},
    {'game': 'backgammon', 'expected_k': 10},
    {'game': 'unknown_game', 'expected_k': 40},  # Default
]