import streamlit as st
import numpy as np

from connect4 import (
    ROW_COUNT,
    COLUMN_COUNT,
    PLAYER_PIECE,
    AI_PIECE,
    EMPTY,
    create_board,
    drop_piece,
    get_next_open_row,
    is_valid_location,
    winning_move,
    minimax,
)


st.set_page_config(page_title="Connect 4", page_icon=":game_die:")

if "board" not in st.session_state:
    st.session_state.board = create_board()
    st.session_state.game_over = False
    st.session_state.turn = PLAYER_PIECE

board = st.session_state.board

st.title("Connect 4")


def render_board(board):
    display = []
    for r in reversed(range(ROW_COUNT)):
        row = []
        for c in range(COLUMN_COUNT):
            val = board[r][c]
            if val == PLAYER_PIECE:
                row.append("🔴")
            elif val == AI_PIECE:
                row.append("🟡")
            else:
                row.append("⚪")
        display.append(" ".join(row))
    st.write("\n".join(display))

render_board(board)

st.write("---")

# Player move buttons
cols = st.columns(COLUMN_COUNT)
for c in range(COLUMN_COUNT):
    if cols[c].button("⬇", key=f"player_{c}") and not st.session_state.game_over:
        if is_valid_location(board, c):
            row = get_next_open_row(board, c)
            drop_piece(board, row, c, PLAYER_PIECE)
            if winning_move(board, PLAYER_PIECE):
                st.session_state.game_over = True
                st.success("You win!")
            else:
                st.session_state.turn = AI_PIECE
        st.experimental_rerun()

# AI move
if not st.session_state.game_over and st.session_state.turn == AI_PIECE:
    col, _ = minimax(board, 4, -np.inf, np.inf, True)
    if col is not None and is_valid_location(board, col):
        row = get_next_open_row(board, col)
        drop_piece(board, row, col, AI_PIECE)
        if winning_move(board, AI_PIECE):
            st.session_state.game_over = True
            st.error("AI wins!")
    st.session_state.turn = PLAYER_PIECE
    st.experimental_rerun()

if st.button("Reset Game"):
    st.session_state.board = create_board()
    st.session_state.game_over = False
    st.session_state.turn = PLAYER_PIECE
    st.experimental_rerun()
