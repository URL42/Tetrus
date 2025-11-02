"""Keyboard mapping helpers."""

from __future__ import annotations

from typing import Optional
import curses


Action = str


def interpret_key(key: int) -> Optional[Action]:
    """Map curses key codes to game actions."""
    if key in (curses.KEY_LEFT, ord("h")):
        return "move_left"
    if key in (curses.KEY_RIGHT, ord("l")):
        return "move_right"
    if key in (curses.KEY_UP, ord("w"), ord("x")):
        return "rotate_cw"
    if key in (ord("z"), ord("a")):
        return "rotate_ccw"
    if key in (curses.KEY_DOWN, ord("j")):
        return "soft_drop"
    if key in (ord(" "),):
        return "hard_drop"
    if key in (ord("p"),):
        return "pause"
    if key in (ord("q"), 27):  # 'q' or ESC
        return "quit"
    return None
