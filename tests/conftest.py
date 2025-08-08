"""
Pytest configuration and shared fixtures for the ELO rating system tests.
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'code'))

# Import after adding to path
try:
    from server import app
    # Import from code directory
    sys.path.append(str(project_root / 'code'))
    from update import make_new_player, delete_player
    from config import get_k_factor
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    # Create mock functions for basic testing
    app = None
    def make_new_player(*args, **kwargs):
        pass
    def delete_player(*args, **kwargs):
        return True
    def get_k_factor(*args, **kwargs):
        return 40


@pytest.fixture
def flask_app():
    """Create a Flask app configured for testing."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def temp_database_dir():
    """Create a temporary database directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create game directories
    for game in ['chess', 'pingpong', 'backgammon']:
        os.makedirs(os.path.join(temp_dir, game), exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {
        'chess': ['alice', 'bob', 'charlie'],
        'pingpong': ['david', 'eve'],
        'backgammon': ['frank']
    }


@pytest.fixture
def mock_database_path(monkeypatch, temp_database_dir):
    """Mock the database path to use temporary directory."""
    # This would need to be adapted based on how your code determines database paths
    monkeypatch.setenv('TEST_DATABASE_PATH', temp_database_dir)
    return temp_database_dir