"""Board management for Tetrus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .constants import BOARD_HEIGHT, BOARD_WIDTH, HIDDEN_ROWS, TETROMINO_GLYPH
from .tetromino import Tetromino


Cell = Optional[str]


def _empty_row(width: int) -> List[Cell]:
    return [None for _ in range(width)]


@dataclass
class LineClearResult:
    cleared: int
    score_gain: int


class Board:
    """Represents the playfield grid and supports basic operations."""

    def __init__(
        self,
        width: int = BOARD_WIDTH,
        height: int = BOARD_HEIGHT,
        hidden_rows: int = HIDDEN_ROWS,
    ) -> None:
        self.width = width
        self.visible_height = height
        self.hidden_rows = hidden_rows
        self.total_height = height + hidden_rows
        self._grid: List[List[Cell]] = [_empty_row(width) for _ in range(self.total_height)]

    def reset(self) -> None:
        for y in range(self.total_height):
            self._grid[y] = _empty_row(self.width)

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.total_height

    def is_cell_free(self, x: int, y: int) -> bool:
        if not self.is_inside(x, y):
            return False
        return self._grid[y][x] is None

    def can_place(self, piece: Tetromino) -> bool:
        for x, y in piece.cells():
            if not self.is_inside(x, y):
                return False
            if self._grid[y][x] is not None:
                return False
        return True

    def lock_piece(self, piece: Tetromino, glyph: str = TETROMINO_GLYPH) -> None:
        for x, y in piece.cells():
            if not self.is_inside(x, y):
                raise ValueError("Cannot lock piece outside board bounds.")
            self._grid[y][x] = glyph

    def _line_full(self, row: Sequence[Cell]) -> bool:
        return all(cell is not None for cell in row)

    def clear_completed_lines(self) -> LineClearResult:
        cleared = 0
        new_grid: List[List[Cell]] = []
        for row in self._grid:
            if self._line_full(row):
                cleared += 1
            else:
                new_grid.append(list(row))

        for _ in range(cleared):
            new_grid.insert(0, _empty_row(self.width))

        # Keep only the most recent rows (in case hidden rows > 0).
        self._grid = new_grid[-self.total_height :]

        score_gain = 0
        if cleared == 1:
            score_gain = 40
        elif cleared == 2:
            score_gain = 100
        elif cleared == 3:
            score_gain = 300
        elif cleared >= 4:
            score_gain = 1200

        return LineClearResult(cleared=cleared, score_gain=score_gain)

    def drop_distance(self, piece: Tetromino) -> int:
        test_piece = piece
        distance = 0
        while True:
            trial = test_piece.moved(0, 1)
            if not self.can_place(trial):
                return distance
            test_piece = trial
            distance += 1

    def hard_drop(self, piece: Tetromino) -> Tetromino:
        distance = self.drop_distance(piece)
        return piece.moved(0, distance)

    def cell(self, x: int, y: int) -> Cell:
        if not self.is_inside(x, y):
            return None
        return self._grid[y][x]

    def visible_rows(self) -> List[List[Cell]]:
        return self._grid[self.hidden_rows :]

    def column_heights(self) -> List[int]:
        heights = [0] * self.width
        for x in range(self.width):
            for y in range(self.total_height):
                if self._grid[y][x] is not None:
                    heights[x] = self.total_height - y
                    break
        return heights
