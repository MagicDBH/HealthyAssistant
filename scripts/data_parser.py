from __future__ import annotations

from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd

from .metrics import safe_float, mean, std, trend_label


class JianDataParser:
    """Parse and summarise health data from the LifeSnaps-derived ``jian.csv`` file.

    This is the **entry point** for all data operations in the skill pipeline.
    It is instantiated once with the CSV path and then used to generate both
    a per-day snapshot and a 7-day rolling summary that feed the prompt builder.

    Trigger condition:
        Instantiated and called at the start of every skill invocation, before
        question classification or query rewriting.  The typical call sequence is::

            parser = JianDataParser(csv_path)
            daily  = parser.build_daily_summary(user_id, date)
            week   = parser.build_7day_summary(user_id, date)

    Attributes:
        csv_path: Resolved path to the CSV data file.
        df: The loaded ``pandas.DataFrame``; ``None`` until :meth:`load` is called.
    """

    def __init__(self, csv_path: str) -> None:
        """Initialise the parser with the path to the CSV data file.

        Args:
            csv_path: Absolute or relative path to ``jian.csv`` (or any file
                with an identical schema).  The file is *not* read until
                :meth:`load` (or a method that calls it) is invoked.
        """
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """Read the CSV file into memory and parse the ``date`` column.

        Returns:
            The loaded ``pandas.DataFrame`` with the ``date`` column coerced
            to ``datetime64``.

        Raises:
            FileNotFoundError: If ``csv_path`` does not point to an existing file.

        Trigger condition:
            Called lazily by :meth:`_ensure_loaded` the first time data is
            needed.  Can also be called explicitly to pre-load the file.
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        return self.df

    def _ensure_loaded(self) -> None:
        """Ensure the CSV has been loaded before attempting to query it.

        Trigger condition:
            Called internally by every public data-access method.
        """
        if self.df is None:
            self.load()

    def get_user_daily_row(self, user_id: str, date: str) -> Dict[str, Any]:
        """Return the single CSV row that matches *user_id* and *date*.

        Args:
            user_id: The user identifier as it appears in the ``id`` column.
            date: An ISO-8601 date string such as ``"2021-07-31"``.

        Returns:
            A dictionary mapping column names to their raw values for the
            matched row.

        Raises:
            ValueError: If no row is found for the given ``user_id`` / ``date``
                combination.

        Trigger condition:
            Called by :meth:`build_daily_summary` to obtain the raw values
            for today's health snapshot.
        """
        self._ensure_loaded()
        target_date = pd.to_datetime(date, errors="coerce")

        df = self.df.copy()
        df["id"] = df["id"].astype(str)

        row = df[(df["id"] == str(user_id)) & (df["date"] == target_date)]
        if row.empty:
            raise ValueError(f"No record found for user_id={user_id}, date={date}")

        return row.iloc[0].to_dict()

    def get_7day_window(self, user_id: str, date: str) -> pd.DataFrame:
        """Return the rows that fall within the 7 days ending on (and including) *date*.

        The window is *open on the left*, i.e. it includes ``(date − 7 days, date]``.

        Args:
            user_id: The user identifier as it appears in the ``id`` column.
            date: The end date (inclusive) of the rolling window in ISO-8601
                format, e.g. ``"2021-07-31"``.

        Returns:
            A ``pandas.DataFrame`` with at most 7 rows, sorted by date ascending.

        Trigger condition:
            Called by :meth:`build_7day_summary` to gather the raw values
            needed for trend computation.
        """
        self._ensure_loaded()
        target_date = pd.to_datetime(date, errors="coerce")

        df = self.df.copy()
        df["id"] = df["id"].astype(str)

        user_df = df[df["id"] == str(user_id)].sort_values("date")
        window = user_df[
            (user_df["date"] <= target_date)
            & (user_df["date"] > target_date - pd.Timedelta(days=7))
        ]
        return window

    def build_daily_summary(self, user_id: str, date: str) -> Dict[str, Any]:
        """Build a structured snapshot of a user's health data for a single day.

        The snapshot is divided into four sub-sections that map directly to the
        categories defined in ``skill.md`` (§4.1):

        * ``profile``  – static demographic attributes.
        * ``activity`` – step / calorie / active-minutes metrics.
        * ``sleep``    – sleep duration, efficiency and stage ratios.
        * ``stress``   – HRV, resting heart rate and stress / recovery scores.
        * ``context``  – time-at-location proportions (HOME, WORK, TRANSIT …).

        Args:
            user_id: The user identifier as it appears in the ``id`` column.
            date: The target date in ISO-8601 format (e.g. ``"2021-07-31"``).

        Returns:
            A nested dictionary suitable for direct use as the ``daily`` field
            of the OpenClaw context payload.

        Trigger condition:
            First function called in the skill pipeline after the user's
            question has been received.  The result is passed to
            :func:`~scripts.prompt_builder.classify_question` and subsequently
            merged into the final payload by
            :func:`~scripts.openclaw_payload.build_payload`.
        """
        row = self.get_user_daily_row(user_id, date)

        return {
            "user_id": str(user_id),
            "date": str(date),
            "profile": {
                "age": row.get("age"),
                "gender": row.get("gender"),
                "bmi": row.get("bmi"),
                "step_goal": row.get("step_goal"),
                "step_goal_label": row.get("step_goal_label"),
            },
            "activity": {
                "calories": safe_float(row.get("calories")),
                "distance": safe_float(row.get("distance")),
                "steps": safe_float(row.get("steps")),
                "lightly_active_minutes": safe_float(row.get("lightly_active_minutes")),
                "moderately_active_minutes": safe_float(row.get("moderately_active_minutes")),
                "very_active_minutes": safe_float(row.get("very_active_minutes")),
                "sedentary_minutes": safe_float(row.get("sedentary_minutes")),
            },
            "sleep": {
                "sleep_duration": safe_float(row.get("sleep_duration")),
                "minutesToFallAsleep": safe_float(row.get("minutesToFallAsleep")),
                "minutesAsleep": safe_float(row.get("minutesAsleep")),
                "minutesAwake": safe_float(row.get("minutesAwake")),
                "minutesAfterWakeup": safe_float(row.get("minutesAfterWakeup")),
                "sleep_efficiency": safe_float(row.get("sleep_efficiency")),
                "sleep_deep_ratio": safe_float(row.get("sleep_deep_ratio")),
                "sleep_wake_ratio": safe_float(row.get("sleep_wake_ratio")),
                "sleep_light_ratio": safe_float(row.get("sleep_light_ratio")),
                "sleep_rem_ratio": safe_float(row.get("sleep_rem_ratio")),
            },
            "stress": {
                "rmssd": safe_float(row.get("rmssd")),
                "resting_hr": safe_float(row.get("resting_hr")),
                "nremhr": safe_float(row.get("nremhr")),
                "stress_score": safe_float(row.get("stress_score")),
                "sleep_points_percentage": safe_float(row.get("sleep_points_percentage")),
                "responsiveness_points_percentage": safe_float(row.get("responsiveness_points_percentage")),
            },
            "context": {
                "HOME": safe_float(row.get("HOME")),
                "HOME_OFFICE": safe_float(row.get("HOME_OFFICE")),
                "WORK/SCHOOL": safe_float(row.get("WORK/SCHOOL")),
                "OUTDOORS": safe_float(row.get("OUTDOORS")),
                "TRANSIT": safe_float(row.get("TRANSIT")),
                "OTHER": safe_float(row.get("OTHER")),
            },
        }

    def build_7day_summary(self, user_id: str, date: str) -> Dict[str, Any]:
        """Compute rolling 7-day statistics for the key health metrics.

        For each metric the summary contains:

        * ``latest``      – the value on *date* (today).
        * ``7d_mean``     – mean over the window.
        * ``7d_std``      – sample standard deviation over the window.
        * ``trend_label`` – ``"high"``, ``"medium"``, or ``"low"`` relative to
          the baseline (see :func:`~scripts.metrics.trend_label`).

        Args:
            user_id: The user identifier as it appears in the ``id`` column.
            date: The target date in ISO-8601 format (e.g. ``"2021-07-31"``).

        Returns:
            A dictionary with keys ``user_id``, ``date``, ``window_days``, and
            ``metrics``.  The ``metrics`` sub-dictionary is keyed by metric name
            and is consumed directly by
            :func:`~scripts.prompt_builder.build_rewrite_prompt` and
            :func:`~scripts.prompt_builder.build_openclaw_context`.

        Trigger condition:
            Called immediately after :meth:`build_daily_summary` in the skill
            pipeline.  Both results are merged into a single ``summary`` dict
            that flows through the rest of the pipeline.
        """
        window = self.get_7day_window(user_id, date)

        def col_values(col: str) -> List[Optional[float]]:
            if col not in window.columns:
                return []
            return [safe_float(v) for v in window[col].tolist()]

        metrics = {
            "steps": {"values": col_values("steps"), "higher_is_better": True},
            "calories": {"values": col_values("calories"), "higher_is_better": True},
            "distance": {"values": col_values("distance"), "higher_is_better": True},
            "lightly_active_minutes": {"values": col_values("lightly_active_minutes"), "higher_is_better": True},
            "moderately_active_minutes": {"values": col_values("moderately_active_minutes"), "higher_is_better": True},
            "very_active_minutes": {"values": col_values("very_active_minutes"), "higher_is_better": True},
            "sedentary_minutes": {"values": col_values("sedentary_minutes"), "higher_is_better": False},
            "sleep_duration": {"values": col_values("sleep_duration"), "higher_is_better": True},
            "sleep_efficiency": {"values": col_values("sleep_efficiency"), "higher_is_better": True},
            "rmssd": {"values": col_values("rmssd"), "higher_is_better": True},
            "resting_hr": {"values": col_values("resting_hr"), "higher_is_better": False},
            "stress_score": {"values": col_values("stress_score"), "higher_is_better": False},
        }

        result: Dict[str, Any] = {}
        for name, cfg in metrics.items():
            vals = cfg["values"]
            if not vals:
                continue
            avg = mean(vals)
            sd = std(vals)
            latest = vals[-1]
            result[name] = {
                "latest": latest,
                "7d_mean": avg,
                "7d_std": sd,
                "trend_label": trend_label(latest, avg, sd, higher_is_better=cfg["higher_is_better"]),
            }

        return {
            "user_id": str(user_id),
            "date": str(date),
            "window_days": len(window),
            "metrics": result,
        }