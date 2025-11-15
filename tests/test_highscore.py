from pathlib import Path

from src.tetrus.highscore import HighScoreTracker


def test_record_persists_best_score(tmp_path: Path) -> None:
    score_file = tmp_path / "scores.json"
    tracker = HighScoreTracker(score_file)
    assert tracker.best_score == 0
    assert tracker.record(1234)
    assert tracker.best_score == 1234

    tracker_again = HighScoreTracker(score_file)
    assert tracker_again.best_score == 1234
    assert not tracker_again.record(1000)
    assert tracker_again.best_score == 1234


def test_corrupt_file_resets_to_zero(tmp_path: Path) -> None:
    score_file = tmp_path / "scores.json"
    score_file.write_text("not json")
    tracker = HighScoreTracker(score_file)
    assert tracker.best_score == 0
