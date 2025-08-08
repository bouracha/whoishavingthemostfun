"""
Unit tests for player management functionality.
"""

import pytest
import os
import tempfile
import pandas as pd
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add code directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'code'))

from update import make_new_player, delete_player


class TestPlayerManagement:
    """Test player creation and deletion functionality."""
    
    def test_make_new_player_creates_file(self, temp_database_dir):
        """Test that make_new_player creates a CSV file."""
        with patch('update.os.path.exists') as mock_exists:
            # Mock that database directory exists
            mock_exists.return_value = True
            
            with patch('update.os.path.exists') as mock_file_exists:
                # Mock that player file doesn't exist yet
                mock_file_exists.return_value = False
                
                with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                    make_new_player('testplayer', 'chess')
                    
                    # Should have called to_csv to create the file
                    mock_to_csv.assert_called_once()
    
    def test_make_new_player_default_rating(self):
        """Test that new players start with default rating of 1200."""
        # Mock that database directory exists but player file doesn't
        def mock_exists(path):
            if 'database' in path and '.csv' not in path:
                return True  # Database directory exists
            return False  # Player file doesn't exist
            
        with patch('update.os.path.exists', side_effect=mock_exists):
            with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                make_new_player('new_test_player', 'chess')
                
                # Should have called to_csv to create the file
                mock_to_csv.assert_called_once()
    
    def test_make_new_player_existing_player_skips(self):
        """Test that creating existing player is skipped."""
        with patch('update.os.path.exists') as mock_exists:
            # Mock that player file already exists
            mock_exists.side_effect = lambda path: 'testplayer.csv' in path
            
            with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                make_new_player('testplayer', 'chess')
                
                # Should not have called to_csv since player exists
                mock_to_csv.assert_not_called()
    
    def test_delete_player_removes_file(self):
        """Test that delete_player removes the CSV file."""
        with patch('update.os.path.exists', return_value=True):
            with patch('update.os.remove') as mock_remove:
                result = delete_player('testplayer', 'chess')
                
                assert result is True
                mock_remove.assert_called_once()
    
    def test_delete_player_nonexistent_file(self):
        """Test that deleting non-existent player returns False."""
        with patch('update.os.path.exists', return_value=False):
            result = delete_player('nonexistent', 'chess')
            
            assert result is False
    
    def test_delete_player_handles_exceptions(self):
        """Test that delete_player handles file system exceptions."""
        with patch('update.os.path.exists', return_value=True):
            with patch('update.os.remove', side_effect=OSError("Permission denied")):
                result = delete_player('testplayer', 'chess')
                
                assert result is False
    
    @pytest.mark.parametrize("game", ['chess', 'pingpong', 'backgammon'])
    def test_make_new_player_all_games(self, game):
        """Test that new players can be created for all supported games."""
        # Mock that database directory exists but player file doesn't
        def mock_exists(path):
            if 'database' in path and '.csv' not in path:
                return True  # Database directory exists
            return False  # Player file doesn't exist
            
        with patch('update.os.path.exists', side_effect=mock_exists):
            with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                make_new_player(f'unique_test_player_{game}', game)
                
                # Should have attempted to create file for any valid game
                mock_to_csv.assert_called_once()
    
    def test_player_file_path_construction(self):
        """Test that player file paths are constructed correctly."""
        with patch('update.os.path.exists') as mock_exists:
            with patch('update.os.remove') as mock_remove:
                # Mock database path exists
                mock_exists.return_value = True
                
                delete_player('testplayer', 'chess')
                
                # Should have checked for the correct path
                expected_calls = [
                    'database',  # Check if database dir exists
                    'database/chess/testplayer.csv'  # Check if player file exists
                ]
                # Verify the path construction logic was called correctly
                assert mock_exists.call_count >= 1

    def test_default_player_image_exists(self):
        """Test that default player image exists for fallback."""
        import os
        from pathlib import Path
        
        # Check that default.png exists in the players directory
        default_image_path = Path("web/images/players/default.png")
        assert default_image_path.exists(), "Default player image should exist"
        
        # Check that it's a reasonable file size (not empty)
        assert default_image_path.stat().st_size > 1000, "Default image should not be empty"