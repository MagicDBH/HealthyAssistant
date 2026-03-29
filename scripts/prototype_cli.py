from __future__ import annotations

import argparse
import json

from .config import settings
from .data_parser import JianDataParser
from .prompt_builder import classify_question
from .query_rewriter import rewrite_query_locally
from .openclaw_payload import build_payload


def main():
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