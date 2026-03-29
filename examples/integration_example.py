"""Integration example for the Sensor-in-the-Loop Health Assistant skill.

This self-contained script demonstrates the complete skill pipeline for several
representative user queries without requiring a real CSV file.  It uses a small
in-memory dataset so you can run it straight away:

    python examples/integration_example.py

For production use, replace ``SAMPLE_CSV`` with the path to your actual
``data/jian.csv`` file (or set the ``DATA_PATH`` environment variable).
"""
from __future__ import annotations

import io
import json
import sys
import os

# ---------------------------------------------------------------------------
# Allow running this script from both the repo root and the examples/ folder.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Minimal sample CSV – one user (id=1), two consecutive days.
# ---------------------------------------------------------------------------
SAMPLE_CSV = """\
id,date,calories,distance,steps,lightly_active_minutes,moderately_active_minutes,very_active_minutes,sedentary_minutes,sleep_duration,minutesToFallAsleep,minutesAsleep,minutesAwake,minutesAfterWakeup,sleep_efficiency,sleep_deep_ratio,sleep_wake_ratio,sleep_light_ratio,sleep_rem_ratio,rmssd,resting_hr,nremhr,stress_score,sleep_points_percentage,responsiveness_points_percentage,HOME,HOME_OFFICE,WORK/SCHOOL,OUTDOORS,TRANSIT,OTHER,age,gender,bmi,step_goal,step_goal_label
1,2021-07-30,2100,5.8,7200,170,18,5,640,6.2,20,372,38,8,87,0.13,0.09,0.54,0.24,27.0,70,62,75,0.58,0.55,0.40,0.20,0.30,0.07,0.02,0.01,32,male,24.1,8000,active
1,2021-07-31,2150,6.2,7340,185,22,8,620,5.9,18,354,41,7,88,0.14,0.10,0.52,0.24,28.5,68,61,72,0.61,0.58,0.42,0.21,0.27,0.06,0.03,0.01,32,male,24.1,8000,active
"""

# ---------------------------------------------------------------------------
# Write the sample CSV to a temporary file so JianDataParser can read it.
# ---------------------------------------------------------------------------
import tempfile, pathlib

_tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
_tmp.write(SAMPLE_CSV)
_tmp.close()
SAMPLE_CSV_PATH = _tmp.name

# ---------------------------------------------------------------------------
# Import skill pipeline components.
# ---------------------------------------------------------------------------
from scripts.data_parser import JianDataParser
from scripts.prompt_builder import classify_question
from scripts.query_rewriter import rewrite_query_locally
from scripts.openclaw_payload import build_payload

USER_ID = "1"
DATE    = "2021-07-31"

# ---------------------------------------------------------------------------
# Example queries covering all six question categories.
# ---------------------------------------------------------------------------
EXAMPLE_QUERIES = [
    ("work_meeting",    "我明天要开会，今天该怎么调整？"),
    ("exercise",        "我今天适合去跑步吗？"),
    ("sleep",           "我昨晚睡得怎么样，今天会不会很疲？"),
    ("travel",          "我明天要坐早班飞机，状态够吗？"),
    ("stress_recovery", "我最近是不是压力太大了？"),
    ("general_health",  "我今天身体状态怎么样？"),
]


def run_pipeline(user_query: str) -> dict:
    """Run the full skill pipeline for a single query and return the payload."""
    parser  = JianDataParser(SAMPLE_CSV_PATH)
    daily   = parser.build_daily_summary(USER_ID, DATE)
    week    = parser.build_7day_summary(USER_ID, DATE)

    summary = {
        "user_id": daily["user_id"],
        "date":    daily["date"],
        "daily":   daily,
        "metrics": week["metrics"],
    }

    question_type   = classify_question(user_query)
    rewritten_query = rewrite_query_locally(summary, user_query, question_type)
    payload         = build_payload(summary, user_query, rewritten_query, question_type)
    return payload


def main() -> None:
    print("=" * 70)
    print("Sensor-in-the-Loop Health Assistant – Integration Examples")
    print("=" * 70)

    for expected_type, query in EXAMPLE_QUERIES:
        print(f"\n{'─' * 60}")
        print(f"Query : {query}")
        print(f"Expected category: {expected_type}")

        payload = run_pipeline(query)

        print(f"Detected category: {payload['question_type']}")
        print(f"Rewritten query  : {payload['rewritten_query'][:80]}...")
        print(f"Answer focus     : {payload['answer_focus']}")

        # Verify the detected category matches expectation.
        assert payload["question_type"] == expected_type, (
            f"Category mismatch: expected {expected_type!r}, "
            f"got {payload['question_type']!r}"
        )

    print(f"\n{'=' * 70}")
    print("All examples completed successfully.")
    print(f"{'=' * 70}\n")

    # Print the full payload for the last example so the user can inspect it.
    print("Full payload for the last example (general_health):")
    print(json.dumps(payload, ensure_ascii=False, indent=2))  # noqa: F821


if __name__ == "__main__":
    try:
        main()
    finally:
        # Clean up the temporary CSV file.
        pathlib.Path(SAMPLE_CSV_PATH).unlink(missing_ok=True)
