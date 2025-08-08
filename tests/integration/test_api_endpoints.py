"""
Integration tests for Flask API endpoints.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock


class TestAPIEndpoints:
    """Test Flask API endpoint functionality."""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct response."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'message' in data
    
    def test_add_player_chess_success(self, client):
        """Test adding a new chess player successfully."""
        with patch('server.make_new_player') as mock_make_player:
            with patch('server.generate_charts') as mock_generate:
                mock_make_player.return_value = None  # Successful creation
                
                response = client.post('/api/players/chess', 
                                     data=json.dumps({'player_name': 'testplayer'}),
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                assert 'testplayer' in data['message']
                
                # Should have called the player creation and chart generation
                mock_make_player.assert_called_once_with('testplayer', 'chess')
                mock_generate.assert_called_once_with('chess')
    
    def test_add_player_pingpong_success(self, client):
        """Test adding a new pingpong player successfully."""
        with patch('server.make_new_player') as mock_make_player:
            with patch('server.generate_charts') as mock_generate:
                response = client.post('/api/players/pingpong',
                                     data=json.dumps({'player_name': 'alice'}),
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                
                mock_make_player.assert_called_once_with('alice', 'pingpong')
                mock_generate.assert_called_once_with('pingpong')
    
    def test_add_player_backgammon_success(self, client):
        """Test adding a new backgammon player successfully."""
        with patch('server.make_new_player') as mock_make_player:
            with patch('server.generate_charts') as mock_generate:
                response = client.post('/api/players/backgammon',
                                     data=json.dumps({'player_name': 'bob'}),
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                
                mock_make_player.assert_called_once_with('bob', 'backgammon')
                mock_generate.assert_called_once_with('backgammon')
    
    def test_add_player_invalid_game(self, client):
        """Test adding player to invalid game (currently allowed - creates directory)."""
        response = client.post('/api/players/invalid_game',
                             data=json.dumps({'player_name': 'testplayer'}),
                             content_type='application/json')
        
        # Currently the server accepts any game name and creates directory
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_add_player_missing_name(self, client):
        """Test adding player without name returns error."""
        response = client.post('/api/players/chess',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_player_empty_name(self, client):
        """Test adding player with empty name returns error."""
        response = client.post('/api/players/chess',
                             data=json.dumps({'player_name': ''}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_player_invalid_json(self, client):
        """Test adding player with invalid JSON returns error."""
        response = client.post('/api/players/chess',
                             data='invalid json',
                             content_type='application/json')
        
        # Flask returns 500 for JSON decode errors, not 400
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_player_exception_handling(self, client):
        """Test that exceptions during player creation are handled."""
        with patch('server.make_new_player', side_effect=Exception("Database error")):
            response = client.post('/api/players/chess',
                                 data=json.dumps({'player_name': 'testplayer'}),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_static_file_serving(self, client):
        """Test that static files are served correctly."""
        # Test that index.html is served
        response = client.get('/')
        assert response.status_code == 200
        assert b'Monica Geller' in response.data or b'ELO' in response.data
    
    def test_chess_page_serving(self, client):
        """Test that chess.html is served correctly."""
        response = client.get('/chess.html')
        assert response.status_code == 200
        # Should contain chess-specific content
        assert b'chess' in response.data.lower()
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.get('/api/health')
        assert 'Access-Control-Allow-Origin' in response.headers
        assert response.headers['Access-Control-Allow-Origin'] == '*'
    
    @pytest.mark.parametrize("game", ['chess', 'pingpong', 'backgammon'])
    def test_add_player_all_games(self, client, game):
        """Parametrized test for adding players to all games."""
        with patch('server.make_new_player') as mock_make_player:
            with patch('server.generate_charts') as mock_generate:
                response = client.post(f'/api/players/{game}',
                                     data=json.dumps({'player_name': 'testplayer'}),
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                
                mock_make_player.assert_called_once_with('testplayer', game)
                mock_generate.assert_called_once_with(game)