#!/usr/bin/env python3
"""
Player Management Script - Backend Only
Safe player deletion with confirmation prompts and chart regeneration.
"""

import sys
import os
import subprocess

try:
    from update import delete_player, make_new_player
except ImportError:
    print("❌ Error: Could not import update functions. Make sure you're running from the code directory.")
    sys.exit(1)

def list_players(game):
    """List all players for a given game."""
    database_path = "database" if os.path.exists("database") else "../database"
    game_path = f"{database_path}/{game}"
    
    if not os.path.exists(game_path):
        print(f"❌ Game '{game}' directory not found")
        return []
    
    players = []
    for file in os.listdir(game_path):
        if file.endswith('.csv'):
            players.append(file[:-4])  # Remove .csv extension
    
    return sorted(players)

def confirm_deletion(player_name, game):
    """Ask for confirmation before deleting a player."""
    print(f"\n⚠️  WARNING: You are about to PERMANENTLY DELETE player '{player_name}' from game '{game}'")
    print("   This will remove ALL their rating history and cannot be undone.")
    print(f"   Player file: database/{game}/{player_name}.csv")
    
    while True:
        response = input(f"\nType '{player_name}' to confirm deletion (or 'cancel' to abort): ").strip()
        
        if response.lower() == 'cancel':
            print("❌ Deletion cancelled")
            return False
        elif response == player_name:
            print("✅ Deletion confirmed")
            return True
        else:
            print(f"❌ Please type exactly '{player_name}' or 'cancel'")

def regenerate_charts(game):
    """Regenerate leaderboard and rating charts after player deletion."""
    print(f"\n📊 Regenerating charts for {game}...")
    
    try:
        # Generate leaderboard JSON
        print(f"  📈 Generating leaderboard...")
        subprocess.run([sys.executable, 'leaderboard.py', game, '--json'], check=True)
        
        # Generate rating charts for all remaining players
        database_path = "database" if os.path.exists("database") else "../database"
        game_path = f"{database_path}/{game}"
        
        if os.path.exists(game_path):
            csv_files = [f"{game_path}/{f}" for f in os.listdir(game_path) if f.endswith('.csv')]
            if csv_files:
                print(f"  📊 Generating rating progress JSON...")
                subprocess.run([sys.executable, 'graph.py'] + csv_files + ['--json'], check=True)
            else:
                print(f"  ℹ️  No players remaining in {game}")
        
        print("✅ Charts regenerated successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error regenerating charts: {e}")

def main():
    if len(sys.argv) < 2:
        print("🎮 Player Management Tool - Backend Only")
        print("\nUsage:")
        print("  python3 manage_players.py list <game>")
        print("  python3 manage_players.py delete <game> <player_name>")
        print("\nExamples:")
        print("  python3 manage_players.py list chess")
        print("  python3 manage_players.py delete chess testplayer")
        print("\nAvailable games: chess, pingpong, backgammon")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        if len(sys.argv) != 3:
            print("❌ Usage: python3 manage_players.py list <game>")
            sys.exit(1)
        
        game = sys.argv[2].lower()
        players = list_players(game)
        
        if not players:
            print(f"📭 No players found for game '{game}'")
        else:
            print(f"🎮 Players in '{game}' ({len(players)} total):")
            for i, player in enumerate(players, 1):
                print(f"  {i:2d}. {player}")
    
    elif command == 'delete':
        if len(sys.argv) != 4:
            print("❌ Usage: python3 manage_players.py delete <game> <player_name>")
            sys.exit(1)
        
        game = sys.argv[2].lower()
        player_name = sys.argv[3]
        
        # List current players first
        players = list_players(game)
        if not players:
            print(f"📭 No players found for game '{game}'")
            sys.exit(1)
        
        if player_name not in players:
            print(f"❌ Player '{player_name}' not found in game '{game}'")
            print(f"Available players: {', '.join(players)}")
            sys.exit(1)
        
        print(f"🎮 Current players in '{game}': {', '.join(players)}")
        
        # Confirm deletion
        if confirm_deletion(player_name, game):
            # Delete the player
            success = delete_player(player_name, game)
            
            if success:
                # Regenerate charts
                regenerate_charts(game)
                
                # Show updated player list
                remaining_players = list_players(game)
                if remaining_players:
                    print(f"\n🎮 Remaining players in '{game}': {', '.join(remaining_players)}")
                else:
                    print(f"\n📭 No players remaining in '{game}'")
            else:
                print("❌ Player deletion failed")
                sys.exit(1)
        else:
            sys.exit(0)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, delete")
        sys.exit(1)

if __name__ == "__main__":
    main()