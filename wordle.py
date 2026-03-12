from copy import deepcopy


class Wordle:
    def __init__(self, word, rows=6, letters=5):
        self.g_count = 0
        self.word = word
        self.w_hash_table = {}
        if word is not None:
            for x, l in enumerate(word):
                if l in self.w_hash_table:
                    self.w_hash_table[l]['count'] += 1
                    self.w_hash_table[l]['pos'].append(x)
                else:
                    self.w_hash_table[l] = {'count': 1, 'pos': [x]}
        self.rows = rows
        self.letters = letters
        self.board = [['' for _ in range(letters)] for _ in range(rows)]
        self.colours = [['' for _ in range(letters)] for _ in range(rows)]
        self.alph = set(chr(code) for code in range(0x30A0, 0x31F0))

    def is_end(self):
        if self.board[-1] != ['' for _ in range(self.letters)]:
            return True
        return self.game_result()[0]

    def game_result(self):
        for i, r in enumerate(self.board):
            if self.word == ''.join(r):
                return (True, i)
        return (False, 99)

    def update_board(self, u_inp):
        w_hash_table = deepcopy(self.w_hash_table)
        i_hash_table = {}
        for x, l in enumerate(str(u_inp).upper()):
            self.board[self.g_count][x] = l
            if l in i_hash_table:
                i_hash_table[l].append(x)
            else:
                i_hash_table[l] = [x]
        colours = {'G': [], 'B': [], 'Y': []}
        for l in i_hash_table:
            if l in w_hash_table:
                g_hold = [p for p in i_hash_table[l] if p in w_hash_table[l]['pos']]
                remaining_positions = [p for p in i_hash_table[l] if p not in g_hold]
                colours['G'] += g_hold
                y_count = w_hash_table[l]['count'] - len(g_hold)
                colours['Y'] += remaining_positions[:y_count]
                colours['B'] += remaining_positions[y_count:]
            else:
                colours['B'] += i_hash_table[l]
        for c, positions in colours.items():
            for p in positions:
                self.colours[self.g_count][p] = c
        self.g_count += 1

    def valid_guess(self, u_inp):
        return len(u_inp) == 5 and all(s in self.alph for s in str(u_inp).upper())
