#!/usr/bin/env python3
"""
Flask server for Who's Having The Most Fun ELO system
Provides web API for managing players and generating charts
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import subprocess
import json
from pathlib import Path

# Add the code directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

# Import our existing functions
from update import make_new_player, delete_last_entry

app = Flask(__name__)
CORS(app, origins="*")  # Enable CORS for all origins (including S3/CloudFront)

# Ensure proper UTF-8 encoding for all responses
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html') + '; charset=utf-8'
    return response

# Configuration
DATABASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')
CODE_DIR = os.path.join(os.path.dirname(__file__), 'code')

@app.route('/')
def serve_index():
    """Serve the main index page"""
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from web directory"""
    return send_from_directory(WEB_DIR, filename)

@app.route('/api/players/<game>', methods=['GET'])
def get_players(game):
    """Get list of players for a specific game"""
    try:
        game_dir = os.path.join(DATABASE_DIR, game)
        if not os.path.exists(game_dir):
            return jsonify({'players': []})
        
        players = []
        for filename in os.listdir(game_dir):
            if filename.endswith('.csv'):
                player_name = filename.replace('.csv', '')
                players.append(player_name)
        
        return jsonify({'players': sorted(players)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<game>', methods=['POST'])
def add_player(game):
    """Add a new player to a game"""
    try:
        data = request.get_json()
        player_name = data.get('player_name', '').strip().lower()
        
        if not player_name:
            return jsonify({'error': 'Player name is required'}), 400
        
        if not player_name.replace('_', '').isalnum():
            return jsonify({'error': 'Player name can only contain letters, numbers, and underscores'}), 400
        
        # Check if game directory exists, create if not
        game_dir = os.path.join(DATABASE_DIR, game)
        os.makedirs(game_dir, exist_ok=True)
        
        # Use our existing function to create the player
        make_new_player(player_name, game)
        
        # Generate updated charts
        generate_charts(game)
        
        return jsonify({
            'success': True, 
            'message': f'Player "{player_name}" added to {game}',
            'player_name': player_name
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<game>/<player_name>', methods=['DELETE'])
def remove_player(game, player_name):
    """Remove a player from a game"""
    try:
        file_path = os.path.join(DATABASE_DIR, game, f"{player_name}.csv")
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Player "{player_name}" not found in {game}'}), 404
        
        # Remove the player's CSV file
        os.remove(file_path)
        
        # Generate updated charts
        generate_charts(game)
        
        return jsonify({
            'success': True,
            'message': f'Player "{player_name}" removed from {game}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/<game>/generate', methods=['POST'])
def regenerate_charts(game):
    """Regenerate leaderboard and ratings charts for a game"""
    try:
        generate_charts(game)
        return jsonify({
            'success': True,
            'message': f'Charts regenerated for {game}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_charts(game):
    """Generate leaderboard and ratings progress charts for a game"""
    try:
        # Change to code directory for script execution
        original_cwd = os.getcwd()
        os.chdir(CODE_DIR)
        
        # Generate leaderboard
        try:
            subprocess.run([
                sys.executable, 'leaderboard.py', game
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            # Leaderboard might fail if no players exist, that's okay
            pass
        
        # Generate ratings progress chart
        try:
            game_dir = os.path.join('..', 'database', game)
            csv_files = list(Path(game_dir).glob('*.csv'))
            if csv_files:
                csv_paths = [str(csv_file) for csv_file in csv_files]
                subprocess.run([
                    sys.executable, 'graph.py'
                ] + csv_paths, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            # Graph might fail if no actual games played, that's okay
            pass
        
        # Restore original working directory
        os.chdir(original_cwd)
        
    except Exception as e:
        # Restore original working directory on error
        os.chdir(original_cwd)
        raise e

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'ELO server is running'})

if __name__ == '__main__':
    print("Starting ELO Rating System Server...")
    print(f"Database directory: {DATABASE_DIR}")
    print(f"Web directory: {WEB_DIR}")
    print(f"Code directory: {CODE_DIR}")
    
    # Check for SSL certificate files
    import os
    ssl_cert_path = '/etc/letsencrypt/live'
    ssl_context = None
    
    # Look for Let's Encrypt certificates
    if os.path.exists(ssl_cert_path):
        # Find the first domain directory
        for domain_dir in os.listdir(ssl_cert_path):
            cert_dir = os.path.join(ssl_cert_path, domain_dir)
            if os.path.isdir(cert_dir):
                fullchain = os.path.join(cert_dir, 'fullchain.pem')
                privkey = os.path.join(cert_dir, 'privkey.pem')
                if os.path.exists(fullchain) and os.path.exists(privkey):
                    ssl_context = (fullchain, privkey)
                    print(f"✅ Using SSL certificate for {domain_dir}")
                    print(f"Server will be available at: https://{domain_dir}:8443")
                    break
    
    if ssl_context is None:
        # Fall back to self-signed certificate
        ssl_context = 'adhoc'
        print("⚠️  Using self-signed certificate (development only)")
        print("Server will be available at: https://localhost:8443")
        print("Browsers will show security warnings for self-signed certificates")
    
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8443, ssl_context=ssl_context)