from __future__ import annotations

from typing import Dict, Any

from .prompt_builder import build_openclaw_context


def build_payload(
    summary: Dict[str, Any],
    original_query: str,
    rewritten_query: str,
    question_type: str,
) -> Dict[str, Any]:
    """Assemble and return the final OpenClaw context payload for the skill invocation.

    This is the **last function called** in the skill pipeline.  It delegates
    to :func:`~scripts.prompt_builder.build_openclaw_context` and exists as a
    thin wrapper so that callers (e.g. :mod:`scripts.prototype_cli`) interact
    with a single, stable public surface.

    Args:
        summary: The merged summary dict containing ``user_id``, ``date``,
            ``daily`` (from
            :meth:`~scripts.data_parser.JianDataParser.build_daily_summary`)
            and ``metrics`` (from
            :meth:`~scripts.data_parser.JianDataParser.build_7day_summary`).
        original_query: The raw question text entered by the user, preserved
            verbatim in the payload.
        rewritten_query: The context-enriched rewrite produced by
            :func:`~scripts.query_rewriter.rewrite_query_locally` (or an
            external LLM rewriter).
        question_type: One of the six category strings returned by
            :func:`~scripts.prompt_builder.classify_question`.

    Returns:
        A JSON-serialisable dictionary ready to be passed to the OpenClaw
        agent as its input context.  See
        :func:`~scripts.prompt_builder.build_openclaw_context` for the full
        field specification.

    Trigger condition:
        Called as the final step in :func:`~scripts.prototype_cli.main` after
        question classification and query rewriting are complete.

    Example::

        payload = build_payload(summary, "我今天适合运动吗？", rewritten, "exercise")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    """
    return build_openclaw_context(
        summary=summary,
        user_query=original_query,
        rewritten_query=rewritten_query,
        question_type=question_type,
    )