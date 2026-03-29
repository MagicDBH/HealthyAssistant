from __future__ import annotations

from typing import Dict, Any

from .prompt_builder import build_openclaw_context


def build_payload(summary: Dict[str, Any], original_query: str, rewritten_query: str, question_type: str) -> Dict[str, Any]:
    return build_openclaw_context(
        summary=summary,
        user_query=original_query,
        rewritten_query=rewritten_query,
        question_type=question_type,
    )