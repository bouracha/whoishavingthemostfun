"""
Unit tests for ELO rating calculations.
"""

import pytest
import sys
from pathlib import Path

# Add code directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'code'))

from update import update


class TestELOCalculations:
    """Test ELO rating calculation logic."""
    
    def test_higher_rated_player_wins_expected(self):
        """Test that higher rated player winning gives small rating change."""
        # Player 1 (1600) beats Player 2 (1400) - expected outcome
        new_rating1, new_rating2 = update(1600, 1400, 1.0, K=40)
        
        # Higher rated player should gain few points
        assert new_rating1 > 1600
        assert new_rating1 < 1620  # Should be small gain
        
        # Lower rated player should lose few points  
        assert new_rating2 < 1400
        assert new_rating2 > 1380  # Should be small loss
    
    def test_lower_rated_player_wins_upset(self):
        """Test that lower rated player winning gives large rating change."""
        # Player 2 (1400) beats Player 1 (1600) - upset
        new_rating1, new_rating2 = update(1600, 1400, 0.0, K=40)
        
        # Higher rated player should lose many points
        assert new_rating1 < 1600
        assert new_rating1 <= 1570  # Should be large loss
        
        # Lower rated player should gain many points
        assert new_rating2 > 1400
        assert new_rating2 >= 1430  # Should be large gain
    
    def test_equal_ratings_win(self):
        """Test rating changes when equal rated players play."""
        # Equal ratings (1500 vs 1500), Player 1 wins
        new_rating1, new_rating2 = update(1500, 1500, 1.0, K=40)
        
        # Should be exactly 20 point swing with K=40
        assert new_rating1 == 1520
        assert new_rating2 == 1480
    
    def test_draw_no_rating_change(self):
        """Test that draws result in no rating change for equal players."""
        # Equal ratings, draw (score = 0.5)
        new_rating1, new_rating2 = update(1500, 1500, 0.5, K=40)
        
        # Ratings should remain the same
        assert new_rating1 == 1500
        assert new_rating2 == 1500
    
    def test_different_k_factors(self):
        """Test that different K factors produce different rating changes."""
        # Same scenario with different K factors
        rating1_k40, rating2_k40 = update(1500, 1500, 1.0, K=40)
        rating1_k10, rating2_k10 = update(1500, 1500, 1.0, K=10)
        
        # K=40 should produce 4x the change of K=10
        assert rating1_k40 - 1500 == 4 * (rating1_k10 - 1500)
        assert 1500 - rating2_k40 == 4 * (1500 - rating2_k10)
    
    def test_minimum_rating_change(self):
        """Test that minimum rating change is 1 point."""
        # Very small expected change should still result in 1 point minimum
        new_rating1, new_rating2 = update(2000, 1000, 1.0, K=40)
        
        # Even with huge rating difference, minimum change should be 1
        assert new_rating1 >= 2001  # At least 1 point gain
        assert new_rating2 <= 999   # At least 1 point loss
    
    def test_rating_conservation(self):
        """Test that total rating points are conserved."""
        initial_total = 1600 + 1400
        new_rating1, new_rating2 = update(1600, 1400, 1.0, K=40)
        final_total = new_rating1 + new_rating2
        
        # Total rating should be conserved (within rounding)
        assert abs(initial_total - final_total) <= 2  # Allow for rounding
    
    @pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
    def test_valid_score_inputs(self, score):
        """Test that valid score inputs work correctly."""
        new_rating1, new_rating2 = update(1500, 1500, score, K=40)
        
        # Should return valid ratings
        assert isinstance(new_rating1, (int, float))
        assert isinstance(new_rating2, (int, float))
        assert new_rating1 > 0
        assert new_rating2 > 0