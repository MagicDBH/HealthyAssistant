"""Command-line interface for the Sensor-in-the-Loop Health Assistant skill.

This module provides a lightweight CLI entry point for testing and local
development.  It exercises the full skill pipeline end-to-end:

1. Parse health data from a CSV file (:class:`~scripts.data_parser.JianDataParser`).
2. Classify the user's question (:func:`~scripts.prompt_builder.classify_question`).
3. Rewrite the question with health context (:func:`~scripts.query_rewriter.rewrite_query_locally`).
4. Build the OpenClaw payload (:func:`~scripts.openclaw_payload.build_payload`).
5. Print the resulting JSON to stdout.

Usage::

    python -m scripts.prototype_cli \\
        --data data/jian.csv \\
        --user-id 122 \\
        --date 2021-07-31 \\
        --query "我明天要开会，今天该怎么调整？" \\
        --show-summary
"""
from __future__ import annotations

import argparse
import json

from .config import settings
from .data_parser import JianDataParser
from .prompt_builder import classify_question
from .query_rewriter import rewrite_query_locally
from .openclaw_payload import build_payload


def main() -> None:
    """Entry point for the prototype CLI.

    Parses command-line arguments, runs the full skill pipeline, and prints
    the resulting OpenClaw payload as pretty-printed JSON to stdout.

    Trigger condition:
        Invoked directly via ``python -m scripts.prototype_cli`` or through
        the ``skill_cli`` console script entry point defined in
        ``pyproject.toml`` / ``setup.py``.
    """
    parser = argparse.ArgumentParser(description="OpenClaw Sensor-in-the-Loop Health Assistant")
    parser.add_argument("--data", default=settings.data_path, help="Path to data/jian.csv")
    parser.add_argument("--user-id", required=True, help="User id from the id column")
    parser.add_argument("--date", required=True, help="Target date, e.g. 2021-07-31")
    parser.add_argument("--query", required=True, help="User question")
    parser.add_argument("--show-summary", action="store_true", help="Print parsed summary")
    args = parser.parse_args()

    dp = JianDataParser(args.data)
    daily = dp.build_daily_summary(args.user_id, args.date)
    summary7 = dp.build_7day_summary(args.user_id, args.date)

    summary = {
        "user_id": daily["user_id"],
        "date": daily["date"],
        "daily": daily,
        "metrics": summary7["metrics"],
    }

    question_type = classify_question(args.query)
    rewritten_query = rewrite_query_locally(summary, args.query, question_type)
    payload = build_payload(summary, args.query, rewritten_query, question_type)

    if args.show_summary:
        print("=== SUMMARY ===")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("\n=== QUESTION TYPE ===")
        print(question_type)
        print("\n=== REWRITTEN QUERY ===")
        print(rewritten_query)

    print("\n=== OPENCLAW PAYLOAD ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()