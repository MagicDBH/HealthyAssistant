from __future__ import annotations

from typing import Dict, Any


def classify_question(user_query: str) -> str:
    """将用户的自由文本问题分类为六个预定义类别之一。

    分类基于关键词，对查询的小写形式进行操作。
    设计上简单快速——不需要调用 LLM。

    类别（按优先级排序）：

    * ``"work_meeting"``   – 关于会议、工作表现、考试、
      演讲、加班或高压任务的问题。
    * ``"exercise"``       – 关于锻炼、跑步、步数、减重
      或增肌的问题。
    * ``"sleep"``          – 关于睡眠质量、就寝习惯、
      熬夜或补觉的问题。
    * ``"travel"``         – 关于通勤、飞行、高铁、出差
      或时差的问题。
    * ``"stress_recovery"``– 关于压力水平、疲劳、焦虑、
      放松或恢复的问题。
    * ``"general_health"`` – 任何其他健康相关问题的后备类别。

    参数：
        user_query: 用户输入的原始问题文本。

    返回：
        上述六个类别字符串之一。

    触发条件：
        在每次技能调用中，紧接
        :meth:`~scripts.data_parser.JianDataParser.build_daily_summary` 返回后调用一次。
        返回的类别驱动查询改写以及注入 OpenClaw 载荷的 ``answer_focus`` 提示。
    """
    q = user_query.lower()

    if any(k in q for k in ["会议", "开会", "演讲", "工作", "考试", "项目", "加班", "任务", "汇报"]):
        return "work_meeting"
    if any(k in q for k in ["运动", "跑步", "健身", "步数", "训练", "减脂", "增肌"]):
        return "exercise"
    if any(k in q for k in ["睡眠", "作息", "熬夜", "睡得", "入睡", "补觉"]):
        return "sleep"
    if any(k in q for k in ["出行", "旅行", "通勤", "飞机", "高铁", "出差", "时差", "赶路"]):
        return "travel"
    if any(k in q for k in ["压力", "疲劳", "累", "恢复", "焦虑", "放松"]):
        return "stress_recovery"
    return "general_health"


def build_rewrite_prompt(summary: Dict[str, Any], user_query: str) -> str:
    """构建结构化的中文提示，指示 LLM 改写用户的查询。

    提示嵌入了一个紧凑的指标趋势快照，以便 LLM 能够将
    改写后的问题与用户的实际健康状态相联系。

    参数：
        summary: 由技能管道生成的合并摘要字典，
            预期包含 ``"metrics"`` 键，其值为
            ``{metric_name: {"trend_label": str, ...}}`` 格式的字典。
        user_query: 用户输入的原始问题文本。

    返回：
        可作为系统或用户消息发送到改写 LLM 的多行字符串。

    触发条件：
        仅在需要外部 LLM 驱动的改写时调用（即调用方选择
        *不*使用 :mod:`scripts.query_rewriter` 中的本地基于规则的改写器）。
        在默认 CLI 管道中，使用
        :func:`~scripts.query_rewriter.rewrite_query_locally` 代替。
    """
    metrics = summary.get("metrics", {})
    compact = []
    for k, v in metrics.items():
        compact.append(f"{k}:{v.get('trend_label')}")

    return f"""
请执行内部查询重写任务，不要输出推理过程。

步骤1：分析用户状态摘要，识别关键因素。
步骤2：确定重写目标（减压 / 提升生产力 / 情感支持 / 睡眠优化 / 运动建议 / 出行准备 / 恢复建议）。
步骤3：把用户问题重写为更适合当前状态的版本。

【状态摘要】
{", ".join(compact)}

【用户问题】
{user_query}

【输出要求】
仅输出重写后的问题句子。
""".strip()


def build_openclaw_context(
    summary: Dict[str, Any],
    user_query: str,
    rewritten_query: str,
    question_type: str,
) -> Dict[str, Any]:
    """组装 OpenClaw 用于生成个性化回复的结构化上下文载荷。

    返回的字典是技能管道的**最终输出**。
    OpenClaw 读取它，并使用嵌入的健康状态、改写后的问题
    和 ``answer_focus`` 提示，以用户语言生成有上下文依据的回复。

    参数：
        summary: 由技能管道生成的合并摘要字典（``user_id``、``date``、``daily``、
            ``metrics``）。
        user_query: 用户输入的原始问题文本。
        rewritten_query: 由
            :func:`~scripts.query_rewriter.rewrite_query_locally` 或外部
            LLM 改写器生成的改写问题。
        question_type: 由
            :func:`classify_question` 返回的六个类别字符串之一。

    返回：
        包含以下字段的可 JSON 序列化字典：

        * ``question_type``            – 类别字符串。
        * ``original_query``           – 未修改的用户问题。
        * ``rewritten_query``          – 问题的上下文丰富版本。
        * ``user_state``               – 完整的嵌套健康摘要。
        * ``answer_focus``             – 关于在回复中优先考虑哪些指标的自然语言提示。
        * ``output_style``             – LLM 的风格约束字符串。
        * ``do_not_show_chain_of_thought`` – 指示 OpenClaw 向最终用户隐藏
          内部推理的标志。

    触发条件：
        由 :func:`~scripts.openclaw_payload.build_payload` 在技能管道的最后一步调用，
        在问题分类和查询改写完成之后。
    """
    return {
        "question_type": question_type,
        "original_query": user_query,
        "rewritten_query": rewritten_query,
        "user_state": summary,
        "answer_focus": _answer_focus(question_type),
        "output_style": "中文、具体、可执行、温和、避免过度医疗化",
        "do_not_show_chain_of_thought": True,
    }


def _answer_focus(question_type: str) -> str:
    """返回针对给定问题类型应强调哪些健康指标的自然语言描述。

    参数：
        question_type: 由
            :func:`classify_question` 返回的六个类别字符串之一。

    返回：
        以中文命名该类别最相关指标的句子。
        对于无法识别的类别字符串，回退到 ``"general_health"`` 描述。

    触发条件：
        由 :func:`build_openclaw_context` 内部调用。
    """
    mapping = {
        "work_meeting": "重点关注压力、恢复、睡眠、心率、RMSSD、静息心率、疲劳和注意力状态。",
        "exercise": "重点关注活动水平、步数、卡路里、活跃分钟、久坐、恢复和睡眠。",
        "sleep": "重点关注睡眠时长、效率、入睡时长、睡眠结构和压力恢复。",
        "travel": "重点关注疲劳、睡眠、压力、活动负荷与当天状态波动。",
        "stress_recovery": "重点关注压力、恢复、静息心率、RMSSD、睡眠和休息需求。",
        "general_health": "综合关注活动、睡眠、压力与趋势摘要。",
    }
    return mapping.get(question_type, mapping["general_health"])