"""Local AI-style helpers for estimating a focus score from session behavior."""


def calculate_focus_score(duration_minutes: float, pause_count: int) -> int:
    """Estimate a focus score based on duration and pause frequency.

    The model uses a simple heuristic that rewards longer sessions while slightly
    penalizing repeated pauses, producing a score between 0 and 100.
    """

    base_score = 50 + (duration_minutes * 1.5)
    penalty = pause_count * 4
    score = round(base_score - penalty)
    return max(0, min(100, score))
