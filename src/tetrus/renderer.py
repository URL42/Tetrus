"""Curses renderer for ASCII green-on-black Tetrus."""

from __future__ import annotations

from typing import Optional
import curses

from .board import Board
from .constants import (
    COLOR_PAIR_BLOCK,
    COLOR_PAIR_HUD,
    EMPTY_GLYPH,
    TETROMINO_GLYPH,
)
from .tetromino import TETROMINO_SHAPES, Tetromino


class Renderer:
    """Responsible for drawing the current frame."""

    def __init__(self, stdscr: "curses._CursesWindow", board: Board) -> None:
        self.stdscr = stdscr
        self.board = board
        self._playfield_origin_y = 1
        self._playfield_origin_x = 2
        self._init_colors()
        self._controls = [
            "←/h : move left",
            "→/l : move right",
            "↑/x : rotate CW",
            "z   : rotate CCW",
            "c   : hold piece",
            "↓   : soft drop",
            "space: hard drop",
            "p   : pause",
            "q   : quit",
        ]
        self._last_required_size: tuple[int, int] = (0, 0)

    def _init_colors(self) -> None:
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(COLOR_PAIR_BLOCK, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(COLOR_PAIR_HUD, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def draw(
        self,
        current_piece: Optional[Tetromino],
        ghost_piece: Optional[Tetromino],
        score: int,
        level: int,
        total_lines: int,
        *,
        next_piece: Optional[Tetromino],
        held_kind: Optional[str],
        best_score: int,
        mode_name: str,
        sprint_target: Optional[int],
        elapsed: float,
        time_remaining: Optional[float],
    ) -> None:
        hud_lines = self._hud_lines(
            score,
            level,
            total_lines,
            best_score,
            mode_name,
            sprint_target,
            elapsed,
            time_remaining,
            next_piece.kind if next_piece is not None else None,
            held_kind,
        )
        if not self._fits_screen(hud_lines):
            self._draw_resize_message()
            self.stdscr.refresh()
            return

        self.stdscr.erase()
        self._draw_border()
        self._draw_board()
        if ghost_piece is not None:
            self._draw_piece(ghost_piece, solid=False)
        if current_piece is not None:
            self._draw_piece(current_piece, solid=True)
        self._draw_hud(hud_lines)
        self.stdscr.refresh()

    def _draw_board(self) -> None:
        visible_rows = self.board.visible_rows()
        for y, row in enumerate(visible_rows):
            for x, cell in enumerate(row):
                if cell is None:
                    continue
                glyph = cell if isinstance(cell, str) else TETROMINO_GLYPH
                self._draw_cell(x, y, glyph, solid=True)

    def _draw_piece(self, piece: Tetromino, solid: bool) -> None:
        glyph = TETROMINO_GLYPH if solid else ".."
        attr = curses.color_pair(COLOR_PAIR_BLOCK)
        if not solid:
            attr |= curses.A_DIM
        for x, y in piece.cells():
            visible_y = y - self.board.hidden_rows
            if visible_y < 0 or visible_y >= self.board.visible_height:
                continue
            if 0 <= x < self.board.width:
                self.stdscr.addstr(
                    self._playfield_origin_y + visible_y,
                    self._playfield_origin_x + x * len(EMPTY_GLYPH),
                    glyph,
                    attr,
                )

    def _draw_cell(self, x: int, visible_y: int, glyph: str, solid: bool) -> None:
        attr = curses.color_pair(COLOR_PAIR_BLOCK)
        if not solid:
            attr |= curses.A_DIM
        self.stdscr.addstr(
            self._playfield_origin_y + visible_y,
            self._playfield_origin_x + x * len(EMPTY_GLYPH),
            glyph,
            attr,
        )

    def _draw_border(self) -> None:
        width = self.board.width * len(EMPTY_GLYPH)
        height = self.board.visible_height
        attr = curses.color_pair(COLOR_PAIR_HUD) | curses.A_BOLD
        top = "+" + "-" * width + "+"
        bottom = top
        self.stdscr.addstr(self._playfield_origin_y - 1, self._playfield_origin_x - 1, top, attr)
        self.stdscr.addstr(
            self._playfield_origin_y + height,
            self._playfield_origin_x - 1,
            bottom,
            attr,
        )
        for row in range(height):
            self.stdscr.addstr(
                self._playfield_origin_y + row,
                self._playfield_origin_x - 1,
                "|",
                attr,
            )
            self.stdscr.addstr(
                self._playfield_origin_y + row,
                self._playfield_origin_x + width,
                "|",
                attr,
            )

    def _draw_hud(self, hud_lines: list[tuple[int, str]]) -> None:
        origin_x = self._playfield_origin_x + self.board.width * len(EMPTY_GLYPH) + 3
        attr = curses.color_pair(COLOR_PAIR_HUD) | curses.A_BOLD
        for offset, text in hud_lines:
            self.stdscr.addstr(self._playfield_origin_y + offset, origin_x, text, attr)

    def _hud_lines(
        self,
        score: int,
        level: int,
        total_lines: int,
        best_score: int,
        mode_name: str,
        sprint_target: Optional[int],
        elapsed: float,
        time_remaining: Optional[float],
        next_kind: Optional[str],
        held_kind: Optional[str],
    ) -> list[tuple[int, str]]:
        lines: list[tuple[int, str]] = []
        cursor = 0
        lines.append((cursor, "Tetrus"))
        cursor += 2
        lines.append((cursor, f"Mode : {mode_name}"))
        cursor += 1
        lines.append((cursor, f"Score: {score}"))
        cursor += 1
        lines.append((cursor, f"Best : {best_score}"))
        cursor += 1
        lines.append((cursor, f"Level: {level}"))
        cursor += 1
        if sprint_target is not None:
            lines.append((cursor, f"Lines: {total_lines}/{sprint_target}"))
        else:
            lines.append((cursor, f"Lines: {total_lines}"))
        cursor += 1
        duration = time_remaining if time_remaining is not None else elapsed
        label = "Time left" if time_remaining is not None else "Time"
        lines.append((cursor, f"{label}: {self._format_duration(duration)}"))
        cursor += 2

        lines.append((cursor, "Next:"))
        cursor += 1
        for block in self._mini_piece_lines(next_kind):
            lines.append((cursor, block))
            cursor += 1
        cursor += 1

        lines.append((cursor, "Hold:"))
        cursor += 1
        for block in self._mini_piece_lines(held_kind):
            lines.append((cursor, block))
            cursor += 1
        cursor += 1

        lines.append((cursor, "Controls:"))
        cursor += 1
        for line in self._controls:
            lines.append((cursor, line))
            cursor += 1
        return lines

    def _mini_piece_lines(self, kind: Optional[str]) -> list[str]:
        size = 4
        grid = [[EMPTY_GLYPH for _ in range(size)] for _ in range(size)]
        if kind is not None:
            offsets = TETROMINO_SHAPES[kind][0]
            min_x = min(ox for ox, _ in offsets)
            min_y = min(oy for _, oy in offsets)
            for ox, oy in offsets:
                grid[oy - min_y][ox - min_x] = TETROMINO_GLYPH
        return ["".join(row) for row in grid]

    def _format_duration(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        minutes, secs = divmod(total_seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _fits_screen(self, hud_lines: list[tuple[int, str]]) -> bool:
        max_y, max_x = self.stdscr.getmaxyx()
        playfield_cells_width = self.board.width * len(EMPTY_GLYPH)
        playfield_right = self._playfield_origin_x + playfield_cells_width
        hud_start_x = self._playfield_origin_x + playfield_cells_width + 3
        hud_right = hud_start_x
        for _, text in hud_lines:
            hud_right = max(hud_right, hud_start_x + len(text) - 1)
        max_right = max(playfield_right, hud_right)
        required_width = max_right + 1

        board_bottom = self._playfield_origin_y + self.board.visible_height
        hud_bottom = max((self._playfield_origin_y + offset for offset, _ in hud_lines), default=0)
        max_bottom = max(board_bottom, hud_bottom)
        required_height = max_bottom + 1

        self._last_required_size = (required_height, required_width)
        return max_y >= required_height and max_x >= required_width

    def _draw_resize_message(self) -> None:
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()
        required_height, required_width = self._last_required_size
        messages = [
            "Terminal too small for Tetrus.",
            f"Need at least {required_width} x {required_height}.",
            f"Current size {max_x} x {max_y}.",
            "Please enlarge the window and try again.",
        ]
        for idx, text in enumerate(messages):
            if idx >= max_y:
                break
            space = max(0, max_x - 1)
            if space == 0:
                continue
            display = text[:space]
            attr = curses.A_BOLD if idx == 0 else curses.A_NORMAL
            self.stdscr.addstr(idx, 0, display, attr)
