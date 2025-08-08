"""
Unit tests for game configuration and constants.
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'code'))

from config import get_k_factor, GAME_CONSTANTS


class TestGameConfig:
    """Test game configuration and K-factor logic."""
    
    def test_chess_k_factor(self):
        """Test that chess uses K-factor of 40."""
        assert get_k_factor('chess') == 40
        assert get_k_factor('CHESS') == 40  # Case insensitive
    
    def test_pingpong_k_factor(self):
        """Test that pingpong uses K-factor of 40."""
        assert get_k_factor('pingpong') == 40
        assert get_k_factor('PINGPONG') == 40
    
    def test_backgammon_k_factor(self):
        """Test that backgammon uses K-factor of 10."""
        assert get_k_factor('backgammon') == 10
        assert get_k_factor('BACKGAMMON') == 10
    
    def test_unknown_game_default_k_factor(self):
        """Test that unknown games default to K-factor of 40."""
        assert get_k_factor('unknown_game') == 40
        assert get_k_factor('') == 40
        assert get_k_factor(None) == 40
    
    def test_game_constants_structure(self):
        """Test that GAME_CONSTANTS has expected structure."""
        assert isinstance(GAME_CONSTANTS, dict)
        
        # Check that all expected games are present
        expected_games = ['chess', 'pingpong', 'backgammon']
        for game in expected_games:
            assert game in GAME_CONSTANTS
            assert 'k_factor' in GAME_CONSTANTS[game]
            assert isinstance(GAME_CONSTANTS[game]['k_factor'], int)
    
    def test_k_factor_values(self):
        """Test specific K-factor values match requirements."""
        assert GAME_CONSTANTS['chess']['k_factor'] == 40
        assert GAME_CONSTANTS['pingpong']['k_factor'] == 40  
        assert GAME_CONSTANTS['backgammon']['k_factor'] == 10
    
    @pytest.mark.parametrize("game,expected_k", [
        ('chess', 40),
        ('pingpong', 40), 
        ('backgammon', 10),
        ('Chess', 40),
        ('PingPong', 40),
        ('BACKGAMMON', 10),
        ('invalid', 40),
        ('', 40),
        (None, 40)
    ])
    def test_k_factor_parametrized(self, game, expected_k):
        """Parametrized test for various game inputs."""
        assert get_k_factor(game) == expected_k