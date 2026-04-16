# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Japanese Katakana Wordle solver. It plays the Wordle game using 5-character Katakana words. The word bank (`data/words.csv`) contains Japanese words stored in Katakana. The game logic mirrors standard Wordle: G=green (correct position), Y=yellow (wrong position), B=black/grey (not in word).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Note: `requirements.txt` has a typo — `tdqm` should be `tqdm`. Install manually if needed:
```bash
pip install pandas numpy tqdm utsuho
```

## Running

```bash
# Game Assist mode (interactive, helps you play on the actual Wordle site)
python3 main.py

# Test with a specific word (automated solver loop)
python3 main.py
```

The current `main.py` runs a single-game assist loop (not the full menu from README). It prompts for guesses and color feedback in the format `ybggy` (lowercase or uppercase accepted).

## Architecture

- **`wordle.py` — `Wordle` class**: Game state. Tracks the board (guesses), colour results, and the target word. `update_board()` computes G/Y/B colours given a guess. `valid_guess()` checks Katakana alphabet validity (Unicode range `0x30A0–0x31F0`).

- **`bot.py` — `Agent` class**: Solver logic. Loads `data/words.csv`, converts words to uppercase Katakana via `utsuho.HiraganaToKatakanaConverter`. Uses two word banks:
  - `w_bank`: full word bank for precise prediction (filters by known green positions and yellow/black constraints)
  - `pw_bank`: subset with all-unique letters for "nallowing" (narrowing) mode

  Strategy in `choose_action()`:
  1. **Nallow mode**: Used when fewer than 2 letters are known, or when many greens exist but candidates remain. Picks from `pw_bank` by letter-position probability to maximize information.
  2. **Precise mode**: Filters `w_bank` by known constraints and picks highest-scoring candidate.

- **`data/words.csv`**: The word bank. One word per row under the `words` column, in Katakana, 5-character entries used for gameplay.

- **`main.py`**: Entry point for game assist mode. Manually updates `bot.y_letters`, `bot.g_letters`, and `bot.prediction` based on user colour input (uses uppercase B/Y/G).

## Key Notes

- The `Wordle` class `alph` and `Agent` `letters_list` cover the full Katakana Unicode block (`0x30A0–0x31F0`), not just standard Katakana.
- `main.py` currently bypasses `wordle.update_board()` and manually parses colours — this differs from the automated test flow that would use `update_board()`.
- `hoge.py` is a scratch/test script for the `utsuho` converter, not part of the main app.
- `data/make_unique.py` is a utility to deduplicate the word list.
