from __future__ import annotations

from typing import Dict, Any


def rewrite_query_locally(summary: Dict[str, Any], user_query: str, question_type: str) -> str:
    """使用基于规则的模板，根据用户当前状态改写其健康问题。

    此函数是将查询发送到外部 LLM 改写器的**本地零延迟替代方案**。
    它生成一个上下文丰富的问题，在生成第一个 token 之前，
    用最相关的健康维度为 OpenClaw 的语言模型做好准备。

    每个模板：

    * 确认 *question_type* 所暗示的特定健康领域。
    * 指示 OpenClaw 评估用户的适合程度/准备情况。
    * 如有必要，要求提供具体可执行的调整建议。
    * 附加原始问题以保留用户的意图原文。

    参数：
        summary: 由技能管道生成的合并摘要字典（``user_id``、``date``、``daily``、
            ``metrics``）。目前未被基于规则的模板使用，
            但为与任何未来 LLM 改写器的 API 保持一致而接受该参数。
        user_query: 用户输入的原始问题文本。
        question_type: 由
            :func:`~scripts.prompt_builder.classify_question` 返回的六个类别字符串之一：
            ``"work_meeting"``、``"exercise"``、``"sleep"``、
            ``"travel"``、``"stress_recovery"`` 或 ``"general_health"``。

    返回：
        中文改写问题字符串，嵌入了相关健康上下文，
        可作为上下文载荷的 ``rewritten_query`` 字段传递给 OpenClaw。

    触发条件：
        在每次技能调用中，紧接
        :func:`~scripts.prompt_builder.classify_question` 返回后调用一次，
        并在 :func:`~scripts.openclaw_payload.build_payload` 组装最终载荷之前。

    示例::

        rewrite_query_locally(summary, "我明天要开会，怎么调整？", "work_meeting")
        # → "结合我当前的睡眠、压力和恢复状态，明天我适合参加会议或处理高压工作吗？..."
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