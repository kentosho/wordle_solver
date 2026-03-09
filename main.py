#!/bin/env python
import os
import numpy.random as random
import numpy as np
import pandas as pd
from utsuho import HiraganaToKatakanaConverter
from tqdm import tqdm
from bot import Agent
from wordle import Wordle

ROWS = 10
LETTERS = 5
GAMES = 1000

"""
cnv = HiraganaToKatakanaConverter()

w_bank = pd.read_csv('data/words.csv')
# letters_filename = 'data/letters.csv'

w_bank = w_bank[w_bank['words'].str.len()==LETTERS]
# w_bank['words'] = w_bank['words'].str.upper() #Convert all words to Uppercase
w_bank = w_bank['words'].apply(cnv.convert) # Convert all words to Katakana

letters_set = set()
letters_freq = {}
for word in w_bank['words'] :
    letters_set.update(word)
    for ltr in word:
        if ltr in letters_freq :
            letters_freq[ltr] += 1
        else:
            letters_freq[ltr] = 1
letters_list = list(letters_set)
"""
game = Wordle(
    None,
    rows=ROWS,
    letters=LETTERS)

bot = Agent(game)
for i in range(ROWS):
    suggest = bot.choose_action()
    print(f'SUGGESTED WORD = {suggest}')
    v_inp = input(f'INPUT YOUR GUESS(DEFAULT {suggest}):\n')
    u_inp = input('COLOURS RETURNED [ex. ybggy]?\n')
    if str(u_inp).upper() == 'GGGGG':
        break
    if v_inp == '':
        guess = suggest
    else:
        guess = str(v_inp).upper() 
    game.colours[i] = [s for s in str(u_inp).upper()]
    game.board[i] = [s for s in str(guess).upper()]
    game.g_count += 1
    for x, s in enumerate(game.colours[i]):
        if s == 'Y':
            if guess[x] in bot.y_letters:
                bot.y_letters[guess[x]].append(x)
            else:
                bot.y_letters[guess[x]] = [x]
        elif s == 'B':
            if guess[x] in bot.g_letters:
                bot.g_letters.append(guess[x])
        elif s == 'G':
            bot.prediction[x] = guess[x]
