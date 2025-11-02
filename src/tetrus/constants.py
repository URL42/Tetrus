"Basic constants for the Tetrus game."

BOARD_WIDTH: int = 12
BOARD_HEIGHT: int = 24
HIDDEN_ROWS: int = 2

GRAVITY_START_SECONDS: float = 0.8
GRAVITY_LEVEL_STEP: float = 0.9  # multiply delay per level
SOFT_DROP_MULTIPLIER: float = 0.05  # scale gravity interval when soft-dropping

LOCK_DELAY_SECONDS: float = 0.5

TETROMINO_GLYPH: str = "[]"
EMPTY_GLYPH: str = "  "

COLOR_PAIR_BLOCK: int = 1
COLOR_PAIR_HUD: int = 2
