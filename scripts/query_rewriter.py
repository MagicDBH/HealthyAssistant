from __future__ import annotations

from typing import Dict, Any


def rewrite_query_locally(summary: Dict[str, Any], user_query: str, question_type: str) -> str:
    """Rewrite a user's health question using rule-based templates grounded in their current state.

    This function is the **local, zero-latency alternative** to sending the
    query to an external LLM rewriter.  It produces a context-enriched question
    that primes OpenClaw's language model with the most relevant health
    dimensions *before* a single token is generated.

    Each template:

    * Acknowledges the specific health domain implied by *question_type*.
    * Instructs OpenClaw to evaluate the user's suitability / readiness.
    * Asks for concrete, actionable adjustments if needed.
    * Appends the original question so the user's intent is preserved verbatim.

    Args:
        summary: The merged summary dict (``user_id``, ``date``, ``daily``,
            ``metrics``) produced by the skill pipeline.  Currently unused by
            the rule-based templates but accepted for API parity with any
            future LLM-based rewriter.
        user_query: The original question text entered by the user.
        question_type: One of the six category strings returned by
            :func:`~scripts.prompt_builder.classify_question`:
            ``"work_meeting"``, ``"exercise"``, ``"sleep"``,
            ``"travel"``, ``"stress_recovery"``, or ``"general_health"``.

    Returns:
        A rewritten question string in Chinese that embeds the relevant health
        context and is ready to be passed to OpenClaw as the ``rewritten_query``
        field of the context payload.

    Trigger condition:
        Called once per skill invocation immediately after
        :func:`~scripts.prompt_builder.classify_question` returns, and before
        :func:`~scripts.openclaw_payload.build_payload` assembles the final
        payload.

    Example::

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