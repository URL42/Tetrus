from random import Random

from src.tetrus.tetromino import (
    ALL_TETROMINO_TYPES,
    SevenBagGenerator,
    Tetromino,
    spawn_tetromino,
)


def test_spawn_tetromino_starts_within_board() -> None:
    width = 10
    for kind in ALL_TETROMINO_TYPES:
        piece = spawn_tetromino(kind, width)
        xs = [x for x, _ in piece.cells()]
        assert min(xs) >= 0
        assert max(xs) < width


def test_seven_bag_cycles_all_pieces() -> None:
    rng = Random(123)
    bag = SevenBagGenerator(rng)
    generator = bag.pieces(board_width=10)
    first_cycle = {next(generator).kind for _ in range(7)}
    assert first_cycle == set(ALL_TETROMINO_TYPES)
    second_cycle = {next(generator).kind for _ in range(7)}
    assert second_cycle == set(ALL_TETROMINO_TYPES)


def test_rotation_changes_dimensions() -> None:
    piece = Tetromino("I", 0, 0, 0)
    rotated = piece.rotated(clockwise=True)
    assert rotated.kind == piece.kind
    assert rotated.rotation != piece.rotation
    assert rotated.width() != piece.width()
    assert rotated.height() != piece.height()
