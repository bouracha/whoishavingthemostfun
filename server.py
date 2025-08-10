#!/usr/bin/env python3
"""
Flask server for Who's Having The Most Fun ELO system
Provides web API for managing players and generating charts
"""

from flask import Flask, request, jsonify, send_from_directory, send_file, session
from flask_cors import CORS
import os
import sys
import pandas as pd
import subprocess
import json
import hashlib
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

# Add the code directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

# Import our existing functions
from update import make_new_player, delete_last_entry

app = Flask(__name__)
# Secret key for sessions (override via env in production)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')

# Enable CORS. Note: if you later use credentials from a different origin, add supports_credentials=True
CORS(app, origins="*")  # Enable CORS for all origins (including S3/CloudFront)

# Session configuration
app.permanent_session_lifetime = timedelta(days=7)

# Ensure proper UTF-8 encoding for all responses
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html') + '; charset=utf-8'
    return response

# Configuration
DATABASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')
CODE_DIR = os.path.join(os.path.dirname(__file__), 'code')
TEAMS_FILE = os.path.join(DATABASE_DIR, 'teams.json')


def ensure_teams_file():
    """Create a default teams.json with a single team if it doesn't exist."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    if not os.path.exists(TEAMS_FILE):
        # Seed with example team 'bourached' / password 'just4fun'
        teams_data = {
            "bourached": {
                "password_hash": generate_password_hash("just4fun")
            }
        }
        with open(TEAMS_FILE, 'w') as f:
            json.dump(teams_data, f)


def load_teams():
    if not os.path.exists(TEAMS_FILE):
        ensure_teams_file()
    try:
        with open(TEAMS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def sanitize_team(team: str) -> str:
    team = (team or '').strip().lower()
    # Allow only a-z, 0-9, underscore, hyphen
    if not team or not all(c.isalnum() or c in ['_', '-'] for c in team):
        raise ValueError('Invalid team name')
    return team


def get_team_from_session():
    team = session.get('team')
    return team


def assert_team_access(requested_team: str):
    current = get_team_from_session()
    if current != requested_team:
        raise PermissionError('Forbidden: not logged into this team')

@app.route('/')
def serve_index():
    """Serve the main index page"""
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from web directory"""
    return send_from_directory(WEB_DIR, filename)

@app.route('/chess')
def serve_chess():
    """Serve chess page with clean URL"""
    return send_from_directory(WEB_DIR, 'chess.html')

@app.route('/pingpong')
def serve_pingpong():
    """Serve ping pong page with clean URL"""
    return send_from_directory(WEB_DIR, 'pingpong.html')

@app.route('/backgammon')
def serve_backgammon():
    """Serve backgammon page with clean URL"""
    return send_from_directory(WEB_DIR, 'backgammon.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        team = sanitize_team(data.get('team', ''))
        password = data.get('password', '')

        teams = load_teams()
        team_info = teams.get(team)
        if not team_info or not check_password_hash(team_info.get('password_hash', ''), password):
            return jsonify({"error": "Invalid team or password"}), 401

        session.permanent = True
        session['team'] = team
        return jsonify({"success": True, "team": team})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('team', None)
    return jsonify({"success": True})

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

@app.route('/api/<team>/players/<game>', methods=['GET'])
def get_players_team(team, game):
    """Get list of players for a specific game within a team"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        team_dir = os.path.join(DATABASE_DIR, team, game)
        if not os.path.exists(team_dir):
            return jsonify({'players': []})
        players = []
        for filename in os.listdir(team_dir):
            if filename.endswith('.csv'):
                players.append(filename[:-4])
        return jsonify({'players': sorted(players), 'team': team})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
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
        
        # Optional backend-only overrides
        starting_rating = float(data.get('starting_rating', 1200.0))
        starting_timestamp = data.get('starting_timestamp') or None

        # Use our existing function to create the player
        make_new_player(
            player_name,
            game,
            starting_rating=starting_rating,
            starting_timestamp=starting_timestamp,
        )
        
        # Generate updated charts
        generate_charts(game)
        
        return jsonify({
            'success': True, 
            'message': f'Player "{player_name}" added to {game}',
            'player_name': player_name
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<team>/players/<game>', methods=['POST'])
def add_player_team(team, game):
    """Add a new player to a team-specific game"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        data = request.get_json(force=True)
        player_name = data.get('player_name', '').strip().lower()

        if not player_name:
            return jsonify({'error': 'Player name is required'}), 400
        if not player_name.replace('_', '').isalnum():
            return jsonify({'error': 'Player name can only contain letters, numbers, and underscores'}), 400

        # Ensure directories
        team_game_dir = os.path.join(DATABASE_DIR, team, game)
        os.makedirs(team_game_dir, exist_ok=True)

        # Optional backend-only overrides
        starting_rating = float(data.get('starting_rating', 1200.0))
        starting_timestamp = data.get('starting_timestamp') or None

        # Use our existing function with team-awareness
        make_new_player(
            player_name,
            game,
            team=team,
            starting_rating=starting_rating,
            starting_timestamp=starting_timestamp,
        )

        # Generate updated charts for this team
        generate_charts_for_team(team, game)

        return jsonify({'success': True, 'message': f'Player "{player_name}" added to {game} for team {team}', 'player_name': player_name, 'team': team})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
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

@app.route('/api/<team>/players/<game>/<player_name>', methods=['DELETE'])
def remove_player_team(team, game, player_name):
    """Remove a player from a team-specific game"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        file_path = os.path.join(DATABASE_DIR, team, game, f"{player_name}.csv")
        if not os.path.exists(file_path):
            return jsonify({'error': f'Player "{player_name}" not found in {game} for team {team}'}), 404
        os.remove(file_path)
        generate_charts_for_team(team, game)
        return jsonify({'success': True, 'message': f'Player "{player_name}" removed from {game}', 'team': team})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
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

@app.route('/api/<team>/charts/<game>/generate', methods=['POST'])
def regenerate_charts_team(team, game):
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        generate_charts_for_team(team, game)
        return jsonify({'success': True, 'message': f'Charts regenerated for {game}', 'team': team})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _deterministic_choice(options, key: str) -> str:
    """Pick a stable option based on a hash of key (prevents message flicker on reload)."""
    if not options:
        return ''
    h = hashlib.sha256(key.encode('utf-8')).hexdigest()
    idx = int(h, 16) % len(options)
    return options[idx]

def _generate_result_commentary(player1_display: str, player2_display: str, result: str, probability: float, timestamp: str) -> str:
    """Create fun commentary for a result. probability is P(player1 wins)."""
    # Draw case
    if result == '1/2-1/2':
        lower_player = player1_display if probability < 0.5 else player2_display
        lower_prob = probability if probability < 0.5 else (1 - probability)
        prob_pct = f"<span class='inline-probability'>{lower_prob * 100:.1f}%</span>"
        draw_comments = [
            f"It was a fierce battle, but a peaceful result! A good result for {lower_player}, who had only a {prob_pct} chance of winning.",
            f"An honorable draw! {lower_player} can be pleased with this outcome, having faced {prob_pct} odds.",
            f"Both warriors earned their stripes in this {prob_pct} underdog story that ended in a draw!",
            f"A diplomatic conclusion! {lower_player} held their ground despite {prob_pct} winning chances."
        ]
        return _deterministic_choice(draw_comments, key=f"{timestamp}-{player1_display}-{player2_display}-{result}-{probability}")

    # Decisive cases
    winner = player1_display if result == '1-0' else player2_display
    winner_prob = probability if result == '1-0' else (1 - probability)
    prob_pct = f"<span class='inline-probability'>{winner_prob * 100:.1f}%</span>"

    if winner_prob >= 0.8:
        comments = [
            f"{winner} cruised to victory with {prob_pct} odds. As expected!",
            f"No surprises here! {winner} dominated with {prob_pct} probability.",
            f"{winner} delivered the expected result with {prob_pct} chances. Textbook!",
        ]
    elif winner_prob >= 0.65:
        comments = [
            f"{winner} lived up to expectations with a solid {prob_pct} favorite win!",
            f"The favorite prevails! {winner} with {prob_pct} odds gets the W.",
            f"{winner} proved why they had {prob_pct} winning chances. Well played!",
        ]
    elif winner_prob >= 0.35:
        comments = [
            f"What a nail-biter! {winner} edges it out with {prob_pct} odds.",
            f"{winner} squeaks by in this {prob_pct} coin-flip battle!",
            f"Close call! {winner} with {prob_pct} chances takes the victory.",
            f"Anyone's game, but {winner} ({prob_pct}) emerges victorious!",
        ]
    else:
        comments = [
            f"🚨 UPSET ALERT! {winner} shocks everyone with only {prob_pct} odds!",
            f"Against all odds! {winner} pulls off the miracle with {prob_pct} chances!",
            f"David vs Goliath moment! {winner} defies {prob_pct} probability!",
            f"Stunning upset! {winner} had just {prob_pct} odds but found a way!",
        ]
    return _deterministic_choice(comments, key=f"{timestamp}-{player1_display}-{player2_display}-{result}-{probability}")

@app.route('/api/recent-results', methods=['GET'])
def get_recent_results_main():
    """Get the 5 most recent results for the main (non-team) database"""
    try:
        results_file = os.path.join(DATABASE_DIR, 'results.csv')
        
        if not os.path.exists(results_file):
            return jsonify({'results': []})
        
        # Read the results CSV
        df = pd.read_csv(results_file)
        
        if df.empty:
            return jsonify({'results': []})
        
        # Sort by timestamp descending and get the 5 most recent
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_sorted = df.sort_values('timestamp', ascending=False).head(5)
        
        # Format results for frontend
        results = []
        for _, row in df_sorted.iterrows():
            # Format player names for display
            player1_display = row['player1'].replace('_', ' ').title()
            player2_display = row['player2'].replace('_', ' ').title()
            timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            probability = float(row['probability'])
            
            # Generate commentary on the backend
            commentary = _generate_result_commentary(
                player1_display, player2_display, row['result'], probability, timestamp_str
            )
            
            results.append({
                'timestamp': timestamp_str,
                'game': row['game'].title(),
                'player1': player1_display,
                'player2': player2_display,
                'result': row['result'],
                'probability': probability,
                'commentary': commentary
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<team>/recent-results', methods=['GET'])
def get_recent_results(team):
    """Get the 5 most recent results for a team"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        
        results_file = os.path.join(DATABASE_DIR, team, 'results.csv')
        
        if not os.path.exists(results_file):
            return jsonify({'results': []})
        
        # Read the results CSV
        df = pd.read_csv(results_file)
        
        if df.empty:
            return jsonify({'results': []})
        
        # Sort by timestamp descending and get the 5 most recent
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_sorted = df.sort_values('timestamp', ascending=False).head(5)
        
        # Format results for frontend
        results = []
        for _, row in df_sorted.iterrows():
            # Format player names for display
            player1_display = row['player1'].replace('_', ' ').title()
            player2_display = row['player2'].replace('_', ' ').title()
            timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            probability = float(row['probability'])
            
            # Generate commentary on the backend
            commentary = _generate_result_commentary(
                player1_display, player2_display, row['result'], probability, timestamp_str
            )
            
            results.append({
                'timestamp': timestamp_str,
                'game': row['game'].title(),
                'player1': player1_display,
                'player2': player2_display,
                'result': row['result'],
                'probability': probability,
                'commentary': commentary
            })
        
        return jsonify({'results': results})
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<game>', methods=['POST'])
def submit_result(game):
    """Submit a game result"""
    try:
        data = request.get_json()
        player1 = data.get('player1', '').strip()
        player2 = data.get('player2', '').strip()
        result = data.get('result', '')  # '1-0', '0-1', or '1/2-1/2'
        
        if not player1 or not player2:
            return jsonify({'error': 'Both players are required'}), 400
        
        if player1 == player2:
            return jsonify({'error': 'Players must be different'}), 400
        
        if result not in ['1-0', '0-1', '1/2-1/2']:
            return jsonify({'error': 'Invalid result format'}), 400
        
        # Convert result to score for main.py
        if result == '1-0':
            score = 1.0
        elif result == '0-1':
            score = 0.0
        else:  # 1/2-1/2
            score = 0.5
        
        # Change to code directory for script execution
        original_cwd = os.getcwd()
        os.chdir(CODE_DIR)
        
        try:
            # Call main.py with the game result
            subprocess.run([
                sys.executable, 'main.py',
                '--game', game,
                '--player1', player1,
                '--player2', player2,
                '--score', str(score)
            ], check=True, capture_output=True, text=True)
            
            # Generate updated charts
            generate_charts(game)
            
            return jsonify({
                'success': True,
                'message': f'Result submitted: {player1} vs {player2} ({result})',
                'game': game,
                'player1': player1,
                'player2': player2,
                'result': result
            })
            
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Failed to submit result: {e.stderr}'}), 500
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<team>/results/<game>', methods=['POST'])
def submit_result_team(team, game):
    """Submit a game result for a specific team"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        data = request.get_json(force=True)
        player1 = data.get('player1', '').strip()
        player2 = data.get('player2', '').strip()
        result = data.get('result', '')

        if not player1 or not player2:
            return jsonify({'error': 'Both players are required'}), 400
        if player1 == player2:
            return jsonify({'error': 'Players must be different'}), 400
        if result not in ['1-0', '0-1', '1/2-1/2']:
            return jsonify({'error': 'Invalid result format'}), 400

        score = 1.0 if result == '1-0' else 0.0 if result == '0-1' else 0.5

        original_cwd = os.getcwd()
        os.chdir(CODE_DIR)
        try:
            # Ensure team directories exist for data and output
            os.makedirs(os.path.join('..', 'database', team, game), exist_ok=True)
            os.makedirs(os.path.join('..', 'web', team), exist_ok=True)

            # Call main.py with team awareness
            subprocess.run([
                sys.executable, 'main.py',
                '--game', game,
                '--player1', player1,
                '--player2', player2,
                '--score', str(score),
                '--team', team
            ], check=True, capture_output=True, text=True)

            # Generate updated charts for this team
            generate_charts_for_team(team, game)

            return jsonify({'success': True, 'message': f'Result submitted: {player1} vs {player2} ({result})', 'game': game, 'team': team})
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Failed to submit result: {e.stderr}'}), 500
        finally:
            os.chdir(original_cwd)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
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


def generate_charts_for_team(team: str, game: str):
    """Generate charts for a specific team/game, saving under web/<team>/..."""
    original_cwd = os.getcwd()
    os.chdir(CODE_DIR)
    try:
        # Ensure output subdir exists
        os.makedirs(os.path.join('..', 'web', team), exist_ok=True)

        # Leaderboard: pass team/game as folder to leverage existing script
        try:
            subprocess.run([
                sys.executable, 'leaderboard.py', f"{team}/{game}"
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            pass

        # Ratings progress: pass CSV paths
        try:
            team_game_dir = os.path.join('..', 'database', team, game)
            csv_files = list(Path(team_game_dir).glob('*.csv'))
            if csv_files:
                csv_paths = [str(csv_file) for csv_file in csv_files]
                subprocess.run([
                    sys.executable, 'graph.py'
                ] + csv_paths, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            pass
    finally:
        os.chdir(original_cwd)


# Team chart serving endpoints
@app.route('/api/<team>/charts/<game>/leaderboard.png')
def serve_team_leaderboard(team, game):
    team = sanitize_team(team)
    try:
        assert_team_access(team)
    except PermissionError:
        return jsonify({'error': 'Forbidden'}), 403
    # leaderboard.py saves as web/<game_folder>_leaderboard.png; with game_folder "team/game"
    # This results in web/<team>/game_leaderboard.png
    team_dir = os.path.join(WEB_DIR, team)
    filename = f"{game}_leaderboard.png"
    return send_from_directory(team_dir, filename)


@app.route('/api/<team>/charts/<game>/ratings_progress.png')
def serve_team_ratings_progress(team, game):
    team = sanitize_team(team)
    try:
        assert_team_access(team)
    except PermissionError:
        return jsonify({'error': 'Forbidden'}), 403
    # graph.py will save into web/<team>/<game>_ratings_progress.png if team is detected
    team_dir = os.path.join(WEB_DIR, team)
    filename = f"{game}_ratings_progress.png"
    return send_from_directory(team_dir, filename)


# Basic pages for login and team landing
@app.route('/login')
def serve_login():
    return send_from_directory(WEB_DIR, 'login.html')


@app.route('/t/<team>')
def serve_team_home(team):
    # For now, serve the same index; frontend can read team from path later
    try:
        team = sanitize_team(team)
    except ValueError:
        pass
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/t/<team>/<game>')
def serve_team_game(team, game):
    # Serve the same game pages under team-prefixed clean URLs
    try:
        team = sanitize_team(team)
    except ValueError:
        pass
    game = (game or '').lower()
    if game == 'chess':
        return send_from_directory(WEB_DIR, 'chess.html')
    if game == 'pingpong':
        return send_from_directory(WEB_DIR, 'pingpong.html')
    if game == 'backgammon':
        return send_from_directory(WEB_DIR, 'backgammon.html')
    return jsonify({'error': 'Unknown game'}), 404

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'ELO server is running'})

if __name__ == '__main__':
    print("🚀 Starting ELO Rating System Server...")
    print(f"Database directory: {DATABASE_DIR}")
    print(f"Web directory: {WEB_DIR}")
    print(f"Code directory: {CODE_DIR}")
    ensure_teams_file()
    print()
    print("✅ Running on HTTP (user-friendly, no certificates needed)")
    print("Server will be available at: http://localhost:8080")
    print("API accessible at: http://your-ec2-ip:8080")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8080)