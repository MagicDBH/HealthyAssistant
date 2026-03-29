from __future__ import annotations

from typing import List, Optional
import math


def safe_float(v: object) -> Optional[float]:
    """Convert a value to float, returning None if conversion is not possible.

    Args:
        v: The value to convert. Can be any type.

    Returns:
        The float representation of ``v``, or ``None`` if the value is
        ``None``, an empty string, or cannot be cast to float.

    Trigger condition:
        Called by ``JianDataParser`` whenever a raw CSV cell value is read
        so that missing or malformed entries are represented as ``None``
        rather than raising an exception downstream.
    """
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def mean(values: List[Optional[float]]) -> float:
    """Compute the arithmetic mean of a list, ignoring ``None`` entries.

    Args:
        values: A list of numeric values that may contain ``None``.

    Returns:
        The mean of the non-``None`` values, or ``0.0`` if the list is
        empty after filtering.

    Trigger condition:
        Called by ``JianDataParser.build_7day_summary`` when summarising
        each metric over a rolling 7-day window.
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def std(values: List[Optional[float]]) -> float:
    """Compute the sample standard deviation of a list, ignoring ``None`` entries.

    Args:
        values: A list of numeric values that may contain ``None``.

    Returns:
        The sample standard deviation of the non-``None`` values, or
        ``0.0`` when fewer than two valid values are present.

    Trigger condition:
        Called by ``JianDataParser.build_7day_summary`` alongside
        :func:`mean` to provide a spread measure for each metric.
    """
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def trend_label(
    value: float,
    avg: float,
    sd: float,
    higher_is_better: bool = True,
) -> str:
    """Classify a metric value as ``"high"``, ``"medium"``, or ``"low"`` relative to its 7-day baseline.

    The thresholds are ±0.5 standard deviations from the mean:

    * ``"high"`` – value is above the upper threshold (or below the lower
      threshold when *higher_is_better* is ``False``).
    * ``"low"``  – opposite of ``"high"``.
    * ``"medium"`` – value falls within ±0.5 SD of the mean, or when SD is zero.

    Args:
        value: The latest (today's) metric value.
        avg: The 7-day mean of the metric.
        sd: The 7-day sample standard deviation of the metric.
        higher_is_better: When ``True`` (default) a value above the mean is
            labelled ``"high"`` (good); when ``False`` a value *below* the mean
            is ``"high"`` (good).  For example, *resting_hr* and *stress_score*
            use ``higher_is_better=False``.

    Returns:
        One of ``"high"``, ``"medium"``, or ``"low"``.

    Trigger condition:
        Called once per metric inside ``JianDataParser.build_7day_summary``
        after :func:`mean` and :func:`std` have been computed.
    """
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