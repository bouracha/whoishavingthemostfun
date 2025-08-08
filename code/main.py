import pandas as pd
from update import *
import argparse
from config import get_k_factor

parser = argparse.ArgumentParser()

parser.add_argument('--game', type=str, help='Which game is being played')
parser.add_argument('--player1', type=str, help='One players name')
parser.add_argument('--player2', type=str, help='One players name')
parser.add_argument('--score', type=float, default=1.0, help='Result, 1.0 means player1 wins')

opt = parser.parse_args()

print("=====================================================================================")

ratings1, ratings2 = read_ratings(opt.player1, opt.player2, opt.game)
rating1, rating2 = ratings1[-1], ratings2[-1]

game = (opt.game or '').lower()
new_rating1, new_rating2 = update(rating1, rating2, opt.score, K=get_k_factor(game))

print(str(opt.player1)+"'s new ratings is "+str(int(new_rating1))+" and "+str(opt.player2)+"'s new ratings is "+str(int(new_rating2)))

write_new_rating(opt.player1, new_rating1, opt.player2, opt.score, opt.game, colour='white')
write_new_rating(opt.player2, new_rating2, opt.player1, (1-opt.score), opt.game, colour='black')

print("=====================================================================================")





