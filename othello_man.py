# othello_bitboard.py
import math, sys
from typing import Optional, Tuple, List

# --- Bitboard layout ---
# Bit 0 = a1 (bottom-left), bit 7 = h1, bit 56 = a8, bit 63 = h8
ALL   = 0xFFFFFFFFFFFFFFFF
EMPTY = 0

# Files for wrap-safe shifts
NOT_A = 0xFEFEFEFEFEFEFEFE  # ~A-file
NOT_H = 0x7F7F7F7F7F7F7F7F  # ~H-file

# Shifts with masking to prevent wrap
def N(bb):  return (bb << 8)  & ALL
def S(bb):  return (bb >> 8)
def E(bb):  return ((bb & NOT_H) << 1) & ALL
def W(bb):  return ((bb & NOT_A) >> 1)
def NE(bb): return ((bb & NOT_H) << 9) & ALL
def NW(bb): return ((bb & NOT_A) << 7) & ALL
def SE(bb): return ((bb & NOT_H) >> 7)
def SW(bb): return ((bb & NOT_A) >> 9)

DIRS = (N, S, E, W, NE, NW, SE, SW)

# Masks for features
CORNER = (1<<0) | (1<<7) | (1<<56) | (1<<63)
X_SQ   = (1<<9) | (1<<14) | (1<<49) | (1<<54)      # b2,g2,b7,g7 (diag to corners)
C_SQ   = (1<<1)|(1<<8)|(1<<6)|(1<<15)|(1<<48)|(1<<57)|(1<<55)|(1<<62)  # "C" near corners
EDGE_RANKS = (0xFF) | (0xFF<<56)
EDGE_FILES = (0x0101010101010101) | (0x8080808080808080)

def popcnt(x:int)->int: return x.bit_count()

def start_position()->Tuple[int,int]:
    black = (1<<28) | (1<<35)  # e4, d5 in our coords (remember a1=bit0)
    white = (1<<27) | (1<<36)  # d4, e5
    return black, white

def pretty(black:int, white:int):
    print("     a b c d e f g h")
    print("   -----------------")
    for r in range(8):
        row = []
        for c in range(8):
            bit = 1 << (r*8 + c)
            if black & bit: row.append("●")
            elif white & bit: row.append("○")
            else: row.append(".")
        print(f"{r+1:2} | {' '.join(row)}")
    print()

def opponent(p:int)->int:
    return 2 if p==1 else 1

def legal_moves(P:int, O:int)->int:
    """Return a bitboard of legal moves for side with stones P vs opponent O."""
    empty = ~(P | O) & ALL
    moves = 0
    for sh in DIRS:
        t = sh(P) & O
        # extend through opponent stones (max 6 steps on 8x8)
        t |= sh(t) & O
        t |= sh(t) & O
        t |= sh(t) & O
        t |= sh(t) & O
        t |= sh(t) & O
        moves |= sh(t) & empty
    return moves

def flips_in_dir(move:int, P:int, O:int, sh)->int:
    """Compute flips in one direction for placing 'move' (single-bit) by P vs O."""
    x = sh(move) & O
    captured = 0
    while x:
        captured |= x
        x2 = sh(x)
        if x2 & P:
            return captured
        if x2 & O:
            x = x2
            continue
        break
    return 0

def apply_move(move:int, P:int, O:int) -> Tuple[int,int]:
    """Apply move (single-bit) for side P vs O. Return new (P,O). Assumes move is legal."""
    flips = 0
    for sh in DIRS:
        flips |= flips_in_dir(move, P, O, sh)
    P_new = P | move | flips
    O_new = O & ~flips
    return P_new, O_new

def parse_move(s:str)->Optional[int]:
    s = s.strip().lower()
    if len(s)==2 and s[0] in "abcdefgh" and s[1] in "12345678":
        c = ord(s[0]) - 97
        r = int(s[1]) - 1
        return 1 << (r*8 + c)
    parts = s.replace(",", " ").split()
    if len(parts)==2 and parts[0].isdigit() and parts[1].isdigit():
        r = int(parts[0]); c = int(parts[1])
        if 0<=r<8 and 0<=c<8: return 1 << (r*8 + c)
    return None

def list_moves(mask:int)->List[str]:
    out=[]
    while mask:
        lsb = mask & -mask
        idx = (lsb.bit_length()-1)
        r,c = divmod(idx,8)
        out.append(f"{chr(c+97)}{r+1}")
        mask ^= lsb
    return out

# --- Evaluation: mobility + corners + frontier + X/C awareness + light edges + endgame parity ---
def frontier_count(bb:int, empties:int)->int:
    # Count discs adjacent to an empty square
    adj_empty = (N(empties)|S(empties)|E(empties)|W(empties)|NE(empties)|NW(empties)|SE(empties)|SW(empties))
    return popcnt(bb & adj_empty)

def evaluate(P:int, O:int)->int:
    empties = ~(P|O) & ALL

    # Mobility
    my_moves  = popcnt(legal_moves(P,O))
    op_moves  = popcnt(legal_moves(O,P))
    mobility  = 0 if my_moves+op_moves==0 else 100 * (my_moves - op_moves) // (my_moves + op_moves)

    # Corners
    my_corners  = popcnt(P & CORNER)
    op_corners  = popcnt(O & CORNER)
    corner_score = 25 * (my_corners - op_corners)

    # X/C danger only if corresponding corner empty
    x_score = 0
    # Map each X to its corner
    pairs = [
        (1<<9,  1<<0), (1<<14, 1<<7),
        (1<<49, 1<<56),(1<<54, 1<<63)
    ]
    for xbit, cbit in pairs:
        corner_empty = (cbit & (P|O)) == 0
        if corner_empty:
            if P & xbit: x_score -= 12
            if O & xbit: x_score += 12

    c_score = 0
    # Each C next to its corner; penalize if corner empty
    c_pairs = [
        (1<<1, 1<<0),(1<<8, 1<<0),
        (1<<6, 1<<7),(1<<15,1<<7),
        (1<<48,1<<56),(1<<57,1<<56),
        (1<<55,1<<63),(1<<62,1<<63),
    ]
    for cbit, corner in c_pairs:
        if (corner & (P|O)) == 0:
            if P & cbit: c_score -= 2
            if O & cbit: c_score += 2

    # Frontier (fewer is better)
    my_front = frontier_count(P, empties)
    op_front = frontier_count(O, empties)
    frontier = 0 if my_front+op_front==0 else 50 * (op_front - my_front) // (my_front + op_front)

    # Light edge value
    edge_score = 2 * (popcnt(P & (EDGE_RANKS|EDGE_FILES)) - popcnt(O & (EDGE_RANKS|EDGE_FILES)))

    # Parity late game
    empty_n = popcnt(empties)
    parity = 0
    if empty_n <= 10:
        parity = 5 * (popcnt(P) - popcnt(O))

    return corner_score + x_score + c_score + mobility + frontier + edge_score + parity

# --- Alpha-beta with simple TT ---
from functools import lru_cache

def key_for(P:int,O:int,player:int,depth:int)->Tuple[int,int,int,int]:
    return (P, O, player, depth)

TT = {}  # dict[(P,O,player,depth)] = score

def alphabeta(P:int, O:int, depth:int, alpha:int, beta:int, max_player:int, cur_player:int)->Tuple[int, Optional[int]]:
    # Terminal: no moves for both sides
    my_moves_mask = legal_moves(P,O)
    op_moves_mask = legal_moves(O,P)
    if (my_moves_mask==0 and op_moves_mask==0):
        # game over -> exact disc diff for max_player
        my = popcnt(P) if max_player==1 else popcnt(O)
        op = popcnt(O) if max_player==1 else popcnt(P)
        return (10**7 if my>op else (-10**7 if op>my else 0)), None
    if depth == 0:
        return evaluate(P,O) if max_player==1 else evaluate(O,P), None

    k = key_for(P,O,cur_player,depth)
    if k in TT:
        return TT[k], None

    # If current player has no moves, pass
    if cur_player==1:
        moves_mask = my_moves_mask
        PP, OO = P, O
    else:
        moves_mask = op_moves_mask
        PP, OO = O, P

    if moves_mask == 0:
        score, _ = alphabeta(P, O, depth-1, alpha, beta, max_player, opponent(cur_player))
        TT[k] = score
        return score, None

    # Move ordering: corners first, then 1-ply eval
    ordered: List[int] = []
    mm = moves_mask
    while mm:
        m = mm & -mm
        mm ^= m
        ordered.append(m)
    corners = [m for m in ordered if m & CORNER]
    non_corners = [m for m in ordered if not (m & CORNER)]

    def one_ply_score(move:int)->int:
        p_after, o_after = apply_move(move, PP, OO)
        return evaluate(p_after, o_after)

    non_corners.sort(key=one_ply_score, reverse=True)
    ordered = corners + non_corners

    best_move = None
    if cur_player == max_player:
        value = -math.inf
        for m in ordered:
            if cur_player==1:
                P2, O2 = apply_move(m, P, O)
            else:
                # play as the "current" perspective then swap back
                o2, p2 = apply_move(m, O, P)
                P2, O2 = p2, o2
            sc, _ = alphabeta(P2, O2, depth-1, alpha, beta, max_player, opponent(cur_player))
            if sc > value:
                value, best_move = sc, m
            alpha = max(alpha, value)
            if alpha >= beta: break
    else:
        value = math.inf
        for m in ordered:
            if cur_player==1:
                P2, O2 = apply_move(m, P, O)
            else:
                o2, p2 = apply_move(m, O, P)
                P2, O2 = p2, o2
            sc, _ = alphabeta(P2, O2, depth-1, alpha, beta, max_player, opponent(cur_player))
            if sc < value:
                value, best_move = sc, m
            beta = min(beta, value)
            if alpha >= beta: break

    TT[k] = int(value)
    return int(value), best_move

def best_move(P:int, O:int, player:int, depth:int=5)->Optional[int]:
    TT.clear()
    score, move = alphabeta(P, O, depth, -math.inf, math.inf, player, player)
    return move

# --- CLI game loop ---
def game():
    black, white = start_position()
    player = 1  # 1=Black (●), 2=White (○)
    depth = 7

    print("Othello (Bitboard) — you are Black (●). Enter moves like d3 or '2 3'. Bot depth =", depth)
    pretty(black, white)

    while True:
        my_moves = legal_moves(black, white)
        op_moves = legal_moves(white, black)
        if my_moves==0 and op_moves==0:
            pretty(black, white)
            b, w = popcnt(black), popcnt(white)
            if b>w: print("Black wins! 🎉")
            elif w>b: print("White wins! 🤖")
            else: print("Draw.")
            break

        # Human (Black)
        if my_moves:
            lm = list_moves(my_moves)
            print(f"Your legal moves: {lm}")
            mv = None
            while mv is None:
                s = input("Your move: ")
                bit = parse_move(s)
                if bit is None or (bit & my_moves) == 0:
                    print("Illegal/invalid. Try again.")
                else:
                    mv = bit
            black, white = apply_move(mv, black, white)
            pretty(black, white)
        else:
            print("You have no legal moves. You pass.")

        # Bot (White)
        op_moves = legal_moves(white, black)
        if op_moves:
            mv = best_move(white, black, player=2, depth=depth)
            # safety fallback
            if mv is None or (mv & op_moves) == 0:
                # pick first legal
                mv = op_moves & -op_moves
            white, black = apply_move(mv, white, black)
            idx = (mv.bit_length()-1)
            r,c = divmod(idx,8)
            print(f"Bot plays {chr(c+97)}{r+1}")
            pretty(black, white)
        else:
            print("Bot has no legal moves. It passes.")

if __name__ == "__main__":
    try:
        game()
    except KeyboardInterrupt:
        sys.exit(0)
