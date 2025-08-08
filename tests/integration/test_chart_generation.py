"""
Integration tests for chart generation functionality.
"""

import pytest
import os
import tempfile
import subprocess
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestChartGeneration:
    """Test chart generation integration."""
    
    def test_leaderboard_generation_chess(self):
        """Test that chess leaderboard generation works."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Import the generate_charts function from server
            from server import generate_charts
            
            generate_charts('chess')
            
            # Should have called leaderboard generation
            assert mock_run.call_count >= 1
            # Check that leaderboard.py was called with chess
            calls = [str(call) for call in mock_run.call_args_list]
            assert any('leaderboard.py' in call and 'chess' in call for call in calls)
    
    def test_rating_chart_generation_chess(self):
        """Test that chess rating charts are generated."""
        with patch('subprocess.run') as mock_run:
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=['player1.csv', 'player2.csv']):
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    from server import generate_charts
                    
                    generate_charts('chess')
                    
                    # Should have called both leaderboard and graph generation
                    assert mock_run.call_count >= 2
    
    def test_chart_generation_no_players(self):
        """Test chart generation when no players exist."""
        with patch('subprocess.run') as mock_run:
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=[]):  # No CSV files
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    from server import generate_charts
                    
                    generate_charts('chess')
                    
                    # Should still call leaderboard generation, but not graph generation
                    assert mock_run.call_count >= 1
    
    def test_chart_generation_handles_errors(self):
        """Test that chart generation handles subprocess errors gracefully."""
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd')):
            from server import generate_charts
            
            # Should not raise exception, but handle gracefully
            try:
                generate_charts('chess')
                # If no exception raised, test passes
            except subprocess.CalledProcessError:
                pytest.fail("Chart generation should handle subprocess errors gracefully")
    
    @pytest.mark.parametrize("game", ['chess', 'pingpong', 'backgammon'])
    def test_chart_generation_all_games(self, game):
        """Test that chart generation works for all supported games."""
        with patch('subprocess.run') as mock_run:
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=['player1.csv']):
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    from server import generate_charts
                    
                    generate_charts(game)
                    
                    # Should have called subprocess for this game
                    assert mock_run.call_count >= 1
                    
                    # Check that the game was passed correctly
                    calls = [str(call) for call in mock_run.call_args_list]
                    assert any(game in call for call in calls)
    
    def test_leaderboard_script_exists(self):
        """Test that the leaderboard script exists and is executable."""
        leaderboard_path = Path('code/leaderboard.py')
        assert leaderboard_path.exists(), "leaderboard.py should exist"
        assert leaderboard_path.is_file(), "leaderboard.py should be a file"
    
    def test_graph_script_exists(self):
        """Test that the graph script exists and is executable."""
        graph_path = Path('code/graph.py')
        assert graph_path.exists(), "graph.py should exist"
        assert graph_path.is_file(), "graph.py should be a file"
    
    def test_chart_output_directory_structure(self):
        """Test that chart generation creates files in correct location."""
        with patch('subprocess.run') as mock_run:
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=['player1.csv']):
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    from server import generate_charts
                    
                    generate_charts('chess')
                    
                    # Verify that the subprocess calls use correct paths
                    calls = mock_run.call_args_list
                    assert len(calls) >= 1
                    
                    # First call should be for leaderboard generation
                    first_call_args = calls[0][0][0]  # First positional argument
                    assert 'leaderboard.py' in ' '.join(first_call_args)
                    assert 'chess' in ' '.join(first_call_args)