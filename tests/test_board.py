from src.tetrus.board import Board
from src.tetrus.tetromino import Tetromino


def test_can_place_detects_collision() -> None:
    board = Board(width=4, height=4, hidden_rows=0)
    piece = Tetromino("O", 0, 0, 0)
    assert board.can_place(piece)
    board.lock_piece(piece)
    assert not board.can_place(piece)
    off_board = Tetromino("O", 0, -1, 0)
    assert not board.can_place(off_board)


def test_clear_completed_lines_scoring() -> None:
    board = Board(width=4, height=4, hidden_rows=0)
    board.lock_piece(Tetromino("O", 0, 0, 2))
    board.lock_piece(Tetromino("O", 0, 2, 2))
    result = board.clear_completed_lines()
    assert result.cleared == 2
    assert result.score_gain == 100
    assert all(cell is None for row in board.visible_rows() for cell in row)


def test_hard_drop_reaches_floor() -> None:
    board = Board(width=10, height=10, hidden_rows=0)
    piece = Tetromino("I", 1, 5, 0)
    dropped = board.hard_drop(piece)
    assert board.can_place(dropped)
    assert not board.can_place(dropped.moved(0, 1))
    assert dropped.y == board.visible_height - dropped.height()
    assert board.drop_distance(piece) == dropped.y - piece.y


def test_drop_distance_stops_above_locked_cells() -> None:
    board = Board(width=4, height=6, hidden_rows=0)
    board.lock_piece(Tetromino("O", 0, 0, 4))
    falling = Tetromino("O", 0, 0, 0)
    distance = board.drop_distance(falling)
    assert distance == 2
    dropped = board.hard_drop(falling)
    assert dropped.y == 2
