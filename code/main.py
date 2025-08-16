import pandas as pd
from update import *
import argparse
from config import get_k_factor

parser = argparse.ArgumentParser()

parser.add_argument('--game', type=str, help='Which game is being played')
parser.add_argument('--player1', type=str, help='One players name')
parser.add_argument('--player2', type=str, help='One players name')
parser.add_argument('--score', type=float, default=1.0, help='Result, 1.0 means player1 wins')
parser.add_argument('--team', type=str, default=None, help='Optional team name for multi-tenancy')
parser.add_argument('--timestamp', type=str, default=None, help='Optional timestamp for the game (YYYY-MM-DD HH:MM:SS)')

opt = parser.parse_args()

print("=====================================================================================")

ratings1, ratings2 = read_ratings(opt.player1, opt.player2, opt.game, team=opt.team)
rating1, rating2 = ratings1[-1], ratings2[-1]

game = (opt.game or '').lower()

# Get adjusted K-factors for each player
k_factor1 = get_adjusted_k_factor(opt.player1, opt.game, opt.team)
k_factor2 = get_adjusted_k_factor(opt.player2, opt.game, opt.team)

# Calculate new ratings with individual K-factors
new_rating1, _, probability = update(rating1, rating2, opt.score, K=k_factor1)
_, new_rating2, _ = update(rating1, rating2, 1-opt.score, K=k_factor2)

print(str(opt.player1)+"'s new ratings is "+str(int(new_rating1))+" and "+str(opt.player2)+"'s new ratings is "+str(int(new_rating2)))

write_new_rating(
    opt.player1,
    new_rating1,
    opt.player2,
    opt.score,
    opt.game,
    colour='white',
    team=opt.team,
    timestamp=opt.timestamp,
)
write_new_rating(
    opt.player2,
    new_rating2,
    opt.player1,
    (1-opt.score),
    opt.game,
    colour='black',
    team=opt.team,
    timestamp=opt.timestamp,
)

# Log result to results.csv (works for both team and main database)
# Convert score back to result format for logging
if opt.score == 1.0:
    result_str = "1-0"
elif opt.score == 0.0:
    result_str = "0-1"
else:
    result_str = "1/2-1/2"

log_result_to_team(opt.player1, opt.player2, result_str, opt.game, opt.team, probability, timestamp=opt.timestamp)

print("=====================================================================================")





