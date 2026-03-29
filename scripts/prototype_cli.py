"""面向传感器在环健康助手技能的命令行界面。

本模块提供了用于测试和本地开发的轻量级 CLI 入口点。
它端到端地执行完整的技能管道：

1. 从 CSV 文件解析健康数据（:class:`~scripts.data_parser.JianDataParser`）。
2. 对用户问题进行分类（:func:`~scripts.prompt_builder.classify_question`）。
3. 用健康上下文改写问题（:func:`~scripts.query_rewriter.rewrite_query_locally`）。
4. 构建 OpenClaw 载荷（:func:`~scripts.openclaw_payload.build_payload`）。
5. 将生成的 JSON 打印到标准输出。

用法::

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
    """原型 CLI 的入口点。

    解析命令行参数，运行完整的技能管道，并将
    生成的 OpenClaw 载荷以格式化 JSON 打印到标准输出。

    触发条件：
        通过 ``python -m scripts.prototype_cli`` 直接调用，或通过
        ``pyproject.toml`` / ``setup.py`` 中定义的
        ``skill_cli`` 控制台脚本入口点调用。
    """
    parser = argparse.ArgumentParser(description="OpenClaw 传感器在环健康助手")
    parser.add_argument("--data", default=settings.data_path, help="data/jian.csv 的路径")
    parser.add_argument("--user-id", required=True, help="id 列中的用户 ID")
    parser.add_argument("--date", required=True, help="目标日期，例如 2021-07-31")
    parser.add_argument("--query", required=True, help="用户问题")
    parser.add_argument("--show-summary", action="store_true", help="打印解析摘要")
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