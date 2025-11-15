"""Main game loop for Tetrus."""

from __future__ import annotations

import argparse
import curses
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from .board import Board
from .constants import (
    GRAVITY_LEVEL_STEP,
    GRAVITY_START_SECONDS,
    LOCK_DELAY_SECONDS,
    SOFT_DROP_MULTIPLIER,
)
from .highscore import HighScoreTracker
from .input import interpret_key
from .renderer import Renderer
from .tetromino import SevenBagGenerator, Tetromino, spawn_tetromino


DEFAULT_HIGHSCORE_PATH = Path.home() / ".tetrus_highscore.json"


@dataclass
class GameStats:
    score: int = 0
    level: int = 1
    total_lines: int = 0


@dataclass(frozen=True)
class GameMode:
    """Represents a gameplay preset."""

    name: str
    sprint_target_lines: Optional[int] = None
    time_limit_seconds: Optional[float] = None


class Game:
    """Encapsulates game state and loop to simplify testing."""

    def __init__(self, mode: GameMode, tracker: HighScoreTracker) -> None:
        self.mode = mode
        self.high_scores = tracker
        self.board = Board()
        self.bag = SevenBagGenerator()
        self._piece_iter = self.bag.pieces(self.board.width)
        self.stats = GameStats()
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.held_kind: Optional[str] = None
        self._hold_used = False
        self._lock_timer_started: Optional[float] = None
        self._gravity_interval = GRAVITY_START_SECONDS
        self._last_gravity_time = time.monotonic()
        self._run_started = time.monotonic()

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
        self._hold_used = False
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
            if (
                self.mode.sprint_target_lines is not None
                and self.stats.total_lines >= self.mode.sprint_target_lines
            ):
                raise ModeComplete("Sprint target reached.")
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

    def _hold_piece(self) -> None:
        assert self.current_piece is not None
        if self._hold_used:
            return
        swap_kind = self.current_piece.kind
        if self.held_kind is None:
            self.held_kind = swap_kind
            self.current_piece = None
            self._hold_used = True
            self._spawn_next_piece()
            return
        replacement = spawn_tetromino(self.held_kind, self.board.width)
        if not self.board.can_place(replacement):
            raise GameOver("Cannot place held piece.")
        self.held_kind = swap_kind
        self.current_piece = replacement
        self._lock_timer_started = None
        self._hold_used = True

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
        elif action == "hold":
            self._hold_piece()
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
        self._run_started = time.monotonic()
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
            elapsed = time.monotonic() - self._run_started
            time_remaining = None
            if self.mode.time_limit_seconds is not None:
                time_remaining = max(0.0, self.mode.time_limit_seconds - elapsed)
            next_piece = self.next_piece
            renderer.draw(
                self.current_piece,
                ghost_piece,
                self.stats.score,
                self.stats.level,
                self.stats.total_lines,
                next_piece=next_piece,
                held_kind=self.held_kind,
                best_score=self.high_scores.best_score,
                mode_name=self.mode.name,
                sprint_target=self.mode.sprint_target_lines,
                elapsed=elapsed,
                time_remaining=time_remaining,
            )
            if self.mode.time_limit_seconds is not None and elapsed >= self.mode.time_limit_seconds:
                raise ModeComplete("Time limit reached.")
            time.sleep(0.01)

    @property
    def elapsed_time(self) -> float:
        return time.monotonic() - self._run_started

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


class ModeComplete(GameOver):
    pass


def _prompt_restart() -> bool:
    try:
        response = input("Play again? [y/N]: ")
    except EOFError:
        return False
    return response.strip().lower() in {"y", "yes"}


def _parse_duration(value: str) -> float:
    text = value.strip().lower()
    multiplier = 1.0
    for suffix, factor in (("min", 60.0), ("m", 60.0), ("s", 1.0)):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            multiplier = factor
            break
    try:
        amount = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid duration '{value}'.") from exc
    if amount <= 0:
        raise argparse.ArgumentTypeError("Duration must be positive.")
    return amount * multiplier


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Tetrus terminal game.")
    parser.add_argument(
        "--score-file",
        type=Path,
        default=DEFAULT_HIGHSCORE_PATH,
        help="path to store the persistent high score (default: %(default)s)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--sprint",
        type=int,
        metavar="LINES",
        help="clear LINES lines as fast as possible (e.g., --sprint 40)",
    )
    group.add_argument(
        "--ultra",
        type=_parse_duration,
        metavar="DURATION",
        help="score as much as possible within DURATION (e.g., --ultra 2m)",
    )
    return parser.parse_args(argv)


def _select_mode(args: argparse.Namespace) -> GameMode:
    if args.sprint:
        return GameMode(name=f"Sprint ({args.sprint} lines)", sprint_target_lines=args.sprint)
    if args.ultra:
        seconds = args.ultra
        if seconds % 60 == 0:
            minutes = int(seconds // 60)
            label = f"Ultra ({minutes} min)"
        else:
            label = f"Ultra ({int(seconds)} s)"
        return GameMode(name=label, time_limit_seconds=seconds)
    return GameMode(name="Marathon")


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def _print_run_summary(
    stats: GameStats,
    elapsed: float,
    best_score: int,
    message: Optional[str],
    new_best: bool,
) -> None:
    print()
    if message:
        print(message)
    print(f"Score: {stats.score}  Best: {best_score}")
    print(f"Lines: {stats.total_lines}  Level: {stats.level}")
    print(f"Time : {_format_duration(elapsed)}")
    if new_best:
        print("New high score!")


def _handle_round_end(game: Game, tracker: HighScoreTracker, message: Optional[str]) -> bool:
    elapsed = game.elapsed_time
    new_best = tracker.record(game.stats.score)
    _print_run_summary(game.stats, elapsed, tracker.best_score, message, new_best)
    return _prompt_restart()


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    tracker = HighScoreTracker(args.score_file)
    mode = _select_mode(args)
    while True:
        game = Game(mode=mode, tracker=tracker)
        try:
            curses.wrapper(game.run)
            tracker.record(game.stats.score)
            return
        except ModeComplete as outcome:
            if not _handle_round_end(game, tracker, outcome.args[0] if outcome.args else None):
                print("Game Over! Thanks for playing Tetrus.")
                return
            print()
        except GameOver as exc:
            if not _handle_round_end(game, tracker, str(exc) or None):
                print("Game Over! Thanks for playing Tetrus.")
                return
            print()


if __name__ == "__main__":
    main()
