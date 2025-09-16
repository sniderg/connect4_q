# othello_bot.py
import math, random, sys
from typing import List, Tuple, Optional

EMPTY, BLACK, WHITE = 0, 1, 2
N = 8
DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def new_board():
    b = [[EMPTY]*N for _ in range(N)]
    b[3][3] = WHITE; b[4][4] = WHITE
    b[3][4] = BLACK; b[4][3] = BLACK
    return b

def in_bounds(r,c): return 0 <= r < N and 0 <= c < N

def pretty(b):
    print("     a b c d e f g h")
    print("   -----------------")
    for r in range(N):
        row = []
        for c in range(N):
            v = b[r][c]
            row.append("." if v==EMPTY else ("●" if v==BLACK else "○"))
        print(f"{r+1:2} | {' '.join(row)}")
    print()

def opponent(p): return BLACK if p==WHITE else WHITE

def line_flips(b, r, c, p, dr, dc):
    flips = []
    rr, cc = r+dr, c+dc
    opp = opponent(p)
    while in_bounds(rr,cc) and b[rr][cc]==opp:
        flips.append((rr,cc))
        rr += dr; cc += dc
    if in_bounds(rr,cc) and b[rr][cc]==p and flips:
        return flips
    return []

def legal_moves(b, p) -> List[Tuple[int,int]]:
    moves = []
    for r in range(N):
        for c in range(N):
            if b[r][c] != EMPTY: continue
            tot = 0
            for dr,dc in DIRS:
                tot += len(line_flips(b,r,c,p,dr,dc))
            if tot > 0:
                moves.append((r,c))
    return moves

def play_move(b, r, c, p) -> List[Tuple[int,int]]:
    """Apply move; return list of flipped disks (for undo). Assumes move is legal."""
    flipped = []
    b[r][c] = p
    for dr,dc in DIRS:
        flips = line_flips(b,r,c,p,dr,dc)
        for (rr,cc) in flips:
            b[rr][cc] = p
        flipped.extend(flips)
    return flipped

def undo_move(b, r, c, p, flipped: List[Tuple[int,int]]):
    opp = opponent(p)
    for (rr,cc) in flipped:
        b[rr][cc] = opp
    b[r][c] = EMPTY

def disk_counts(b):
    black = sum(1 for r in range(N) for c in range(N) if b[r][c]==BLACK)
    white = sum(1 for r in range(N) for c in range(N) if b[r][c]==WHITE)
    empty = N*N - black - white
    return black, white, empty

# --- Heuristic ---
CORNER_CELLS = {(0,0),(0,7),(7,0),(7,7)}
X_CELLS = {(1,1),(1,6),(6,1),(6,6)}  # dangerous early if corner open
C_EDGE = {(0,1),(1,0),(0,6),(1,7),(6,0),(7,1),(6,7),(7,6)}  # near corner

def frontier_count(b, p):
    cnt = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] != p: continue
            # adjacent to empty?
            for dr,dc in DIRS:
                rr,cc = r+dr,c+dc
                if in_bounds(rr,cc) and b[rr][cc]==EMPTY:
                    cnt += 1; break
    return cnt

def evaluate(b, p) -> int:
    me, you = p, opponent(p)
    my_moves = len(legal_moves(b, me))
    opp_moves = len(legal_moves(b, you))
    mobility = 0 if (my_moves+opp_moves)==0 else 100 * (my_moves - opp_moves) // (my_moves + opp_moves)

    # corners and dangerous squares
    my_corners = sum(1 for rc in CORNER_CELLS if b[rc[0]][rc[1]]==me)
    opp_corners = sum(1 for rc in CORNER_CELLS if b[rc[0]][rc[1]]==you)
    corner_score = 25 * (my_corners - opp_corners)

    # X-squares (disc diagonal to an empty corner is bad)
    x_score = 0
    for (xr,xc) in X_CELLS:
        val = b[xr][xc]
        # Penalize occupying X when the adjacent corner is empty (heuristic danger)
        cr = 0 if xr==1 else 7
        cc = 0 if xc==1 else 7
        corner_empty = (b[cr][cc]==EMPTY)
        if corner_empty:
            if val==me: x_score -= 12
            elif val==you: x_score += 12

    # frontier: fewer is better
    my_front = frontier_count(b, me)
    opp_front = frontier_count(b, you)
    frontier = 0 if (my_front+opp_front)==0 else 50 * (opp_front - my_front) // (my_front + opp_front)

    # parity (endgame only)
    black, white, empty = disk_counts(b)
    parity = 0
    if empty <= 10:
        my_disks = black if me==BLACK else white
        opp_disks = white if me==BLACK else black
        parity = 5 * (my_disks - opp_disks)

    # edges (light reward if not adjacent to open corner)
    edge_score = 0
    for c in range(N):
        if b[0][c]==me: edge_score += 2
        elif b[0][c]==you: edge_score -= 2
        if b[7][c]==me: edge_score += 2
        elif b[7][c]==you: edge_score -= 2
    for r in range(N):
        if b[r][0]==me: edge_score += 2
        elif b[r][0]==you: edge_score -= 2
        if b[r][7]==me: edge_score += 2
        elif b[r][7]==you: edge_score -= 2
    # discount “C” cells if adjacent corner is empty
    for (er,ec) in C_EDGE:
        cr = 0 if er in (0,1) else 7
        cc = 0 if ec in (0,1) else 7
        if b[cr][cc]==EMPTY:
            if b[er][ec]==me: edge_score -= 2
            elif b[er][ec]==you: edge_score += 2

    # combine
    return (corner_score + x_score + mobility + frontier + edge_score + parity)

# --- Zobrist hashing + TT ---
random.seed(2025)
Z = [[[random.getrandbits(64) for _ in range(3)] for _ in range(N)] for _ in range(N)]
def hash_board(b):
    h=0
    for r in range(N):
        for c in range(N):
            h ^= Z[r][c][b[r][c]]
    return h
TT = {}  # key -> (depth, score)

def terminal_value(b, max_player) -> Optional[int]:
    m1 = legal_moves(b, BLACK)
    m2 = legal_moves(b, WHITE)
    if not m1 and not m2:  # game over
        black, white, _ = disk_counts(b)
        if max_player==BLACK:
            return 10**7 if black>white else (-10**7 if white>black else 0)
        else:
            return 10**7 if white>black else (-10**7 if black>white else 0)
    return None

# Move ordering: corners first, then by 1-ply eval
def order_moves(b, moves, p):
    def score_move(move):
        r,c = move
        if (r,c) in CORNER_CELLS: return 10_000
        flips = play_move(b, r, c, p)
        s = evaluate(b, p)
        undo_move(b, r, c, p, flips)
        return s
    return sorted(moves, key=score_move, reverse=True)

def alphabeta(b, depth, alpha, beta, max_player, cur_player) -> Tuple[int, Optional[Tuple[int,int]]]:
    tv = terminal_value(b, max_player)
    if tv is not None:
        return tv, None
    if depth == 0:
        return evaluate(b, max_player), None

    h = hash_board(b)
    if h in TT:
        d, s = TT[h]
        if d >= depth:
            return s, None

    moves = legal_moves(b, cur_player)
    if not moves:
        # Pass turn
        score, _ = alphabeta(b, depth-1, alpha, beta, max_player, opponent(cur_player))
        TT[h] = (depth, score)
        return score, None

    best_move = None
    if cur_player == max_player:
        value = -math.inf
        for (r,c) in order_moves(b, moves, cur_player):
            flips = play_move(b, r, c, cur_player)
            score, _ = alphabeta(b, depth-1, alpha, beta, max_player, opponent(cur_player))
            undo_move(b, r, c, cur_player, flips)
            if score > value:
                value, best_move = score, (r,c)
            alpha = max(alpha, value)
            if alpha >= beta: break
    else:
        value = math.inf
        for (r,c) in order_moves(b, moves, cur_player):
            flips = play_move(b, r, c, cur_player)
            score, _ = alphabeta(b, depth-1, alpha, beta, max_player, opponent(cur_player))
            undo_move(b, r, c, cur_player, flips)
            if score < value:
                value, best_move = score, (r,c)
            beta = min(beta, value)
            if alpha >= beta: break

    TT[h] = (depth, int(value))
    return int(value), best_move

def best_move(b, player, depth=5):
    _, mv = alphabeta(b, depth, -math.inf, math.inf, player, player)
    return mv

# --- CLI ---
def parse_move(s: str) -> Optional[Tuple[int,int]]:
    s = s.strip().lower()
    # formats: "d3" or "3 2"
    if len(s) == 2 and s[0] in "abcdefgh" and s[1] in "12345678":
        c = "abcdefgh".index(s[0]); r = int(s[1]) - 1
        return (r,c)
    parts = s.replace(",", " ").split()
    if len(parts)==2 and parts[0].isdigit() and parts[1].isdigit():
        r = int(parts[0]); c = int(parts[1])
        if 0<=r<8 and 0<=c<8: return (r,c)
    return None

def game():
    board = new_board()
    human = BLACK  # you are Black by default
    ai = WHITE
    turn = BLACK
    depth = 5

    print("Othello — you are Black (●). Enter moves like d3 or '2 3'. Bot depth =", depth)
    pretty(board)

    while True:
        m1 = legal_moves(board, turn)
        m2 = legal_moves(board, opponent(turn))
        if not m1 and not m2:
            b,w,_ = disk_counts(board)
            pretty(board)
            if b>w: print("Black wins! 🎉")
            elif w>b: print("White wins! 🤖")
            else: print("Draw.")
            break

        if not m1:
            # pass
            if turn==human:
                print("No legal moves for you; you pass.")
            else:
                print("Bot has no legal moves; it passes.")
            turn = opponent(turn)
            continue

        if turn == human:
            print(f"Your legal moves: {[chr(c+97)+str(r+1) for (r,c) in m1]}")
            mv = None
            while mv is None:
                s = input("Your move: ")
                mv = parse_move(s)
                if mv is None or mv not in m1:
                    print("Illegal/invalid. Try again.")
                    mv = None
            r,c = mv
            flips = play_move(board, r, c, human)
            pretty(board)
        else:
            mv = best_move(board, ai, depth=depth)
            if mv is None:
                print("Bot passes.")
                turn = human
                continue
            r,c = mv
            play_move(board, r, c, ai)
            print(f"Bot plays {chr(c+97)}{r+1}")
            pretty(board)

        turn = opponent(turn)

if __name__ == "__main__":
    try:
        game()
    except KeyboardInterrupt:
        sys.exit(0)
