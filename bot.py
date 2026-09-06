import numpy.random as random
import pandas as pd
import os
from utsuho import HiraganaToKatakanaConverter

COND_NUM=20
pd.set_option('display.max_rows', None)


class Agent:
    def __init__(self, game, f_name='data/words.csv'):
        real_path = os.path.realpath(__file__)
        data_path = os.path.dirname(real_path) + "/" + f_name
        w_bank = pd.read_csv(data_path)
        w_bank = w_bank[w_bank['words'].str.len() == game.letters] 
        cnv = HiraganaToKatakanaConverter()
        w_bank['words'] = w_bank['words'].str.upper().apply(cnv.convert)
        letters_list = [chr(code) for code in range(0x30A0, 0x31F0)]
        self.w_bank = w_bank
        self.pw_bank = w_bank[w_bank['words'].apply(lambda w: len(set(w)) == len(w))].copy()
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.y_letters = {}
        self.g_letters = []
        self.g_max = 0
        self.used_letters = []
        self.possible_letters = set(letters_list)

    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.w_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.w_bank[f'p-{x}'] = self.w_bank['words'].str[x].map(counts)
            pcounts = self.pw_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.pw_bank[f'p-{x}'] = self.pw_bank['words'].str[x].map(pcounts)

    def parse_board(self):
        if self.game.g_count == 0:
            return
        g_num = 0
        row = self.game.g_count - 1
        for x, c in enumerate(self.game.colours[row]):
            letter = self.game.board[row][x]
            if c == 'Y':
                if letter not in self.used_letters:
                    self.used_letters.append(letter)
                self.y_letters.setdefault(letter, [])
                if x not in self.y_letters[letter]:
                    self.y_letters[letter].append(x)
            elif c == 'G':
                if letter not in self.used_letters:
                    self.used_letters.append(letter)
                g_num += 1
                self.prediction[x] = letter
            else:  # B
                self.possible_letters.discard(letter)
                if letter in self.prediction:
                    self.y_letters.setdefault(letter, [])
                    self.y_letters[letter].append(x)
                elif letter not in self.g_letters:
                    self.g_letters.append(letter)
        self.possible_letters -= set(self.used_letters)
        self.g_letters = [l for l in self.g_letters if l not in self.y_letters and l not in self.prediction]
        if g_num > self.g_max:
            self.g_max = g_num

    def choose_action(self):
        self.parse_board()
        narrow_prediction = False
        manygreen_prediction = False
        y_len = len(self.y_letters)

        if self.g_letters:
            self.w_bank = self.w_bank[~self.w_bank['words'].str.contains('|'.join(self.g_letters))]
            self.g_letters = []
        if self.y_letters:
            y_str = '^' + ''.join(fr'(?=.*{l})' for l in self.y_letters)
            self.w_bank = self.w_bank[self.w_bank['words'].str.contains(y_str)]
            for s, positions in self.y_letters.items():
                for i in positions:
                    self.w_bank = self.w_bank[self.w_bank['words'].str[i] != s]
            self.y_letters = {}

        if len(self.used_letters) < 2:
            print("Used letters less than 2: narrow mode")
            narrow_prediction = True

        not_green = {}
        if self.g_max >= 2 and y_len == 0 and \
                (self.game.letters - self.g_max) * (self.game.rows - self.game.g_count - 1) \
                < len(self.w_bank) and \
                (self.game.rows - self.game.g_count) > 1:
            print("Many green letters: non-green letter narrow mode")
            narrow_prediction = True
            manygreen_prediction = True
            empty_positions = {i for i, s in enumerate(self.prediction) if s == ''}
            for _, bank_row in self.w_bank.iterrows():
                for j, l in enumerate(bank_row['words']):
                    if j in empty_positions:
                        not_green[l] = not_green.get(l, 0) + 1

        self.calc_letter_probs()

        self.pw_bank['w-score'] = 1.0
        self.pw_bank['ng-count'] = 0
        self.pw_bank = self.pw_bank[self.pw_bank['words'].apply(
            lambda w: all(l in self.possible_letters for l in w))]
        if len(self.pw_bank) == 0:
            print("Narrow predictions exhausted")
            narrow_prediction = False
        else:
            for x in range(self.game.letters):
                self.pw_bank['w-score'] *= self.pw_bank[f'p-{x}']
            if manygreen_prediction:
                self.pw_bank['ng-count'] = self.pw_bank['words'].apply(
                    lambda w: sum(not_green.get(l, 0) for l in w))
            self.pw_bank['w-score'] += self.pw_bank['ng-count']
            mpv_bank = self.pw_bank[self.pw_bank['w-score'] == self.pw_bank['w-score'].max()]

        for i, s in enumerate(self.prediction):
            if s != '':
                self.w_bank = self.w_bank[self.w_bank['words'].str[i] == s]
        self.w_bank['w-score'] = 1.0
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.w_bank['w-score'] *= self.w_bank[f'p-{x}']
        if narrow_prediction and len(self.w_bank) < (self.game.rows - self.game.g_count):
            narrow_prediction = False
        mv_bank = self.w_bank[self.w_bank['w-score'] == self.w_bank['w-score'].max()]

        cand_words = self.w_bank['words'].head(COND_NUM).tolist()
        for i in range(0, len(cand_words), 5):
            print(cand_words[i:i+5])

        if narrow_prediction:
            print(f"{len(self.w_bank)} words left: narrow mode")
            return random.choice(mpv_bank['words'].tolist())
        else:
            print(f"{len(self.w_bank)} words left: precise mode")
            return random.choice(mv_bank['words'].tolist())
