"""Tetromino definitions and bag randomizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Sequence, Tuple
import random

Point = Tuple[int, int]

TETROMINO_SHAPES: dict[str, Sequence[Sequence[Point]]] = {
    "I": (
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (0, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    "O": (
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (0, 1), (1, 1)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0), (1, 1)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
}

ALL_TETROMINO_TYPES: Tuple[str, ...] = tuple(TETROMINO_SHAPES.keys())


@dataclass(frozen=True)
class Tetromino:
    """Represents a tetromino's kind, rotation, and origin."""

    kind: str
    rotation: int
    x: int
    y: int

    def cells(self) -> List[Point]:
        """Absolute board coordinates for each block."""
        offsets = TETROMINO_SHAPES[self.kind][self.rotation]
        return [(self.x + ox, self.y + oy) for ox, oy in offsets]

    def moved(self, dx: int, dy: int) -> "Tetromino":
        return Tetromino(self.kind, self.rotation, self.x + dx, self.y + dy)

    def rotated(self, clockwise: bool = True) -> "Tetromino":
        rotation_count = len(TETROMINO_SHAPES[self.kind])
        delta = 1 if clockwise else -1
        return Tetromino(self.kind, (self.rotation + delta) % rotation_count, self.x, self.y)

    def width(self) -> int:
        offsets = TETROMINO_SHAPES[self.kind][self.rotation]
        return max(ox for ox, _ in offsets) + 1

    def height(self) -> int:
        offsets = TETROMINO_SHAPES[self.kind][self.rotation]
        return max(oy for _, oy in offsets) + 1


def spawn_tetromino(kind: str, board_width: int) -> Tetromino:
    """Spawn tetromino centered horizontally near the top of the board."""
    rotation = 0
    offsets = TETROMINO_SHAPES[kind][rotation]
    min_x = min(ox for ox, _ in offsets)
    max_x = max(ox for ox, _ in offsets)
    piece_width = max_x - min_x + 1
    spawn_x = (board_width - piece_width) // 2 - min_x
    return Tetromino(kind=kind, rotation=rotation, x=spawn_x, y=0)


class SevenBagGenerator:
    """Generates tetromino kinds using the classic seven-bag algorithm."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._bag: List[str] = []

    def _refill(self) -> None:
        self._bag = list(ALL_TETROMINO_TYPES)
        self._rng.shuffle(self._bag)

    def next_kind(self) -> str:
        if not self._bag:
            self._refill()
        return self._bag.pop()

    def pieces(self, board_width: int) -> Iterator[Tetromino]:
        while True:
            yield spawn_tetromino(self.next_kind(), board_width)
