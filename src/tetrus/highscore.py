"""High score persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class HighScoreTracker:
    """Tracks and persists the best score across play sessions."""

    path: Path
    best_score: int = 0

    def __post_init__(self) -> None:
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text())
        except FileNotFoundError:
            return
        except (json.JSONDecodeError, OSError):
            return
        try:
            self.best_score = int(data.get("best_score", 0))
        except (TypeError, ValueError):
            self.best_score = 0

    def record(self, score: int) -> bool:
        """Persist score if it beats the stored best value."""
        if score > self.best_score:
            self.best_score = score
            self._save()
            return True
        return False

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        payload = {"best_score": self.best_score}
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            tmp_path.write_text(json.dumps(payload))
            tmp_path.replace(self.path)
        except OSError:
            self.path.write_text(json.dumps(payload))


__all__ = ["HighScoreTracker"]
