import numpy as np
import pandas as pd
from datetime import datetime
import argparse
import os

def update(rating1, rating2, score, K: int = 40):

    score1 = score
    score2 = 1 - score

    ratingDifference = np.abs(rating1 - rating2)

    probabilityOfWeakerPlayerWinning = (1.0 / (1.0 + (10 ** ((ratingDifference * 1.0/ 400)))))

    probabilityOfStrongerPlayerWinning = 1 - probabilityOfWeakerPlayerWinning

    if (rating1 > rating2):
        prob_of_1_winning = probabilityOfStrongerPlayerWinning
        prob_of_2_winning = probabilityOfWeakerPlayerWinning
    else:
        prob_of_1_winning = probabilityOfWeakerPlayerWinning
        prob_of_2_winning = probabilityOfStrongerPlayerWinning

    print("Probability of White winning: {:.5f}".format(prob_of_1_winning))
    rating_change1 = (score1 - prob_of_1_winning) * K
    rating_change2 = (score2 - prob_of_2_winning) * K

    if np.abs(rating_change1) < 1:
        rating_change1 = rating_change1/np.abs(rating_change1)
    if np.abs(rating_change2) < 1:
        rating_change2 = rating_change2/np.abs(rating_change2)

    newRating1 = rating1 + rating_change1
    newRating2 = rating2 + rating_change2

    return round(newRating1), round(newRating2)



def write_new_rating(player, new_rating, opponent, result, game='chess', colour='white'):
    now = datetime.now()
    df = pd.DataFrame(np.array(np.expand_dims((new_rating, opponent, result, colour, now), axis=0)))
    with open(f'../database/{game}/{player}.csv', 'a') as f:
        df.to_csv(f, header=False, index=False)


def read_ratings(player1, player2, game='chess'):
    data1 = pd.read_csv(f'../database/{game}/{player1}.csv')
    data2 = pd.read_csv(f'../database/{game}/{player2}.csv')

    rating1 = np.array(data1['rating'])
    rating2 = np.array(data2['rating'])

    return rating1, rating2

def make_new_player(player_name='default', game='chess'):
    import os
    
    # Determine the correct path based on where we're running from
    if os.path.exists('database'):
        # Running from root directory (server context)
        file_path = f'database/{game}/{player_name}.csv'
        database_dir = f'database/{game}'
    else:
        # Running from code directory (command line context)
        file_path = f'../database/{game}/{player_name}.csv'
        database_dir = f'../database/{game}'
    
    # Ensure the game directory exists
    os.makedirs(database_dir, exist_ok=True)
    
    # Only create new player if file doesn't exist
    if not os.path.exists(file_path):
        head = np.array(['rating', 'opponent', 'result', 'colour', 'timestamp'])
        df = pd.DataFrame(np.array(np.expand_dims((1200.0, 'no opponent', 0, 'no colour', 'beginning of time'), axis=0)))
        df.to_csv(file_path, header=head, index=False)
        print(f"Created new player '{player_name}' for game '{game}'")
    else:
        print(f"Player '{player_name}' already exists for game '{game}' - skipping creation")

def delete_player(player_name, game='chess'):
    """
    Completely delete a player from the specified game.
    This removes their CSV file and all their rating history.
    
    Args:
        player_name (str): Name of the player to delete
        game (str): The game name (e.g., 'chess', 'pingpong', 'backgammon')
    
    Returns:
        bool: True if player was deleted successfully, False otherwise
    """
    # Determine the correct path (database/ or ../database/)
    database_path = "database" if os.path.exists("database") else "../database"
    file_path = f"{database_path}/{game}/{player_name}.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ Player '{player_name}' not found for game '{game}'")
        return False
    
    try:
        # Remove the player's CSV file
        os.remove(file_path)
        print(f"✅ Player '{player_name}' completely deleted from game '{game}'")
        print(f"   Removed file: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting player '{player_name}': {e}")
        return False

def delete_last_entry(game, players):
    """
    Delete the last entry for each specified player in the given game.
    
    Args:
        game (str): The game name (e.g., 'chess', 'pingpong')
        players (list): List of player names to delete last entry for
    """
    for player in players:
        file_path = f"../database/{game}/{player}.csv"
        
        if not os.path.exists(file_path):
            print(f"Warning: Player '{player}' file not found for game '{game}'")
            continue
            
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Check if there are entries to delete (more than just the initial entry)
            if len(df) <= 1:
                print(f"Warning: Player '{player}' has no game entries to delete (only initial rating remains)")
                continue
                
            # Remove the last row (most recent game)
            df = df.iloc[:-1]
            
            # Save the updated data back to the file
            df.to_csv(file_path, index=False)
            print(f"Deleted last entry for player '{player}' in game '{game}'")
            
        except Exception as e:
            print(f"Error deleting last entry for player '{player}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ELO rating system utilities')
    parser.add_argument('--delete_last_entry', action='store_true', 
                       help='Delete the last entry for specified players')
    parser.add_argument('--delete_player', action='store_true',
                       help='Completely delete player(s) and all their data')
    parser.add_argument('--new_player', action='store_true',
                       help='Create new player(s) for the specified game')
    parser.add_argument('game', type=str, help='Game name (e.g., chess, pingpong)')
    parser.add_argument('players', nargs='+', help='Player names')
    
    args = parser.parse_args()
    
    if args.delete_last_entry:
        delete_last_entry(args.game, args.players)
    elif args.delete_player:
        for player in args.players:
            delete_player(player, args.game)
    elif args.new_player:
        for player in args.players:
            make_new_player(player, args.game)
    else:
        print("Usage:")
        print("  Create new player(s): python3 update.py --new_player <game> <player1> [player2] ...")
        print("  Delete last entry: python3 update.py --delete_last_entry <game> <player1> [player2] ...")
        print("  Delete player(s): python3 update.py --delete_player <game> <player1> [player2] ...")
        print("")
        print("Examples:")
        print("  python3 update.py --new_player chess anthony")
        print("  python3 update.py --new_player pingpong gavin eve dean")
        print("  python3 update.py --delete_last_entry chess dean gavin")
        print("  python3 update.py --delete_player chess testplayer")