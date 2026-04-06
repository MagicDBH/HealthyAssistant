from __future__ import annotations

from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd

from .metrics import safe_float, mean, std, trend_label


class JianDataParser:
    """解析并汇总来自 LifeSnaps 衍生的 ``jian.csv`` 文件中的健康数据。

    这是技能管道中所有数据操作的**入口点**。
    它在实例化时接收 CSV 路径，然后用于生成每日快照
    和7天滚动摘要，作为提示构建器的输入。

    触发条件：
        在每次技能调用开始时实例化并调用，在
        问题分类或查询改写之前。典型调用序列如下::

            parser = JianDataParser(csv_path)
            daily  = parser.build_daily_summary(user_id, date)
            week   = parser.build_7day_summary(user_id, date)

    属性：
        csv_path: CSV 数据文件的解析路径。
        df: 已加载的 ``pandas.DataFrame``；在调用 :meth:`load` 之前为 ``None``。
    """

    def __init__(self, csv_path: str) -> None:
        """使用 CSV 数据文件的路径初始化解析器。

        参数：
            csv_path: ``jian.csv`` 的绝对或相对路径（或任何具有相同
                模式的文件）。文件在调用 :meth:`load`（或调用它的方法）
                之前不会被读取。
        """
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """将 CSV 文件读取到内存中并解析 ``date`` 列。

        返回：
            已加载的 ``pandas.DataFrame``，其中 ``date`` 列被转换为
            ``datetime64`` 类型。

        异常：
            FileNotFoundError: 如果 ``csv_path`` 未指向现有文件。

        触发条件：
            在第一次需要数据时由 :meth:`_ensure_loaded` 延迟调用。
            也可以显式调用以预加载文件。
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        return self.df

    def _ensure_loaded(self) -> None:
        """确保在尝试查询 CSV 之前已加载文件。

        触发条件：
            由每个公共数据访问方法在内部调用。
        """
        if self.df is None:
            self.load()

    def get_user_daily_row(self, user_id: str, date: str) -> Dict[str, Any]:
        """返回匹配 *user_id* 和 *date* 的单个 CSV 行。

        参数：
            user_id: 在 ``id`` 列中出现的用户标识符。
            date: ISO-8601 格式的日期字符串，例如 ``"2021-07-31"``。

        返回：
            将列名映射到匹配行原始值的字典。

        异常：
            ValueError: 如果未找到给定 ``user_id`` / ``date`` 组合的行。

        触发条件：
            由 :meth:`build_daily_summary` 调用，以获取今日健康快照的原始值。
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
        """返回落在以 *date* 结束（含）的7天内的行。

        窗口在左侧是**开放的**，即包含 ``(date − 7 天, date]``。

        参数：
            user_id: 在 ``id`` 列中出现的用户标识符。
            date: 滚动窗口的结束日期（含），ISO-8601 格式，
                例如 ``"2021-07-31"``。

        返回：
            最多包含7行的 ``pandas.DataFrame``，按日期升序排列。

        触发条件：
            由 :meth:`build_7day_summary` 调用，以收集趋势计算所需的原始值。
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
        """构建用户单日健康数据的结构化快照。

        快照分为五个子部分，直接映射到 ``skill.md``（§4.1）中定义的类别：

        * ``profile``  – 静态人口统计属性。
        * ``activity`` – 步数 / 卡路里 / 活跃分钟数指标。
        * ``sleep``    – 睡眠时长、效率和睡眠阶段比例。
        * ``stress``   – HRV、静息心率和压力/恢复评分。
        * ``context``  – 位置时间比例（家、工作、交通等）。

        参数：
            user_id: 在 ``id`` 列中出现的用户标识符。
            date: ISO-8601 格式的目标日期（例如 ``"2021-07-31"``）。

        返回：
            适合直接用作 OpenClaw 上下文载荷中 ``daily`` 字段的嵌套字典。

        触发条件：
            在接收到用户问题后，技能管道中第一个被调用的函数。
            结果传递给 :func:`~scripts.prompt_builder.classify_question`，
            并随后由 :func:`~scripts.openclaw_payload.build_payload` 合并到最终载荷中。
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
        """计算关键健康指标的滚动7天统计数据。

        对于每个指标，摘要包含：

        * ``latest``      – *date*（今日）的值。
        * ``7d_mean``     – 窗口内的均值。
        * ``7d_std``      – 窗口内的样本标准差。
        * ``trend_label`` – 相对于基线的 ``"high"``、``"medium"`` 或 ``"low"``
          （参见 :func:`~scripts.metrics.trend_label`）。

        参数：
            user_id: 在 ``id`` 列中出现的用户标识符。
            date: ISO-8601 格式的目标日期（例如 ``"2021-07-31"``）。

        返回：
            包含键 ``user_id``、``date``、``window_days`` 和
            ``metrics`` 的字典。``metrics`` 子字典以指标名称为键，
            直接由 :func:`~scripts.prompt_builder.build_rewrite_prompt` 和
            :func:`~scripts.prompt_builder.build_openclaw_context` 使用。

        触发条件：
            在技能管道中紧接 :meth:`build_daily_summary` 之后调用。
            两个结果被合并为一个 ``summary`` 字典，流经管道的其余部分。
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