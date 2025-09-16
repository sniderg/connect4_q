import math
import random
from collections import defaultdict
from typing import List, Optional, Tuple

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2

def make_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

def print_board(board):
    for r in range(ROWS-1, -1, -1):
        row = []
        for c in range(COLS):
            v = board[r][c]
            row.append("." if v == EMPTY else ("X" if v == P1 else "O"))
        print(" ".join(row))
    print("0 1 2 3 4 5 6\n")

def legal_moves(board) -> List[int]:
    return [c for c in range(COLS) if board[ROWS-1][c] == EMPTY]

def play_move(board, col, player) -> bool:
    """Drop a piece in column; return True if success."""
    if col < 0 or col >= COLS or board[ROWS-1][col] != EMPTY:
        return False
    for r in range(ROWS):
        if board[r][col] == EMPTY:
            board[r][col] = player
            return True
    return False

def undo_move(board, col):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] != EMPTY:
            board[r][col] = EMPTY
            return

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def check_dir(board, r, c, dr, dc, player):
    cnt = 0
    for _ in range(4):
        if not in_bounds(r, c) or board[r][c] != player:
            return False
        r += dr; c += dc
        cnt += 1
    return cnt == 4

def winner(board) -> Optional[int]:
    dirs = [(1,0),(0,1),(1,1),(1,-1)]
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p == EMPTY: continue
            for dr, dc in dirs:
                if check_dir(board, r, c, dr, dc, p):
                    return p
    return None

def is_full(board) -> bool:
    return all(board[ROWS-1][c] != EMPTY for c in range(COLS))

# Heuristic helpers
def count_window(window: List[int], player: int) -> int:
    opp = P1 if player == P2 else P2
    score = 0
    if window.count(player) == 4: score += 100000
    elif window.count(player) == 3 and window.count(EMPTY) == 1: score += 100
    elif window.count(player) == 2 and window.count(EMPTY) == 2: score += 10
    if window.count(opp) == 3 and window.count(EMPTY) == 1: score -= 120  # block threats
    if window.count(opp) == 4: score -= 100000
    return score

def evaluate(board, player: int) -> int:
    score = 0
    # center control
    center_col = [board[r][COLS//2] for r in range(ROWS)]
    score += center_col.count(player) * 6

    # all windows of 4
    # horizontal
    for r in range(ROWS):
        for c in range(COLS-3):
            window = [board[r][c+i] for i in range(4)]
            score += count_window(window, player)
    # vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            window = [board[r+i][c] for i in range(4)]
            score += count_window(window, player)
    # diag up-right
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += count_window(window, player)
    # diag up-left
    for r in range(ROWS-3):
        for c in range(3, COLS):
            window = [board[r+i][c-i] for i in range(4)]
            score += count_window(window, player)

    return score

# Zobrist hashing for transposition table
random.seed(1337)
Z = [[[random.getrandbits(64) for _ in range(3)] for _ in range(COLS)] for _ in range(ROWS)]
def hash_board(board) -> int:
    h = 0
    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            h ^= Z[r][c][v]
    return h

TT = {}  # hash -> (depth, score)

def terminal_value(board, maximizing_player) -> Optional[int]:
    w = winner(board)
    if w == maximizing_player:
        return 10**9
    elif w is not None:
        return -10**9
    elif is_full(board):
        return 0
    return None

def order_moves(board, player) -> List[int]:
    # Prefer center, then adjacent columns
    order = [3,2,4,1,5,0,6]
    # Light lookahead: prefer immediate winning/blocking moves
    moves = legal_moves(board)
    scored = []
    for c in moves:
        play_move(board, c, player)
        tv = winner(board)
        undo_move(board, c)
        s = 2 if tv == player else 0
        # simulate opponent win to block
        opp = P1 if player == P2 else P2
        block_flag = 0
        for oc in legal_moves(board):
            play_move(board, oc, opp)
            if winner(board) == opp:
                block_flag = 1
            undo_move(board, oc)
            if block_flag: break
        scored.append((s + block_flag, c))
    # base on template order to break ties
    scored.sort(key=lambda x: (-x[0], order.index(x[1]) if x[1] in order else 99))
    return [c for _, c in scored]

def alphabeta(board, depth, alpha, beta, maximizing_player, current_player) -> Tuple[int, Optional[int]]:
    tv = terminal_value(board, maximizing_player)
    if tv is not None:
        return tv, None
    if depth == 0:
        return evaluate(board, maximizing_player), None

    h = hash_board(board)
    if h in TT:
        d, s = TT[h]
        if d >= depth:
            return s, None

    best_col = None
    if current_player == maximizing_player:
        value = -math.inf
        for col in order_moves(board, current_player):
            play_move(board, col, current_player)
            score, _ = alphabeta(board, depth-1, alpha, beta, maximizing_player, P1 if current_player==P2 else P2)
            undo_move(board, col)
            if score > value:
                value, best_col = score, col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = math.inf
        for col in order_moves(board, current_player):
            play_move(board, col, current_player)
            score, _ = alphabeta(board, depth-1, alpha, beta, maximizing_player, P1 if current_player==P2 else P2)
            undo_move(board, col)
            if score < value:
                value, best_col = score, col
            beta = min(beta, value)
            if alpha >= beta:
                break

    TT[h] = (depth, int(value))
    return int(value), best_col

def best_move(board, player, depth=6) -> int:
    _, move = alphabeta(board, depth, -math.inf, math.inf, player, player)
    if move is None:
        # no legal move fallback
        ms = legal_moves(board)
        return ms[0] if ms else -1
    return move

def play_cli():
    board = make_board()
    human = P1  # you are X
    ai = P2     # bot is O
    turn = P1
    depth = 6

    print("Connect 4 — you are 'X' (Player 1). Enter a column 0–6. Bot depth =", depth)
    print_board(board)

    while True:
        if turn == human:
            try:
                col = int(input("Your move (0–6): ").strip())
            except Exception:
                print("Enter an integer 0–6.")
                continue
            if not play_move(board, col, human):
                print("Illegal move. Try again.")
                continue
        else:
            col = best_move(board, ai, depth=depth)
            play_move(board, col, ai)
            print(f"Bot plays column {col}")

        print_board(board)
        w = winner(board)
        if w == human:
            print("You win! 🎉")
            break
        elif w == ai:
            print("Bot wins! 🤖")
            break
        elif is_full(board):
            print("Draw.")
            break
        turn = P1 if turn == P2 else P2

if __name__ == "__main__":
    play_cli()
