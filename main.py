#!/bin/env python
# -*- coding: utf-8 -*-

import re
from bot import Agent
from wordle import Wordle

ROWS = 10
LETTERS = 5

game = Wordle(None, rows=ROWS, letters=LETTERS)
bot = Agent(game)

for i in range(ROWS+10):
    if i == 0 :
        suggest = "キャッシュ"
    else :
        suggest = bot.choose_action()
    print(f'SUGGESTED WORD = {suggest}')
    v_inp = input(f'INPUT YOUR GUESS (DEFAULT {suggest}):\n')
    while(1):
        u_inp = input('COLOURS RETURNED [ex. ybggy]?\n')
        if re.match(r"[BYG]{5}", str(u_inp).upper() ):
            break
        else:
            print('STRING ERROR, INPUT AGAIN')
    if str(u_inp).upper() == 'GGGGG':
        break
    guess = str(v_inp).upper() if v_inp else suggest
    game.board[i] = list(str(guess).upper())
    game.colours[i] = list(str(u_inp).upper())
    game.g_count += 1
