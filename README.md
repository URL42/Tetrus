# Tetrus

An ASCII Tetris-style clone that runs in the terminal using Python and `curses`. Blocks fall onto a 12×24 board with a live next-piece preview, a hold slot, and persistent high scores.

## Quick Start
- Ensure Python 3.10+ is available with `curses` support (preinstalled on macOS/Linux; Windows users can run under WSL).
- Install project dependencies: `make setup`
- Launch the game: `python -m tetrus`

## Controls
- `← / h` – move left  `→ / l` – move right
- `↑ / x` – rotate clockwise  `z` – rotate counter-clockwise  `c` – hold/swap
- `↓ / j` – soft drop  `space` – hard drop
- `p` – pause  `q` – quit current run

## Modes & Options
- Classic endless play is the default. Use `--sprint 40` to clear a specific number of lines as fast as possible, or `--ultra 2m` (supports `s`, `m`, `min`) to chase a high score within a time limit.
- High scores persist in `~/.tetrus_highscore.json` by default; override via `--score-file <path>`.

## Development
- Format & lint: `make lint`
- Run tests: `make test` (requires `pytest`, `ruff`, `mypy`, etc.)
- Focused test run: `python3 -m pytest -k "<pattern>"`

## Project Layout
- `src/tetrus/` – gameplay logic, rendering, and input handling
- `tests/` – `pytest` suite mirroring the source modules
- `docs/` – supplementary project notes
- `tetrus/` – module entry point for `python -m tetrus`

Feel free to tweak constants in `src/tetrus/constants.py` to adjust speed, scoring, or board dimensions. Happy stacking!
