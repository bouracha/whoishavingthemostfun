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
from update import make_new_player, delete_last_entry, undo_last_result, submit_game_with_charts, calculate_elo_probability, add_comment_to_result

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
    return send_from_directory(WEB_DIR, 'game.html')

@app.route('/pingpong')
def serve_pingpong():
    """Serve ping pong page with clean URL"""
    return send_from_directory(WEB_DIR, 'game.html')

@app.route('/backgammon')
def serve_backgammon():
    """Serve backgammon page with clean URL"""
    return send_from_directory(WEB_DIR, 'game.html')

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

def format_player_name_for_display(player_name: str) -> str:
    """Format player name for display, with special case for Q suffix"""
    display_name = player_name.replace('_', ' ').title()
    
    # Replace any " Q" with " (-♛)" (space + Q becomes space + brackets + queen)
    display_name = display_name.replace(' Q', ' (-♛)')
    
    return display_name

# Removed on-the-fly rating change calculation; changes are now persisted in results.csv

def _generate_result_commentary(player1_display: str, player2_display: str, result: str, probability: float, timestamp: str) -> str:
    """Create fun commentary for a result. probability is P(player1 wins)."""
    # Draw case
    if result == '1/2-1/2':
        lower_player = player1_display if probability < 0.5 else player2_display
        lower_prob = probability if probability < 0.5 else (1 - probability)
        prob_pct = f"<span class='inline-probability'>{lower_prob * 100:.1f}%</span>"
        draw_comments = [
            f"🤝 It was a fierce battle, but a peaceful result! A good result for {lower_player}, who had only a {prob_pct} chance of winning.",
            f"🤝 An honorable draw! {lower_player} can be pleased with this outcome, having faced {prob_pct} odds.",
            f"🤝 Both warriors earned their stripes in this {prob_pct} underdog story that ended in a draw!",
            f"🤝 A diplomatic conclusion! {lower_player} held their ground despite {prob_pct} winning chances.",
            f"🤝 Peace treaty signed! {lower_player} survives the {prob_pct} odds and lives to fight another day!",
            f"🤝 Stalemate! {lower_player} proves that even with {prob_pct} odds, you can't always lose!",
            f"🤝 Mutual respect achieved! {lower_player} shows that {prob_pct} odds are just numbers on paper!",
            f"🤝 Draw your weapons... and then put them away! {lower_player} escapes with dignity despite {prob_pct} odds!",
            f"🤝 A gentleman's agreement! {lower_player} demonstrates that {prob_pct} odds don't mean certain defeat!",
            f"🤝 Both players leave with their honor intact! {lower_player} defies the {prob_pct} probability gods!"
        ]
        return _deterministic_choice(draw_comments, key=f"{timestamp}-{player1_display}-{player2_display}-{result}-{probability}")

    # Decisive cases
    winner = player1_display if result == '1-0' else player2_display
    loser = player2_display if result == '1-0' else player1_display
    # Use the correct probability for the winner
    winner_prob = probability if result == '1-0' else (1 - probability)
    prob_pct = f"<span class='inline-probability'>{winner_prob * 100:.1f}%</span>"

    if winner_prob >= 0.8:
        comments = [
            f"👑 {winner} cruised to victory with {prob_pct} odds. As expected!",
            f"👑 No surprises here! {winner} dominated with {prob_pct} probability.",
            f"👑 {winner} delivered the expected result with {prob_pct} chances. Textbook!",
            f"👑 {winner} made it look easy with {prob_pct} odds. {loser} never stood a chance!",
            f"👑 {winner} flexed their {prob_pct} muscles and crushed the competition!",
            f"👑 {winner} showed why they had {prob_pct} odds - pure dominance!",
            f"👑 {winner} steamrolled through with {prob_pct} probability. {loser} is probably still recovering!",
            f"👑 {winner} proved that {prob_pct} odds aren't just numbers - they're a promise!",
            f"👑 {winner} made {loser} question their life choices with that {prob_pct} performance!",
            f"👑 {winner} didn't just win, they sent a message with {prob_pct} authority!"
        ]
    elif winner_prob >= 0.65:
        comments = [
            f"🏆 {winner} lived up to expectations with a solid {prob_pct} favorite win!",
            f"🏆 The favorite prevails! {winner} with {prob_pct} odds gets the W.",
            f"🏆 {winner} proved why they had {prob_pct} winning chances. Well played!",
            f"🏆 {winner} showed their class with a {prob_pct} probability victory!",
            f"🏆 {winner} made the {prob_pct} odds look generous to {loser}!",
            f"🏆 {winner} demonstrated that {prob_pct} odds are earned, not given!",
            f"🏆 {winner} took care of business with {prob_pct} efficiency!",
            f"🏆 {winner} proved that {prob_pct} odds are just the beginning of their story!",
            f"🏆 {winner} made {loser} feel the heat, converting {prob_pct} odds into a win!",
            f"🏆 {winner} showed why they're the {prob_pct} favorite - pure skill!"
        ]
    elif winner_prob >= 0.35:
        comments = [
            f"⚡ What a nail-biter! {winner} edges it out with {prob_pct} odds.",
            f"⚡ {winner} squeaks by in this {prob_pct} coin-flip battle!",
            f"⚡ Close call! {winner} with {prob_pct} chances takes the victory.",
            f"⚡ Anyone's game, but {winner} ({prob_pct}) emerges victorious!",
            f"⚡ {winner} found a way to win in this {prob_pct} thriller!",
            f"⚡ {winner} proved that {prob_pct} odds are just a suggestion!",
            f"⚡ {winner} made the most of their {prob_pct} chances!",
            f"⚡ {winner} showed that {prob_pct} probability can be enough!",
            f"⚡ {winner} turned {prob_pct} odds into pure gold!",
            f"⚡ {winner} made {loser} sweat despite {prob_pct} odds!"
        ]
    else:
        comments = [
            f"🚨 UPSET ALERT! {winner} shocks everyone with only {prob_pct} odds!",
            f"🚨 Against all odds! {winner} pulls off the miracle with {prob_pct} chances!",
            f"🚨 David vs Goliath moment! {winner} defies {prob_pct} probability!",
            f"🚨 Stunning upset! {winner} had just {prob_pct} odds but found a way!",
            f"🚨 {winner} just made {loser} question everything with {prob_pct} odds!",
            f"🚨 {winner} pulled a rabbit out of a hat with {prob_pct} probability!",
            f"🚨 {winner} made the impossible possible with {prob_pct} odds!",
            f"🚨 {winner} just wrote a new chapter in the underdog story with {prob_pct} chances!",
            f"🚨 {winner} proved that {prob_pct} odds are just numbers on a screen!",
            f"🚨 {winner} made {loser} eat their words with {prob_pct} determination!",
            f"🚨 {winner} just became a legend with {prob_pct} odds!",
            f"🚨 {winner} showed that miracles happen with {prob_pct} probability!",
            f"🚨 {winner} made the {prob_pct} underdogs proud!",
            f"🚨 {winner} just pulled off the heist of the century with {prob_pct} odds!",
            f"🚨 {winner} made {loser} look like they forgot how to play with {prob_pct} skill!"
        ]
    return _deterministic_choice(comments, key=f"{timestamp}-{player1_display}-{player2_display}-{result}-{probability}")

@app.route('/api/recent-results', methods=['GET'])
def get_recent_results_main():
    """Get recent results for the main (non-team) database with pagination"""
    try:
        results_file = os.path.join(DATABASE_DIR, 'results.csv')
        
        if not os.path.exists(results_file):
            return jsonify({'results': [], 'has_more': False})
        
        # Read the results CSV
        df = pd.read_csv(results_file)
        
        if df.empty:
            return jsonify({'results': [], 'has_more': False})
        
        # Get pagination parameters
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 25, type=int)
        
        # Sort by timestamp descending and get paginated results
        # Handle both timestamp formats (with and without microseconds)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
        df_sorted = df.sort_values('timestamp', ascending=False)
        
        # Check if there are more results available
        total_results = len(df_sorted)
        has_more = (offset + limit) < total_results
        
        # Get the requested slice
        df_paginated = df_sorted.iloc[offset:offset + limit]
        
        # Format results for frontend
        results = []
        for _, row in df_paginated.iterrows():
            # Format player names for display
            player1_display = format_player_name_for_display(row['player1'])
            player2_display = format_player_name_for_display(row['player2'])
            timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            probability = float(row['probability'])
            
            # Read persisted rating changes from results.csv (if present)
            try:
                p1c = row['player1_change'] if 'player1_change' in df_paginated.columns else None
            except Exception:
                p1c = None
            try:
                p2c = row['player2_change'] if 'player2_change' in df_paginated.columns else None
            except Exception:
                p2c = None
            
            # Normalize to int or None
            def to_int_or_none(v):
                try:
                    import pandas as _pd
                    if v is None or (isinstance(v, float) and _pd.isna(v)):
                        return None
                    return int(round(float(v)))
                except Exception:
                    return None
            player1_change = to_int_or_none(p1c)
            player2_change = to_int_or_none(p2c)
            
            # Generate commentary on the backend
            commentary = _generate_result_commentary(
                player1_display, player2_display, row['result'], probability, timestamp_str
            )
            
            # Parse comments if they exist
            comments = []
            if 'comments' in df_paginated.columns and pd.notna(row['comments']) and row['comments'] != '':
                try:
                    import ast
                    if row['comments'] != '[]':
                        comments_list = ast.literal_eval(row['comments'])
                        if isinstance(comments_list, list):
                            comments = comments_list
                except (ValueError, SyntaxError):
                    # If parsing fails, treat as empty
                    comments = []
            
            results.append({
                'timestamp': timestamp_str,
                'game': row['game'].title(),
                'player1': player1_display,
                'player2': player2_display,
                'result': row['result'],
                'probability': probability,
                'commentary': commentary,
                'player1_change': player1_change,
                'player2_change': player2_change,
                'comments': comments
            })
        
        return jsonify({'results': results, 'has_more': has_more})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<team>/recent-results', methods=['GET'])
def get_recent_results(team):
    """Get recent results for a team with pagination"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        
        results_file = os.path.join(DATABASE_DIR, team, 'results.csv')
        
        if not os.path.exists(results_file):
            return jsonify({'results': [], 'has_more': False})
        
        # Read the results CSV
        df = pd.read_csv(results_file)
        
        if df.empty:
            return jsonify({'results': [], 'has_more': False})
        
        # Get pagination parameters
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 25, type=int)
        
        # Sort by timestamp descending and get paginated results
        # Handle both timestamp formats (with and without microseconds)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
        df_sorted = df.sort_values('timestamp', ascending=False)
        
        # Check if there are more results available
        total_results = len(df_sorted)
        has_more = (offset + limit) < total_results
        
        # Get the requested slice
        df_paginated = df_sorted.iloc[offset:offset + limit]
        
        # Format results for frontend
        results = []
        for _, row in df_paginated.iterrows():
            # Format player names for display
            player1_display = format_player_name_for_display(row['player1'])
            player2_display = format_player_name_for_display(row['player2'])
            timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            probability = float(row['probability'])
            
            # Read persisted rating changes from results.csv (if present)
            try:
                p1c = row['player1_change'] if 'player1_change' in df_paginated.columns else None
            except Exception:
                p1c = None
            try:
                p2c = row['player2_change'] if 'player2_change' in df_paginated.columns else None
            except Exception:
                p2c = None
            
            # Normalize to int or None
            def to_int_or_none(v):
                try:
                    import pandas as _pd
                    if v is None or (isinstance(v, float) and _pd.isna(v)):
                        return None
                    return int(round(float(v)))
                except Exception:
                    return None
            player1_change = to_int_or_none(p1c)
            player2_change = to_int_or_none(p2c)
            
            # Generate commentary on the backend
            commentary = _generate_result_commentary(
                player1_display, player2_display, row['result'], probability, timestamp_str
            )
            
            # Parse comments if they exist
            comments = []
            if 'comments' in df_paginated.columns and pd.notna(row['comments']) and row['comments'] != '':
                try:
                    import ast
                    if row['comments'] != '[]':
                        comments_list = ast.literal_eval(row['comments'])
                        if isinstance(comments_list, list):
                            comments = comments_list
                except (ValueError, SyntaxError):
                    # If parsing fails, treat as empty
                    comments = []
            
            results.append({
                'timestamp': timestamp_str,
                'game': row['game'].title(),
                'player1': player1_display,
                'player2': player2_display,
                'result': row['result'],
                'probability': probability,
                'commentary': commentary,
                'player1_change': player1_change,
                'player2_change': player2_change,
                'comments': comments
            })
        
        return jsonify({'results': results, 'has_more': has_more})
        
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
        comment = data.get('comment', '').strip()
        commenter_name = data.get('commenter_name', '').strip()
        
        if not player1 or not player2:
            return jsonify({'error': 'Both players are required'}), 400
        
        if player1 == player2:
            return jsonify({'error': 'Players must be different'}), 400
        
        if result not in ['1-0', '0-1', '1/2-1/2']:
            return jsonify({'error': 'Invalid result format'}), 400
        
        # Validate comment inputs if comment is provided
        if comment and not commenter_name:
            return jsonify({'error': 'Commenter name is required when adding a comment'}), 400
        
        # Convert result to score for main.py
        if result == '1-0':
            score = 1.0
        elif result == '0-1':
            score = 0.0
        else:  # 1/2-1/2
            score = 0.5
        
        # Use the submit_game_with_charts function directly (includes rating changes)
        result_data = submit_game_with_charts(player1, player2, result, game)
        
        if result_data.get('success'):
            response_data = {
                'success': True,
                'message': result_data['message'],
                'game': game,
                'player1': player1,
                'player2': player2,
                'result': result
            }
            
            # Add comment if provided
            if comment and commenter_name:
                comment_result = add_comment_to_result(
                    comment=comment,
                    commenter_name=commenter_name,
                    team=None,
                    offset=0,
                    index=0  # Latest result is at position 0,0
                )
                
                if comment_result.get('success'):
                    response_data['comment_added'] = True
                    response_data['comment'] = comment_result.get('comment')
                    response_data['message'] += ' (with comment)'
                else:
                    # Comment failed but game succeeded - still return success
                    response_data['comment_error'] = comment_result.get('error')
            
            return jsonify(response_data)
        else:
            return jsonify({'error': result_data.get('error', 'Unknown error')}), 500
    
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
        comment = data.get('comment', '').strip()
        commenter_name = data.get('commenter_name', '').strip()

        if not player1 or not player2:
            return jsonify({'error': 'Both players are required'}), 400
        if player1 == player2:
            return jsonify({'error': 'Players must be different'}), 400
        if result not in ['1-0', '0-1', '1/2-1/2']:
            return jsonify({'error': 'Invalid result format'}), 400
        
        # Validate comment inputs if comment is provided
        if comment and not commenter_name:
            return jsonify({'error': 'Commenter name is required when adding a comment'}), 400

        score = 1.0 if result == '1-0' else 0.0 if result == '0-1' else 0.5

        # Use the submit_game_with_charts function directly (includes rating changes)
        result_data = submit_game_with_charts(player1, player2, result, game, team=team)
        
        if result_data.get('success'):
            response_data = {
                'success': True,
                'message': result_data['message'],
                'game': game,
                'team': team
            }
            
            # Add comment if provided
            if comment and commenter_name:
                comment_result = add_comment_to_result(
                    comment=comment,
                    commenter_name=commenter_name,
                    team=team,
                    offset=0,
                    index=0  # Latest result is at position 0,0
                )
                
                if comment_result.get('success'):
                    response_data['comment_added'] = True
                    response_data['comment'] = comment_result.get('comment')
                    response_data['message'] += ' (with comment)'
                else:
                    # Comment failed but game succeeded - still return success
                    response_data['comment_error'] = comment_result.get('error')
            
            return jsonify(response_data)
        else:
            return jsonify({'error': result_data.get('error', 'Unknown error')}), 500
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except PermissionError:
        return jsonify({'error': 'Forbidden: not logged into this team'}), 403
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
    """Serve team game page"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        
        # Check if game directory exists
        game_dir = os.path.join(DATABASE_DIR, team, game)
        if not os.path.exists(game_dir):
            return jsonify({'error': 'Unknown game'}), 404
        
        return send_from_directory(WEB_DIR, 'game.html')
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/games')
def get_available_games():
    """Get list of available games by scanning database directory"""
    try:
        games = []
        
        # Scan main database directory for game folders
        if os.path.exists(DATABASE_DIR):
            for item in os.listdir(DATABASE_DIR):
                item_path = os.path.join(DATABASE_DIR, item)
                if os.path.isdir(item_path) and item not in ['teams']:
                    # Check if it's a valid game directory (has at least one CSV file)
                    csv_files = [f for f in os.listdir(item_path) if f.endswith('.csv')]
                    if csv_files:
                        games.append(item)
        
        # Also scan team directories for additional games
        if os.path.exists(DATABASE_DIR):
            for item in os.listdir(DATABASE_DIR):
                item_path = os.path.join(DATABASE_DIR, item)
                if os.path.isdir(item_path) and item not in ['teams', 'test_data'] and not item.endswith('.csv'):
                    # This might be a team directory
                    for game in os.listdir(item_path):
                        game_path = os.path.join(item_path, game)
                        if os.path.isdir(game_path) and game not in games:
                            csv_files = [f for f in os.listdir(game_path) if f.endswith('.csv')]
                            if csv_files:
                                games.append(game)
        
        # Remove duplicates and sort
        games = sorted(list(set(games)))
        
        # Load game metadata from config file
        game_metadata = {}
        config_file = os.path.join(os.path.dirname(__file__), 'config', 'games.json')
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                game_metadata = config_data.get('games', {})
                defaults = config_data.get('defaults', {})
        except Exception as e:
            print(f"Warning: Could not load games config: {e}")
            # Fallback metadata
            game_metadata = {
                'chess': {'name': 'Chess', 'emoji': '♔'},
                'pingpong': {'name': 'Ping Pong', 'emoji': '🏓'},
                'backgammon': {'name': 'Backgammon', 'emoji': '🎲'}
            }
            defaults = {'emoji': '🎮', 'description': 'Rating system game'}
        
        # Build response with metadata
        games_with_metadata = []
        for game in games:
            metadata = game_metadata.get(game, {})
            games_with_metadata.append({
                'id': game,
                'name': metadata.get('name', game.replace('_', ' ').title()),
                'emoji': metadata.get('emoji', defaults.get('emoji', '🎮')),
                'description': metadata.get('description', defaults.get('description', 'Rating system game')),
                'leaderboardImage': f'{game}_leaderboard.png',
                'ratingsImage': f'{game}_ratings_progress.png'
            })
        
        return jsonify({'games': games_with_metadata})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/undo-last-result', methods=['POST'])
def undo_last_result_main():
    """Undo the last result from the main database"""
    try:
        result = undo_last_result(team=None)
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'undone_result': result['undone_result']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/<team>/undo-last-result', methods=['POST'])
def undo_last_result_team(team):
    """Undo the last result from a specific team's database"""
    try:
        # Validate team access
        assert_team_access(team)
        
        result = undo_last_result(team=team)
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'undone_result': result['undone_result']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    except PermissionError:
        return jsonify({
            'success': False,
            'error': 'Forbidden: not logged into this team'
        }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

def get_probability_matrix(game: str, team: str = None) -> dict:
    """
    Generate a cross-table showing win probabilities between all players.
    Returns dict with player names and probability matrix.
    """
    try:
        # Determine the correct database path
        if team:
            game_dir = os.path.join(DATABASE_DIR, team, game)
        else:
            game_dir = os.path.join(DATABASE_DIR, game)
        
        if not os.path.exists(game_dir):
            return {"error": f"No data found for {game}"}
        
        # Get all player files
        player_files = [f for f in os.listdir(game_dir) if f.endswith('.csv')]
        if not player_files:
            return {"error": f"No players found for {game}"}
        
        # Read current ratings for all players
        players = []
        ratings = {}
        
        for player_file in player_files:
            player_name = player_file[:-4]  # Remove .csv
            file_path = os.path.join(game_dir, player_file)
            
            try:
                data = pd.read_csv(file_path)
                if not data.empty:
                    current_rating = data['rating'].iloc[-1]
                    players.append(player_name)
                    ratings[player_name] = current_rating
            except Exception as e:
                print(f"Error reading {player_file}: {e}")
                continue
        
        if len(players) < 2:
            return {"error": "Need at least 2 players for probability matrix"}
        
        # Sort players by current rating (highest to lowest) for better UX
        players.sort(key=lambda p: ratings[p], reverse=True)
        
        # Generate probability matrix
        matrix = []
        for i, player_a in enumerate(players):
            row = []
            for j, player_b in enumerate(players):
                if i == j:
                    # Same player - probability is undefined, use null
                    probability = None
                else:
                    probability = calculate_elo_probability(ratings[player_a], ratings[player_b])
                    probability = round(probability, 3)  # Round to 3 decimal places
                row.append(probability)
            matrix.append(row)
        
        return {
            "players": players,
            "ratings": ratings,
            "matrix": matrix,
            "game": game
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/probability-matrix/<game>')
def get_probability_matrix_main(game):
    """Get probability matrix for main database"""
    try:
        result = get_probability_matrix(game)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/<team>/probability-matrix/<game>')
def get_probability_matrix_team(team, game):
    """Get probability matrix for team database"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        result = get_probability_matrix(game, team)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except PermissionError:
        return jsonify({'error': 'Forbidden'}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['POST'])
def add_comment_main():
    """Add a comment to a result in the main database"""
    try:
        data = request.get_json()
        timestamp = data.get('timestamp', '').strip()
        comment = data.get('comment', '').strip()
        commenter_name = data.get('commenter_name', '').strip()
        offset = data.get('offset', 0)
        index = data.get('index', 0)
        
        if not comment:
            return jsonify({'error': 'Comment is required'}), 400
            
        if not commenter_name:
            return jsonify({'error': 'Commenter name is required'}), 400
        
        # Use our backend function to add the comment
        result = add_comment_to_result(
            timestamp=timestamp,
            comment=comment, 
            commenter_name=commenter_name, 
            team=None,
            offset=offset,
            index=index
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'comment': result['comment'],
                'timestamp': result.get('timestamp', timestamp)
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<team>/comments', methods=['POST'])
def add_comment_team(team):
    """Add a comment to a result in a team's database"""
    try:
        team = sanitize_team(team)
        assert_team_access(team)
        
        data = request.get_json(force=True)
        timestamp = data.get('timestamp', '').strip()
        comment = data.get('comment', '').strip()
        commenter_name = data.get('commenter_name', '').strip()
        offset = data.get('offset', 0)
        index = data.get('index', 0)
        
        if not comment:
            return jsonify({'error': 'Comment is required'}), 400
            
        if not commenter_name:
            return jsonify({'error': 'Commenter name is required'}), 400
        
        # Use our backend function to add the comment
        result = add_comment_to_result(
            timestamp=timestamp,
            comment=comment, 
            commenter_name=commenter_name, 
            team=team,
            offset=offset,
            index=index
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'comment': result['comment'],
                'timestamp': result.get('timestamp', timestamp),
                'team': team
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 400
    
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except PermissionError:
        return jsonify({'error': 'Forbidden: not logged into this team'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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