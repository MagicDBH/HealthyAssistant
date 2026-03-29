# Integration Guide – Sensor-in-the-Loop Health Assistant

This guide explains how to integrate the **Sensor-in-the-Loop Personalized Health Assistant** skill into [OpenClaw](https://openclaw.ai) or [Claude Code](https://claude.ai/code).

---

## 1. Prerequisites

| Requirement | Details |
|---|---|
| Python | ≥ 3.9 |
| pandas | any recent version |
| Health data | `data/jian.csv` (or set `DATA_PATH` env var) |

Install dependencies:

```bash
pip install pandas
```

---

## 2. Registering the Skill in OpenClaw

### 2.1 Using `skill_manifest.json`

OpenClaw discovers skills by reading `skill_manifest.json` in the skill root directory.  No manual registration is needed – place the repository folder inside OpenClaw's skill search path and restart the agent.

```
skills/
└── HealthyAssistant/        ← this repository
    ├── skill_manifest.json  ← auto-discovered by OpenClaw
    ├── skill.md
    └── scripts/
```

### 2.2 Manual registration (API)

If your OpenClaw deployment requires explicit registration, call the Skills API:

```python
import requests, json, pathlib

manifest = json.loads(pathlib.Path("skill_manifest.json").read_text())
requests.post(
    "https://<your-openclaw-host>/api/skills/register",
    json=manifest,
    headers={"Authorization": "Bearer <token>"},
).raise_for_status()
```

---

## 3. Registering the Skill in Claude Code

Add the skill manifest path to your `.claude/tools.json` configuration:

```json
{
  "tools": [
    {
      "name": "sensor_in_the_loop_health_assistant",
      "description": "Reads real wearable/sensor health data and returns a structured health context payload for personalised advice.",
      "manifest": "./skill_manifest.json",
      "entry": "scripts.prototype_cli:main"
    }
  ]
}
```

Claude Code will parse `skill_manifest.json` and expose each declared function as a callable tool.

---

## 4. Invoking the Skill Programmatically

The skill pipeline is a plain Python function chain.  You can embed it directly in your application:

```python
import json
from scripts.data_parser import JianDataParser
from scripts.prompt_builder import classify_question
from scripts.query_rewriter import rewrite_query_locally
from scripts.openclaw_payload import build_payload

# --- configuration ---
CSV_PATH   = "data/jian.csv"
USER_ID    = "122"
DATE       = "2021-07-31"
USER_QUERY = "我明天要开会，今天该怎么调整？"

# --- pipeline ---
parser  = JianDataParser(CSV_PATH)
daily   = parser.build_daily_summary(USER_ID, DATE)
week    = parser.build_7day_summary(USER_ID, DATE)

summary = {
    "user_id": daily["user_id"],
    "date":    daily["date"],
    "daily":   daily,
    "metrics": week["metrics"],
}

question_type    = classify_question(USER_QUERY)
rewritten_query  = rewrite_query_locally(summary, USER_QUERY, question_type)
payload          = build_payload(summary, USER_QUERY, rewritten_query, question_type)

# --- hand off to OpenClaw / your LLM ---
print(json.dumps(payload, ensure_ascii=False, indent=2))
```

---

## 5. Using the Command-Line Interface

For local testing, the `prototype_cli` module provides a ready-made CLI:

```bash
# Basic usage
python -m scripts.prototype_cli \
    --data data/jian.csv \
    --user-id 122 \
    --date 2021-07-31 \
    --query "我今天适合运动吗？"

# Show the intermediate summary and question type as well
python -m scripts.prototype_cli \
    --data data/jian.csv \
    --user-id 122 \
    --date 2021-07-31 \
    --query "我明天要开会，今天该怎么调整？" \
    --show-summary
```

The `DATA_PATH` environment variable overrides `--data`:

```bash
export DATA_PATH=/path/to/my/health_data.csv
python -m scripts.prototype_cli --user-id 122 --date 2021-07-31 --query "我最近睡眠怎么样？"
```

---

## 6. Payload Format

The skill returns a JSON object with the following fields:

```json
{
  "question_type":   "work_meeting",
  "original_query":  "我明天要开会，今天该怎么调整？",
  "rewritten_query": "结合我当前的睡眠、压力和恢复状态，明天我适合参加会议或处理高压工作吗？...",
  "user_state": {
    "user_id": "122",
    "date":    "2021-07-31",
    "daily":   { "profile": {}, "activity": {}, "sleep": {}, "stress": {}, "context": {} },
    "metrics": {
      "sleep_duration": { "latest": 6.5, "7d_mean": 7.1, "7d_std": 0.6, "trend_label": "low" }
    }
  },
  "answer_focus":                  "重点关注压力、恢复、睡眠、心率、RMSSD、静息心率、疲劳和注意力状态。",
  "output_style":                  "中文、具体、可执行、温和、避免过度医疗化",
  "do_not_show_chain_of_thought":  true
}
```

Pass this payload as the **system context** or **user message prefix** when calling your LLM.

---

## 7. Error Handling

| Exception | Cause | Recommended action |
|---|---|---|
| `FileNotFoundError` | CSV file missing | Check `DATA_PATH` / `--data` |
| `ValueError` | No row for user/date | Verify `user_id` and `date` exist in CSV |
| `KeyError` | Missing column in CSV | Ensure CSV matches the schema in `references/data_schema.md` |

---

## 8. Safety Disclaimer

This skill provides general wellness suggestions based on wearable sensor data.  
**It does not diagnose medical conditions, replace professional medical advice, or handle emergency health situations.**  
If a user reports a potential medical emergency, instruct them to contact emergency services immediately.

---

## 9. Full Example Output

See [`examples/example_output.json`](examples/example_output.json) for a complete sample payload.  
See [`examples/integration_example.py`](examples/integration_example.py) for a self-contained runnable example.
