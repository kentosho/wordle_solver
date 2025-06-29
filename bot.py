import numpy.random as random
import numpy as np
import pandas as pd
from utsuho import HiraganaToKatakanaConverter

class Agent:
    def __init__(self, game, f_name='data/words.csv'):
        w_bank = pd.read_csv(f_name)
        w_bank = w_bank[w_bank['words'].str.len()==game.letters]
        cnv = HiraganaToKatakanaConverter()
        w_bank['words'] = w_bank['words'].str.upper() #Convert all words to uppercase
        w_bank['words'] = w_bank['words'].apply(cnv.convert) #Convert all words to カタカナ
        letters_list =  [chr(code) for code in range(0x30A0, 0x31F0)]
        # word bank for precise prediction
        self.w_bank = w_bank
        # word bank for letter-nallowing prediction
        self.pw_bank = w_bank[w_bank['words'].apply(lambda w: len(set(w)) == len(w))].copy()
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.y_letters = {}
        self.g_letters = []
        self.g_max = 0
        self.used_letters = []
        self.possible_letters = set(letters_list)
        self.last_letters = set(letters_list)
        pd.set_option('display.max_rows', None)

    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.w_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.w_bank[f'p-{x}'] = self.w_bank['words'].str[x].map(counts)
            pcounts = self.pw_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.pw_bank[f'p-{x}'] = self.pw_bank['words'].str[x].map(pcounts)
    def parse_board(self):
        if self.game.g_count > 0:
            g_hold = []
            g_num = 0
            for x, c in enumerate(self.game.colours[self.game.g_count - 1]):
                letter = self.game.board[self.game.g_count - 1][x]
                if c == 'Y':
                    if letter not in self.used_letters:
                        self.used_letters.append(letter)
                    if letter not in self.y_letters:
                        self.y_letters[letter] = [x]
                    else:
                        if x not in self.y_letters[letter]:
                            self.y_letters[letter].append(x)
                elif c == 'G':
                    if letter not in self.used_letters:
                        self.used_letters.append(letter)
                    g_num += 1
                    self.prediction[x] = letter
                else:
                    self.possible_letters.discard(letter)
                    if letter in self.prediction:
                        if letter not in self.y_letters:
                            self.y_letters[letter] = [x]
                        else:
                            self.y_letters[letter].append(x)
                    elif letter not in self.g_letters:
                        self.g_letters.append(letter)
            self.possible_letters = self.possible_letters - set(self.used_letters)
            self.g_letters = [l for l in self.g_letters if l not in self.y_letters and l not in self.prediction]
            if g_num > self.g_max : self.g_max = g_num

    def choose_action(self):
        self.parse_board()
        nallow_prediction = False
        manygreen_prediction = False
        y_len = len(self.y_letters)
        if len(self.g_letters) > 0:
            self.w_bank = self.w_bank[~self.w_bank['words'].str.contains('|'.join(self.g_letters))]
            self.g_letters = []
        if len(self.y_letters) > 0:
            y_str = '^' + ''.join(fr'(?=.*{l})' for l in self.y_letters)
            self.w_bank = self.w_bank[self.w_bank['words'].str.contains(y_str)]
            for s, p in self.y_letters.items():
                for i in p:
                    self.w_bank = self.w_bank[self.w_bank['words'].str[i]!=s]
            self.y_letters = {}
        if len(self.used_letters) < 2:
            print("Used letters less than 2: nallow mode")
            nallow_prediction = True
        # print("predictions: " +str(self.prediction))
        if self.g_max >= 3 and y_len == 0 and \
                (self.game.letters - self.g_max) * (self.game.rows - self.game.g_count - 1) \
                < len(self.w_bank) and \
                (self.game.rows - self.game.g_count) > 1:
            print("many green letters: nallow mode")
            nallow_prediction = True
            manygreen_prediction = True
            not_green_letters = set()
            not_green = set()
            for i,s in enumerate(self.prediction):
                if self.prediction[i] == '':
                    not_green.add(i)
            for i,r in self.w_bank.iterrows():
                for j,w in enumerate(r['words']):
                    for k in not_green:
                        not_green_letters.add(r['words'][k])
            
        #Recalculate letter position probability
        self.calc_letter_probs()

        # nallowing possible words bank 
        self.pw_bank['w-score'] = [1] * len(self.pw_bank)
        pattern = "[" + "".join(self.possible_letters) + "]"
        self.pw_bank = self.pw_bank[self.pw_bank['words'].apply(lambda w: all(l in self.possible_letters for l in w))]
        if len(self.pw_bank) == 0:
            print("nallow predictions have exausted")
            nallow_prediction = False
        else:
            for x in range(self.game.letters):
                self.pw_bank['w-score'] *= self.pw_bank[f'p-{x}']
                if manygreen_prediction :
                    self.pw_bank['ng-count'] = [0] * len(self.pw_bank) 
                    self.pw_bank['ng-count'] = self.pw_bank['words'].apply(lambda x: sum(1 for letter in x if letter in not_green_letters))
                    self.pw_bank['w-score'] += self.pw_bank['ng-count']
            mpv_bank = self.pw_bank[self.pw_bank['w-score']==self.pw_bank['w-score'].max()]

        # precise mode  prediction
        for i, s in enumerate(self.prediction):
            if s != '':
                self.w_bank = self.w_bank[self.w_bank['words'].str[i]==s]
        self.w_bank['w-score'] = [1] * len(self.w_bank)
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.w_bank['w-score'] *= self.w_bank[f'p-{x}']
        if nallow_prediction and len(self.w_bank) < (self.game.rows - self.game.g_count) :
            nallow_prediction = False
        mv_bank = self.w_bank[self.w_bank['w-score']==self.w_bank['w-score'].max()]
        
        if nallow_prediction :
            print(str(len(self.w_bank)) + " words left: letter-nallowing mode")
            result = random.choice(mpv_bank['words'].tolist())
        else :
            print(str(len(self.w_bank)) + " words left:  presice mode")
            result = random.choice(mv_bank['words'].tolist())
        return result
