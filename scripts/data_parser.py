from __future__ import annotations

from typing import Dict, Any
from pathlib import Path
import pandas as pd

from .metrics import safe_float, mean, std, trend_label


class JianDataParser:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None

    def load(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        return self.df

    def _ensure_loaded(self):
        if self.df is None:
            self.load()

    def get_user_daily_row(self, user_id: str, date: str) -> Dict[str, Any]:
        self._ensure_loaded()
        target_date = pd.to_datetime(date, errors="coerce")

        df = self.df.copy()
        df["id"] = df["id"].astype(str)

        row = df[(df["id"] == str(user_id)) & (df["date"] == target_date)]
        if row.empty:
            raise ValueError(f"No record found for user_id={user_id}, date={date}")

        return row.iloc[0].to_dict()

    def get_7day_window(self, user_id: str, date: str):
        self._ensure_loaded()
        target_date = pd.to_datetime(date, errors="coerce")

        df = self.df.copy()
        df["id"] = df["id"].astype(str)

        user_df = df[df["id"] == str(user_id)].sort_values("date")
        window = user_df[(user_df["date"] <= target_date) & (user_df["date"] > target_date - pd.Timedelta(days=7))]
        return window

    def build_daily_summary(self, user_id: str, date: str) -> Dict[str, Any]:
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
        window = self.get_7day_window(user_id, date)

        def col_values(col):
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

        result = {}
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