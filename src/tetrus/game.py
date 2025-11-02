"""Main game loop for Tetrus."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from typing import Optional

from .board import Board
from .constants import (
    GRAVITY_LEVEL_STEP,
    GRAVITY_START_SECONDS,
    LOCK_DELAY_SECONDS,
    SOFT_DROP_MULTIPLIER,
)
from .input import interpret_key
from .renderer import Renderer
from .tetromino import SevenBagGenerator, Tetromino


@dataclass
class GameStats:
    score: int = 0
    level: int = 1
    total_lines: int = 0


class Game:
    """Encapsulates game state and loop to simplify testing."""

    def __init__(self) -> None:
        self.board = Board()
        self.bag = SevenBagGenerator()
        self._piece_iter = self.bag.pieces(self.board.width)
        self.stats = GameStats()
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self._lock_timer_started: Optional[float] = None
        self._gravity_interval = GRAVITY_START_SECONDS
        self._last_gravity_time = time.monotonic()

    def _update_gravity_interval(self) -> None:
        self._gravity_interval = max(
            0.05,
            GRAVITY_START_SECONDS * (GRAVITY_LEVEL_STEP ** (self.stats.level - 1)),
        )

    def _spawn_next_piece(self) -> None:
        if self.next_piece is None:
            self.next_piece = next(self._piece_iter)
        self.current_piece = self.next_piece
        self.next_piece = next(self._piece_iter)
        if not self.board.can_place(self.current_piece):
            raise GameOver("No room to spawn the next piece.")

    def _lock_current_piece(self) -> None:
        assert self.current_piece is not None
        self.board.lock_piece(self.current_piece)
        result = self.board.clear_completed_lines()
        if result.cleared:
            self.stats.total_lines += result.cleared
            self.stats.level = 1 + self.stats.total_lines // 10
            self.stats.score += result.score_gain * self.stats.level
            self._update_gravity_interval()
        self._lock_timer_started = None
        self.current_piece = None

    def _move_piece(self, dx: int, dy: int) -> bool:
        assert self.current_piece is not None
        moved = self.current_piece.moved(dx, dy)
        if self.board.can_place(moved):
            self.current_piece = moved
            if dy > 0:
                self._last_gravity_time = time.monotonic()
            self._lock_timer_started = None
            return True
        return False

    def _rotate_piece(self, clockwise: bool) -> None:
        assert self.current_piece is not None
        rotated = self.current_piece.rotated(clockwise)
        for kick in (0, -1, 1, -2, 2):
            candidate = rotated.moved(kick, 0)
            if self.board.can_place(candidate):
                self.current_piece = candidate
                self._lock_timer_started = None
                return

    def _process_action(self, action: str) -> bool:
        assert self.current_piece is not None
        if action == "move_left":
            self._move_piece(-1, 0)
        elif action == "move_right":
            self._move_piece(1, 0)
        elif action == "rotate_cw":
            self._rotate_piece(clockwise=True)
        elif action == "rotate_ccw":
            self._rotate_piece(clockwise=False)
        elif action == "soft_drop":
            if not self._move_piece(0, 1):
                self._maybe_start_lock_timer()
            else:
                self.stats.score += 1
        elif action == "hard_drop":
            drop_distance = self.board.drop_distance(self.current_piece)
            self.current_piece = self.current_piece.moved(0, drop_distance)
            self.stats.score += drop_distance * 2
            self._lock_current_piece()
            self._spawn_next_piece()
        elif action == "pause":
            return True
        elif action == "quit":
            raise GameQuit
        return False

    def _maybe_start_lock_timer(self) -> None:
        if self._lock_timer_started is None:
            self._lock_timer_started = time.monotonic()

    def _apply_gravity(self, soft_drop: bool) -> None:
        assert self.current_piece is not None
        interval = self._gravity_interval
        if soft_drop:
            interval *= SOFT_DROP_MULTIPLIER
        now = time.monotonic()
        if now - self._last_gravity_time < interval:
            return
        if not self._move_piece(0, 1):
            self._maybe_start_lock_timer()
        self._last_gravity_time = now

    def run(self, stdscr: "curses._CursesWindow") -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(0)
        renderer = Renderer(stdscr, self.board)
        self.board.reset()
        self._update_gravity_interval()
        self._spawn_next_piece()

        paused = False
        while True:
            if self.current_piece is None:
                self._spawn_next_piece()
            soft_drop_active = False
            try:
                while True:
                    key = stdscr.getch()
                    if key == -1:
                        break
                    action = interpret_key(key)
                    if action is None:
                        continue
                    if action == "pause":
                        paused = not paused
                        if paused:
                            self._show_pause_screen(stdscr)
                        else:
                            stdscr.nodelay(True)
                        continue
                    if paused:
                        continue
                    if action == "soft_drop":
                        soft_drop_active = True
                    should_pause = self._process_action(action)
                    if should_pause:
                        paused = True
                        self._show_pause_screen(stdscr)
            except GameQuit:
                break

            if paused:
                time.sleep(0.05)
                continue

            self._apply_gravity(soft_drop_active)
            self._handle_lock_delay()
            ghost_piece = None
            if self.current_piece is not None:
                ghost_piece = self.board.hard_drop(self.current_piece)
            renderer.draw(self.current_piece, ghost_piece, self.stats.score, self.stats.level, self.stats.total_lines)
            time.sleep(0.01)

    def _handle_lock_delay(self) -> None:
        if self._lock_timer_started is None or self.current_piece is None:
            return
        if time.monotonic() - self._lock_timer_started >= LOCK_DELAY_SECONDS:
            self._lock_current_piece()

    def _show_pause_screen(self, stdscr: "curses._CursesWindow") -> None:
        stdscr.nodelay(False)
        stdscr.addstr(0, 0, "Paused. Press 'p' to resume.", curses.A_BOLD)
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if interpret_key(key) == "pause":
                stdscr.nodelay(True)
                return


class GameQuit(RuntimeError):
    pass


class GameOver(RuntimeError):
    pass


def _prompt_restart() -> bool:
    try:
        response = input("Game Over! Play again? [y/N]: ")
    except EOFError:
        return False
    return response.strip().lower() in {"y", "yes"}


def main() -> None:
    while True:
        game = Game()
        try:
            curses.wrapper(game.run)
            return
        except GameOver:
            if not _prompt_restart():
                print("Game Over! Thanks for playing Tetrus.")
                return
            print()


if __name__ == "__main__":
    main()
