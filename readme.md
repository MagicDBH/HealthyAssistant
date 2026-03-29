# HealthyAssistant

一个用于 **Sensor-in-the-Loop** 的个性化健康助手 skill。

## 功能
- 解析真实健康数据 `jian.csv`
- 提取活动、睡眠、压力指标
- 计算近 7 天均值、标准差与趋势标签
- 根据用户问题进行查询重写
- 调用 LLM 生成个性化建议

## 支持的典型问题
- 健康状态
- 睡眠与作息
- 运动与健身
- 会议、考试、工作安排
- 出行、通勤、旅行、时差
- 疲劳、恢复、压力与情绪支持

## 目录
- `skill.md`：skill 触发规则与执行逻辑
- `scripts/`：核心代码
- `references/`：参考文献
- `docs/`：数据字段说明

## 运行示例
```bash
pip install -r requirements.txt
python -m scripts.prototype_cli \
  --data scripts/sample_data/jian.csv \
  --user-id 122 \
  --date 2021-07-31 \
  --query "我明天要开会，今天该怎么调整？" \
  --show-summary