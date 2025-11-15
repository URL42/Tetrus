# Tetrus Architecture (Draft)

## Goals
- Console-based Tetris clone rendered with green ASCII characters on a black background.
- Keyboard controls for move/rotate/drop behaving like classic Tetris.
- Deterministic core logic separated from rendering to enable unit testing.

## High-Level Components

| Module | Responsibility |
| --- | --- |
| `src/tetrus/board.py` | Maintain board grid, lock pieces, clear lines, expose score updates. |
| `src/tetrus/tetromino.py` | Define shapes, rotations, spawn logic, and random piece generation via bag system. |
| `src/tetrus/game.py` | Orchestrate game loop, integrate input, timing, scoring, and state transitions. |
| `src/tetrus/renderer.py` | Handle curses setup, draw board/piece/score using ASCII glyphs and green color pair. |
| `src/tetrus/input.py` | Map key presses to game actions; abstracted for easier testing/mocking. |
| `src/tetrus/constants.py` | Store shared settings (board size, tick rate, glyphs, colors). |

## Notes & Assumptions
- Use Python's `curses` module for terminal rendering; fallback stubs may be needed on platforms without curses.
- Standard 10x20 playfield with hidden buffer rows for spawning; support classic 7-bag piece randomizer.
- Score rules follow NES Tetris (lines cleared = 40/100/300/1200 * level).
- Gravity tick increases gradually; soft drop via down arrow accelerates tick, hard drop optional but nice-to-have.
- Tests will target `board` and `tetromino` logic; curses renderer remains thin and manually testable.

## Recent Enhancements
- Added hold slot, next-piece preview, and ghost overlays without changing the monochrome look.
- Introduced persistent high scores plus optional sprint/ultra challenge presets selectable via CLI flags.
