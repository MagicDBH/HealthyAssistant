from __future__ import annotations

from typing import List
import math


def safe_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def mean(values: List[float]) -> float:
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def std(values: List[float]) -> float:
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def trend_label(value: float, avg: float, sd: float, higher_is_better: bool = True) -> str:
    if sd == 0:
        return "medium"

    upper = avg + 0.5 * sd
    lower = avg - 0.5 * sd

    if higher_is_better:
        if value >= upper:
            return "high"
        if value <= lower:
            return "low"
        return "medium"
    else:
        if value <= lower:
            return "high"
        if value >= upper:
            return "low"
        return "medium"