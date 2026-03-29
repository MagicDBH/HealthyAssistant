from __future__ import annotations

from typing import Dict, Any


def rewrite_query_locally(summary: Dict[str, Any], user_query: str, question_type: str) -> str:
    """
    本地重写：给 OpenClaw 前置一个更适合推理的问句。
    不依赖外部 LLM。
    """
    if question_type == "work_meeting":
        return f"结合我当前的睡眠、压力和恢复状态，明天我适合参加会议或处理高压工作吗？如果不适合，应该如何调整？原问题：{user_query}"
    if question_type == "exercise":
        return f"结合我当前的活动量、睡眠和恢复状态，我今天/最近适合进行什么强度的运动？是否需要调整训练计划？原问题：{user_query}"
    if question_type == "sleep":
        return f"结合我最近的睡眠和压力趋势，我应该如何调整作息和恢复节奏？原问题：{user_query}"
    if question_type == "travel":
        return f"结合我当前的疲劳、睡眠和压力状态，我是否适合出行/通勤/赶路？如果要出行，需要注意什么？原问题：{user_query}"
    if question_type == "stress_recovery":
        return f"结合我当前的压力、恢复和睡眠状态，我现在最需要什么样的恢复方式？原问题：{user_query}"
    return f"结合我当前的健康数据和近7天趋势，请回答以下问题并给出个性化建议：{user_query}"