from __future__ import annotations

from typing import Dict, Any


def classify_question(user_query: str) -> str:
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


def build_openclaw_context(summary: Dict[str, Any], user_query: str, rewritten_query: str, question_type: str) -> Dict[str, Any]:
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
    mapping = {
        "work_meeting": "重点关注压力、恢复、睡眠、心率、RMSSD、静息心率、疲劳和注意力状态。",
        "exercise": "重点关注活动水平、步数、卡路里、活跃分钟、久坐、恢复和睡眠。",
        "sleep": "重点关注睡眠时长、效率、入睡时长、睡眠结构和压力恢复。",
        "travel": "重点关注疲劳、睡眠、压力、活动负荷与当天状态波动。",
        "stress_recovery": "重点关注压力、恢复、静息心率、RMSSD、睡眠和休息需求。",
        "general_health": "综合关注活动、睡眠、压力与趋势摘要。",
    }
    return mapping.get(question_type, mapping["general_health"])