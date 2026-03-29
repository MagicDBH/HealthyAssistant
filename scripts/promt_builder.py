from __future__ import annotations

from typing import Dict, Any


def classify_question(user_query: str) -> str:
    """Classify a user's free-text question into one of six pre-defined categories.

    The classification is keyword-based and operates on the lowercased query.
    It is intentionally simple and fast – no LLM call is required.

    Categories (in priority order):

    * ``"work_meeting"``   – questions about meetings, work performance, exams,
      presentations, overtime, or high-pressure tasks.
    * ``"exercise"``       – questions about workouts, running, steps, weight
      loss, or muscle gain.
    * ``"sleep"``          – questions about sleep quality, bedtime habits,
      all-nighters, or catching up on sleep.
    * ``"travel"``         – questions about commuting, flights, trains, business
      trips, or jet lag.
    * ``"stress_recovery"``– questions about stress levels, fatigue, anxiety,
      relaxation, or recovery.
    * ``"general_health"`` – fallback for any other health-related question.

    Args:
        user_query: The raw question text entered by the user.

    Returns:
        One of the six category strings listed above.

    Trigger condition:
        Called once per skill invocation immediately after
        :meth:`~scripts.data_parser.JianDataParser.build_daily_summary` returns.
        The returned category drives both query rewriting and the ``answer_focus``
        hint injected into the OpenClaw payload.
    """
    q = user_query.lower()

    if any(k in q for k in ["会议", "开会", "演讲", "工作", "考试", "项目", "加班", "任务", "汇报"]):
        return "work_meeting"
    if any(k in q for k in ["运动", "跑步", "健身", "步数", "训练", "减脂", "增肌"]):
        return "exercise"
    if any(k in q for k in ["睡眠", "作息", "熬夜", "睡得", "入睡", "补觉"]):
        return "sleep"
    if any(k in q for k in ["出行", "旅行", "通勤", "飞机", "高铁", "出差", "时差", "赶路"]):
        return "travel"
    if any(k in q for k in ["压力", "疲劳", "累", "恢复", "焦虑", "放松"]):
        return "stress_recovery"
    return "general_health"


def build_rewrite_prompt(summary: Dict[str, Any], user_query: str) -> str:
    """Build a structured Chinese-language prompt that instructs an LLM to rewrite the user's query.

    The prompt embeds a compact metric-trend snapshot so the LLM can ground
    the rewritten question in the user's actual health state.

    Args:
        summary: The merged summary dict produced by the skill pipeline,
            expected to contain a ``"metrics"`` key whose value is a dict of
            ``{metric_name: {"trend_label": str, ...}}``.
        user_query: The original question text entered by the user.

    Returns:
        A multi-line string ready to be sent as the system or user message to
        the rewriting LLM.

    Trigger condition:
        Called only when an external LLM-powered rewrite is desired (i.e. when
        the caller opts *not* to use the local rule-based rewriter in
        :mod:`scripts.query_rewriter`).  In the default CLI pipeline
        :func:`~scripts.query_rewriter.rewrite_query_locally` is used instead.
    """
    metrics = summary.get("metrics", {})
    compact = []
    for k, v in metrics.items():
        compact.append(f"{k}:{v.get('trend_label')}")

    return f"""
请执行内部查询重写任务，不要输出推理过程。

步骤1：分析用户状态摘要，识别关键因素。
步骤2：确定重写目标（减压 / 提升生产力 / 情感支持 / 睡眠优化 / 运动建议 / 出行准备 / 恢复建议）。
步骤3：把用户问题重写为更适合当前状态的版本。

【状态摘要】
{", ".join(compact)}

【用户问题】
{user_query}

【输出要求】
仅输出重写后的问题句子。
""".strip()


def build_openclaw_context(
    summary: Dict[str, Any],
    user_query: str,
    rewritten_query: str,
    question_type: str,
) -> Dict[str, Any]:
    """Assemble the structured context payload that OpenClaw uses to generate a personalised reply.

    The returned dictionary is the **final output** of the skill pipeline.
    OpenClaw reads it and uses the embedded health state, rewritten question,
    and ``answer_focus`` hint to produce a contextually grounded response in
    the user's language.

    Args:
        summary: The merged summary dict (``user_id``, ``date``, ``daily``,
            ``metrics``) produced by the skill pipeline.
        user_query: The original question text entered by the user.
        rewritten_query: The rewritten question produced by
            :func:`~scripts.query_rewriter.rewrite_query_locally` or an
            external LLM rewriter.
        question_type: One of the six category strings returned by
            :func:`classify_question`.

    Returns:
        A JSON-serialisable dictionary containing:

        * ``question_type``            – category string.
        * ``original_query``           – unmodified user question.
        * ``rewritten_query``          – context-enriched version of the question.
        * ``user_state``               – full nested health summary.
        * ``answer_focus``             – natural-language hint about which metrics
          to prioritise in the reply.
        * ``output_style``             – style constraint string for the LLM.
        * ``do_not_show_chain_of_thought`` – flag instructing OpenClaw to hide
          internal reasoning from the end user.

    Trigger condition:
        Called by :func:`~scripts.openclaw_payload.build_payload` as the last
        step of the skill pipeline, after question classification and query
        rewriting are complete.
    """
    return {
        "question_type": question_type,
        "original_query": user_query,
        "rewritten_query": rewritten_query,
        "user_state": summary,
        "answer_focus": _answer_focus(question_type),
        "output_style": "中文、具体、可执行、温和、避免过度医疗化",
        "do_not_show_chain_of_thought": True,
    }


def _answer_focus(question_type: str) -> str:
    """Return a natural-language description of which health metrics to emphasise for a given question type.

    Args:
        question_type: One of the six category strings returned by
            :func:`classify_question`.

    Returns:
        A Chinese-language sentence naming the most relevant metrics for the
        category.  Falls back to the ``"general_health"`` description for
        unrecognised category strings.

    Trigger condition:
        Called internally by :func:`build_openclaw_context`.
    """
    mapping = {
        "work_meeting": "重点关注压力、恢复、睡眠、心率、RMSSD、静息心率、疲劳和注意力状态。",
        "exercise": "重点关注活动水平、步数、卡路里、活跃分钟、久坐、恢复和睡眠。",
        "sleep": "重点关注睡眠时长、效率、入睡时长、睡眠结构和压力恢复。",
        "travel": "重点关注疲劳、睡眠、压力、活动负荷与当天状态波动。",
        "stress_recovery": "重点关注压力、恢复、静息心率、RMSSD、睡眠和休息需求。",
        "general_health": "综合关注活动、睡眠、压力与趋势摘要。",
    }
    return mapping.get(question_type, mapping["general_health"])