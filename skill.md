# Skill: Sensor-in-the-Loop Personalized Health Assistant for OpenClaw
--

--
## 1. Skill 名称与目标

**Skill 名称**：Sensor-in-the-Loop Personalized Health Assistant  
**适用平台**：OpenClaw  
**核心用途**：当用户提出与健康、作息、运动、压力、恢复、出行、会议准备、工作状态、疲劳、旅行、通勤、时差等相关的问题时，读取真实健康数据并构造上下文，让 OpenClaw 的 LLM 生成个性化回复。

该 skill 不直接调用 LLM API，而是负责：
1. 判断是否应触发该 skill；
2. 从真实健康数据中提取用户状态；
3. 计算近 7 天趋势；
4. 根据问题类型确定分析重点；
5. 重写用户问题，使其更适合上下文感知回答；
6. 生成结构化上下文，交由 OpenClaw 接管最终回复。

---

## 2. 触发条件

当用户的问题与以下任何一类场景相关时，应触发该 skill：

### 2.1 健康状态类
- 我今天身体怎么样？
- 我最近状态好吗？
- 我这几天是不是太累了？
- 我现在适合继续工作吗？
- 我最近恢复得怎么样？
- 我今天压力大吗？
- 我最近是不是不太对劲？
- 我这周整体状态怎么样？

### 2.2 睡眠与作息类
- 我昨晚睡得怎么样？
- 我最近是不是熬夜太多？
- 我怎么调整作息？
- 我该几点睡觉比较好？
- 最近睡眠效率怎么样？
- 我今天适合晚睡吗？
- 我睡眠不足，明天怎么办？
- 我最近睡眠质量下降了吗？
- 我该怎么把作息恢复正常？

### 2.3 运动与健身类
- 我今天适合运动吗？
- 我最近该怎么安排运动？
- 我现在适合跑步吗？
- 我能不能去健身？
- 我今天步数够吗？
- 我怎么提高活动量？
- 我想减脂/增肌，最近状态能支持吗？
- 我今天适合做高强度训练吗？
- 我最近运动量是不是不够？
- 我该怎样安排今天的锻炼？

### 2.4 工作、会议、考试、演讲、重要活动类
- 我明天要开会，今天该怎么调整？
- 我适合明天早上的会议吗？
- 我后天有演讲，今晚应该怎么准备？
- 我今天工作效率怎么样？
- 我现在适合加班吗？
- 我明天要赶路/出差，怎么安排更好？
- 我最近能承受高强度工作吗？
- 我适合今晚继续熬夜赶项目吗？
- 我明天有重要安排，今天该怎么恢复？
- 我现在适合处理高压任务吗？

### 2.5 出行、通勤、旅行、时差类
- 我今天适合出门吗？
- 我明天坐飞机/高铁，状态好吗？
- 我最近适合旅行吗？
- 我通勤会不会太累？
- 我需要怎么应对时差？
- 我今天的身体状态适合长途出行吗？
- 我出差前要注意什么？
- 我连续赶路后怎么恢复？
- 我今天适合早起赶车吗？
- 我现在适合开始旅程吗？

### 2.6 恢复、疲劳、压力、情绪支持类
- 我最近是不是压力太大了？
- 我为什么总觉得累？
- 我现在该怎么恢复？
- 我今天需要休息吗？
- 我最近有点焦虑，怎么办？
- 我该如何缓解疲劳？
- 我最近心率/压力指标异常吗？
- 我最近是不是恢复不够？
- 我怎么让自己放松下来？
- 我今天该优先休息还是继续推进工作？

### 2.7 泛生活方式与综合建议类
- 我应该怎么改善生活习惯？
- 我怎样更规律地生活？
- 我最近的健康习惯有什么问题？
- 我适合什么样的作息和运动节奏？
- 我今天应该专注休息还是继续冲刺？
- 我最近该怎么平衡工作和健康？
- 我能不能把作息调好一点？
- 我现在状态适合做哪些事？
- 我该怎么安排今天和接下来两天？
- 我最近需要调整生活方式吗？

---

## 3. 适用范围与不适用范围

### 3.1 适用范围
该 skill 适用于：
- 个人健康状态分析
- 基于真实穿戴设备或行为数据的建议生成
- 结合日常状态进行任务安排判断
- 提供可执行的生活方式优化建议
- 生成"传感器在环"的个性化上下文

### 3.2 不适用范围
以下情况不应使用该 skill 作为主要回答方式：
- 紧急医疗状况
- 严重疾病诊断
- 替代医生的专业治疗建议
- 明确的精神危机或自伤风险
- 需要法律、财务、政策判断的问题
- 与身体状态无关的纯知识问答

如用户问题涉及严重健康风险，应优先建议其寻求专业医疗帮助。

---

## 4. 输入数据要求

该 skill 优先使用真实健康数据文件，例如 `data/jian.csv` 或同类结构化健康数据。

### 4.1 关键字段

#### 活动类
- `calories`
- `distance`
- `steps`
- `lightly_active_minutes`
- `moderately_active_minutes`
- `very_active_minutes`
- `sedentary_minutes`

#### 睡眠类
- `sleep_duration`
- `minutesToFallAsleep`
- `minutesAsleep`
- `minutesAwake`
- `minutesAfterWakeup`
- `sleep_efficiency`
- `sleep_deep_ratio`
- `sleep_wake_ratio`
- `sleep_light_ratio`
- `sleep_rem_ratio`

#### 压力 / 恢复类
- `rmssd`
- `resting_hr`
- `nremhr`
- `stress_score`
- `sleep_points_percentage`
- `responsiveness_points_percentage`

#### 场景类
- `HOME`
- `HOME_OFFICE`
- `WORK/SCHOOL`
- `OUTDOORS`
- `TRANSIT`
- `OTHER`

#### 人群类
- `age`
- `gender`
- `bmi`
- `step_goal`
- `step_goal_label`

### 4.2 数据使用原则
- 优先使用用户当天数据；
- 同时读取过去 7 天数据，生成趋势；
- 如果部分字段缺失，应在输出中注明"数据不足"；
- 不要捏造不存在的数据。

---

## 5. 处理流程

### 5.1 问题分类
先判断用户问题属于哪一类：
- 健康概览
- 睡眠/作息
- 运动/健身
- 工作/会议/考试
- 出行/通勤/旅行
- 压力/恢复/情绪
- 综合建议

### 5.2 状态摘要读取
读取：
- 当天真实数据
- 最近 7 天移动平均值
- 最近 7 天标准差
- 趋势标签（high / medium / low）

### 5.3 指标聚焦
根据问题类型切换重点：

#### A. 开会、工作、演讲、考试、重要活动
重点关注：
- `stress_score`
- `rmssd`
- `resting_hr`
- `sleep_duration`
- `sleep_efficiency`
- `minutesAsleep`
- `minutesAwake`
- `sedentary_minutes`

建议风格：
- 判断是否适合高压任务
- 提醒补觉、减压、安排休息
- 给出时间管理和状态调整建议

#### B. 运动、健身、减脂、活动建议
重点关注：
- `steps`
- `calories`
- `distance`
- `lightly_active_minutes`
- `moderately_active_minutes`
- `very_active_minutes`
- `sedentary_minutes`
- `sleep_duration`
- `rmssd`
- `resting_hr`

建议风格：
- 判断是否适合运动
- 推荐运动强度与时长
- 给出恢复与拉伸建议
- 避免过度训练

#### C. 作息、睡眠、恢复、熬夜后建议
重点关注：
- `sleep_duration`
- `sleep_efficiency`
- `minutesToFallAsleep`
- `minutesAsleep`
- `minutesAwake`
- `minutesAfterWakeup`
- `sleep_deep_ratio`
- `sleep_rem_ratio`
- `stress_score`
- `rmssd`
- `resting_hr`

建议风格：
- 判断睡眠质量和恢复是否不足
- 给出睡前习惯、补觉、午休、节奏调整建议
- 提醒避免持续熬夜

#### D. 出行、通勤、旅行、时差
重点关注：
- `sleep_duration`
- `sleep_efficiency`
- `stress_score`
- `rmssd`
- `resting_hr`
- `sedentary_minutes`
- `steps`
- `OUTDOORS`
- `TRANSIT`
- `WORK/SCHOOL`

建议风格：
- 判断是否适合长途出行
- 提醒时差适应
- 评估疲劳状态
- 建议补水、补觉、分段活动

#### E. 泛健康状态问题
重点关注：
- 活动、睡眠、压力三大类全量指标
- 最近 7 天趋势
- 当天是否异常偏低或偏高

建议风格：
- 综合判断当前状态
- 指出主要风险因子
- 给出优先级排序建议

---

## 6. 查询重写规则

在把内容交给 OpenClaw 的 LLM 前，需要先进行查询重写：

1. 分析用户状态摘要；
2. 判断用户真实目标；
3. 将原始问题改写为更贴近当前身体状态的版本。

### 6.1 重写目标示例
- 减压
- 提升生产力
- 情感支持
- 睡眠优化
- 运动建议
- 恢复建议
- 出行准备
- 活动安排调整

### 6.2 重写要求
- 不暴露内部分析过程；
- 只输出重写后的问题；
- 保留用户原意，但结合真实数据背景增强上下文；
- 如果用户问题很模糊，应改写为更具体的健康决策问题。

---

## 7. 输出结构

当该 skill 被触发后，应输出一个结构化上下文，供 OpenClaw 继续生成最终回答。建议包含以下部分：

### 7.1 基础信息
- 用户 ID
- 日期
- 原始问题
- 重写后的问题
- 问题类别

### 7.2 当日摘要
- 活动摘要
- 睡眠摘要
- 压力摘要
- 场景摘要
- 用户画像

### 7.3 7 天趋势
- 每个关键指标的 7 天均值
- 标准差
- 趋势标签

### 7.4 回答偏好提示
- 建议应更关注哪一类指标
- 建议的语气与风格
- 是否需要提醒休息、减压、运动、补觉或出行调整

---

## 8. 输出风格与安全边界

### 8.1 输出风格
回答应：
- 中文输出；
- 具体、可执行、温和；
- 语气自然，不机械；
- 尽量给出优先级明确的建议；
- 结合真实数据说明理由；
- 必要时给出"如果你今晚/明天/接下来 24 小时想这样做，可以怎么安排"。

### 8.2 安全边界
- 不做医疗诊断；
- 不夸大数据结论；
- 不制造不存在的危险；
- 对于明显异常或紧急问题，建议就医；
- 不暴露链式思维全过程，只保留高层处理逻辑。

---

## 9. 示例触发问题

以下问题都应触发该 skill：

- 我今天身体怎么样？
- 我最近压力是不是太大了？
- 我明天要开会，怎么调整状态？
- 我今晚睡少了，明天怎么补救？
- 我适合去运动吗？
- 我最近步数太少，怎么改善？
- 我连续几天睡不好怎么办？
- 我明天要出差，身体状态行不行？
- 我现在适合去跑步吗？
- 我最近适合加班吗？
- 我最近是不是恢复不够？
- 我现在适合高强度训练吗？
- 我这周生活规律吗？
- 我今天该休息还是继续工作？
- 我接下来两天有很多事，怎么安排更合理？

---

## 10. 执行原则

当该 skill 被触发时：
1. 先识别问题类型；
2. 再读取当天数据与 7 天趋势；
3. 再确定分析重点；
4. 再重写用户问题；
5. 再把结构化上下文交给 OpenClaw；
6. 最终由 OpenClaw 生成个性化、可执行的回答。

---

## 11. 函数调用规范

本节明确说明 `scripts/` 目录中每个函数的**调用时机**、**参数**和**返回值**，供 OpenClaw / Claude Code 自动注册和调用。

### 调用顺序（数据流程）

```
用户问题
    │
    ▼
[Step 1] JianDataParser.build_daily_summary(user_id, date)
    │     → 返回当日健康快照（活动 / 睡眠 / 压力 / 场景）
    │
    ▼
[Step 2] JianDataParser.build_7day_summary(user_id, date)
    │     → 返回近 7 天各指标均值、标准差、趋势标签
    │
    ├─── 合并为 summary = {user_id, date, daily, metrics}
    │
    ▼
[Step 3] classify_question(user_query)
    │     → 返回问题类别字符串
    │       可选值：work_meeting / exercise / sleep /
    │               travel / stress_recovery / general_health
    │
    ▼
[Step 4] rewrite_query_locally(summary, user_query, question_type)
    │     → 返回上下文增强后的问题（中文字符串）
    │
    ▼
[Step 5] build_payload(summary, original_query, rewritten_query, question_type)
          → 返回结构化 JSON 上下文，交由 OpenClaw LLM 生成最终回复
```

### 函数详细说明

#### `JianDataParser.build_daily_summary`
- **模块**：`scripts.data_parser`
- **何时调用**：skill 被触发后**第一步**，在问题分类之前。
- **参数**：
  - `user_id` (str)：CSV `id` 列的用户标识。
  - `date` (str)：目标日期，ISO-8601 格式，如 `"2021-07-31"`。
- **返回值**：包含 `profile` / `activity` / `sleep` / `stress` / `context` 的嵌套字典。
- **异常**：
  - `FileNotFoundError`：CSV 文件不存在。
  - `ValueError`：指定用户/日期无数据。

#### `JianDataParser.build_7day_summary`
- **模块**：`scripts.data_parser`
- **何时调用**：紧跟 `build_daily_summary` 之后，**第二步**。
- **参数**：同上（`user_id`, `date`）。
- **返回值**：包含 `window_days` 和 `metrics` 的字典；每个指标含 `latest` / `7d_mean` / `7d_std` / `trend_label`。

#### `classify_question`
- **模块**：`scripts.prompt_builder`
- **何时调用**：两个数据摘要合并后，**第三步**。
- **参数**：
  - `user_query` (str)：用户原始问题。
- **返回值**：六类之一的字符串：`work_meeting` / `exercise` / `sleep` / `travel` / `stress_recovery` / `general_health`。

#### `rewrite_query_locally`
- **模块**：`scripts.query_rewriter`
- **何时调用**：`classify_question` 返回后，**第四步**。不需要外部 LLM。
- **参数**：
  - `summary` (dict)：合并摘要。
  - `user_query` (str)：原始问题。
  - `question_type` (str)：`classify_question` 的返回值。
- **返回值**：上下文增强后的中文问题字符串。

#### `build_payload`
- **模块**：`scripts.openclaw_payload`
- **何时调用**：管道**最后一步**，整合所有数据后调用。
- **参数**：
  - `summary` (dict)：合并摘要。
  - `original_query` (str)：用户原始问题。
  - `rewritten_query` (str)：重写后的问题。
  - `question_type` (str)：问题类别。
- **返回值**：完整的 OpenClaw 上下文 JSON，含 `question_type` / `original_query` / `rewritten_query` / `user_state` / `answer_focus` / `output_style` / `do_not_show_chain_of_thought`。

---

## 12. 期望效果

这个 skill 的目标不是只回答"健康不健康"，而是把用户的真实身体状态嵌入到日常决策中，例如：
- 明天要不要开会前加班
- 今晚要不要运动
- 今天是休息还是推进任务
- 是否适合旅行或赶路
- 是否应该调整作息
- 是否应该减少压力负荷

通过这种方式，系统能更像一个真正"懂当前状态"的个性化健康助手。