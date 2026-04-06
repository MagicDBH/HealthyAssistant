from __future__ import annotations

from typing import List, Optional
import math


def safe_float(v: object) -> Optional[float]:
    """将值转换为浮点数，如果无法转换则返回 None。

    参数：
        v: 要转换的值，可以是任何类型。

    返回：
        ``v`` 的浮点表示，如果值为
        ``None``、空字符串或无法转换为浮点数，则返回 ``None``。

    触发条件：
        每当 ``JianDataParser`` 读取原始 CSV 单元格值时调用，
        以便将缺失或格式错误的条目表示为 ``None``
        而不是在下游引发异常。
    """
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def mean(values: List[Optional[float]]) -> float:
    """计算列表的算术平均值，忽略 ``None`` 条目。

    参数：
        values: 可能包含 ``None`` 的数值列表。

    返回：
        非 ``None`` 值的均值，如果过滤后列表为空则返回 ``0.0``。

    触发条件：
        当 ``JianDataParser.build_7day_summary`` 在滚动7天窗口中
        汇总每个指标时调用。
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def std(values: List[Optional[float]]) -> float:
    """计算列表的样本标准差，忽略 ``None`` 条目。

    参数：
        values: 可能包含 ``None`` 的数值列表。

    返回：
        非 ``None`` 值的样本标准差，当有效值少于两个时
        返回 ``0.0``。

    触发条件：
        由 ``JianDataParser.build_7day_summary`` 与
        :func:`mean` 一起调用，为每个指标提供离散度量。
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
    """将指标值相对于其7天基线分类为 ``"high"``、``"medium"`` 或 ``"low"``。

    阈值为均值的 ±0.5 标准差：

    * ``"high"`` – 值高于上限阈值（或当 *higher_is_better* 为 ``False`` 时
      低于下限阈值）。
    * ``"low"``  – ``"high"`` 的相反情况。
    * ``"medium"`` – 值落在均值 ±0.5 标准差范围内，或当标准差为零时。

    参数：
        value: 最新（今日）的指标值。
        avg: 指标的7天均值。
        sd: 指标的7天样本标准差。
        higher_is_better: 当为 ``True``（默认）时，高于均值的值
            标记为 ``"high"``（好）；当为 ``False`` 时，*低于*均值的值
            为 ``"high"``（好）。例如，*resting_hr* 和 *stress_score*
            使用 ``higher_is_better=False``。

    返回：
        ``"high"``、``"medium"`` 或 ``"low"`` 之一。

    触发条件：
        在 :func:`mean` 和 :func:`std` 计算完成后，
        在 ``JianDataParser.build_7day_summary`` 内为每个指标调用一次。
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