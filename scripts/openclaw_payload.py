from __future__ import annotations

from typing import Dict, Any

from .prompt_builder import build_openclaw_context


def build_payload(
    summary: Dict[str, Any],
    original_query: str,
    rewritten_query: str,
    question_type: str,
) -> Dict[str, Any]:
    """组装并返回技能调用的最终 OpenClaw 上下文载荷。

    这是技能管道中**最后调用的函数**。它委托给
    :func:`~scripts.prompt_builder.build_openclaw_context`，
    作为薄封装存在，以便调用方（如 :mod:`scripts.prototype_cli`）
    与单一稳定的公共接口交互。

    参数：
        summary: 包含 ``user_id``、``date``、
            ``daily``（来自
            :meth:`~scripts.data_parser.JianDataParser.build_daily_summary`）
            和 ``metrics``（来自
            :meth:`~scripts.data_parser.JianDataParser.build_7day_summary`）的合并摘要字典。
        original_query: 用户输入的原始问题文本，在载荷中原样保留。
        rewritten_query: 由
            :func:`~scripts.query_rewriter.rewrite_query_locally`（或外部 LLM 改写器）
            生成的上下文丰富改写。
        question_type: 由
            :func:`~scripts.prompt_builder.classify_question` 返回的六个类别字符串之一。

    返回：
        可 JSON 序列化的字典，可作为 OpenClaw 代理的输入上下文传入。
        参见 :func:`~scripts.prompt_builder.build_openclaw_context` 了解完整字段规范。

    触发条件：
        在问题分类和查询改写完成后，作为
        :func:`~scripts.prototype_cli.main` 中的最后一步调用。

    示例::

        payload = build_payload(summary, "我今天适合运动吗？", rewritten, "exercise")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    """
    return build_openclaw_context(
        summary=summary,
        user_query=original_query,
        rewritten_query=rewritten_query,
        question_type=question_type,
    )