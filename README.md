# Tetrus

An ASCII Tetris-style clone that runs in the terminal using Python and `curses`. Blocks fall onto a 12×24 board, and you can hop back in immediately after a game over without restarting the program.

## Quick Start
- Ensure Python 3.10+ is available with `curses` support (preinstalled on macOS/Linux; Windows users can run under WSL).
- Install project dependencies: `make setup`
- Launch the game: `python -m tetrus`

## Controls
- `← / h` – move left  `→ / l` – move right
- `↑ / x` – rotate clockwise  `z` – rotate counter-clockwise
- `↓` – soft drop  `space` – hard drop
- `p` – pause  `q` – quit current run

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
