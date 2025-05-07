import numpy.random as random
import numpy as np
import pandas as pd
from utsuho import HiraganaToKatakanaConverter

class Agent:
    def __init__(self, game, letters_list, f_name='data/words.csv', lf_name='data/letters.csv'):
        self.vowels = ['イ','ウ','ン','シ','ノ','カ','ト','タ','ニ','レ']
        w_bank = pd.read_csv(f_name)
        l_bank = pd.read_csv(lf_name)
        w_bank = w_bank[w_bank['words'].str.len()==game.letters]
        # w_bank['words'] = w_bank['words'].str.upper() #Convert all words to uppercase
        cnv = HiraganaToKatakanaConverter()
        w_bank['words'] = w_bank['words'].apply(cnv.convert) #Convert all words to カタカナ
        w_bank['v-count'] = w_bank['words'].apply(lambda x: ''.join(set(x))).str.count('|'.join(self.vowels)) #Count amount of vowels in words
        # word bank for precise prediction
        self.w_bank = w_bank
        # word bank for letter-nallowing prediction
        self.pw_bank = w_bank[w_bank['words'].apply(lambda w: len(set(w)) == len(w))].copy()
        self.l_bank = l_bank
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.y_letters = {}
        self.g_letters = []
        self.used_letters = []
        self.possible_letters = set(letters_list)
        pd.set_option('display.max_rows', None)

    def has_not_used(word):
        return all(l not in self.possible_letters for l in word)
    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.w_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.w_bank[f'p-{x}'] = self.w_bank['words'].str[x].map(counts)
            pcounts = self.pw_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.pw_bank[f'p-{x}'] = self.pw_bank['words'].str[x].map(pcounts)
    def parse_board(self):
        if self.game.g_count > 0:
            g_hold = []
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

    def choose_action(self):
        self.parse_board()
        nallow_predictions = False
        if len(self.g_letters) > 0:
            self.w_bank = self.w_bank[~self.w_bank['words'].str.contains('|'.join(self.g_letters))]
            self.g_letters = []
            if len(self.g_letters) >= 3 and len(self.w_bank) > 5 :
                nallow_predictions = True
        if len(self.y_letters) > 0:
            y_str = '^' + ''.join(fr'(?=.*{l})' for l in self.y_letters)
            self.w_bank = self.w_bank[self.w_bank['words'].str.contains(y_str)]
            for s, p in self.y_letters.items():
                for i in p:
                    self.w_bank = self.w_bank[self.w_bank['words'].str[i]!=s]
            self.y_letters = {}
        if len(self.used_letters) < 2:
            print("Used letters less than 2: nallow mode")
            nallow_predictions = True
        #Recalculate letter position probability
        self.calc_letter_probs()

        # wide mode prediction 
        self.pw_bank['w-score'] = [1] * len(self.pw_bank)
        pattern = "[" + "".join(self.possible_letters) + "]"
        self.pw_bank = self.pw_bank[self.pw_bank['words'].apply(lambda w: all(l in self.possible_letters for l in w))]
        if len(self.pw_bank) == 0:
            print("nallow predictions have exausted")
            nallow_predictions = False
        else:
            for x in range(self.game.letters):
                self.pw_bank['w-score'] *= self.pw_bank[f'p-{x}']
            mpv_bank = self.pw_bank[self.pw_bank['w-score']==self.pw_bank['w-score'].max()]

        # nallow mode  prediction
        for i, s in enumerate(self.prediction):
            if s != '':
                self.w_bank = self.w_bank[self.w_bank['words'].str[i]==s]
        self.w_bank['w-score'] = [1] * len(self.w_bank)
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.w_bank['w-score'] *= self.w_bank[f'p-{x}']
        # if True not in [True for s in self.prediction if s in self.vowels]:
        #     self.w_bank['w-score'] += self.w_bank['v-count'] / self.game.letters
        mv_bank = self.w_bank[self.w_bank['w-score']==self.w_bank['w-score'].max()]
        # print(mv_bank['w-score'])
        # if self.game.g_count == 0:
        #     result = 'カントウシ'
        # elif self.game.g_count == 1 and len(self.used_letters) < 2:
        #     result = 'ニクタイハ'
        # elif self.game.g_count == 2 and len(self.used_letters) < 2:
        #     result = 'コワレモノ'
        # elif self.game.g_count == 3 and len(self.used_letters) < 2:
        #     result = 'ジョセツキ'
        # else:
        if nallow_predictions :
            print("letter-nallowing mode")
            result = random.choice(mpv_bank['words'].tolist())
        else :
            print("presice mode")
            result = random.choice(mv_bank['words'].tolist())
        return result
