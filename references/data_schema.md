# Data Schema

本项目使用 `data/jian.csv` 作为真实健康数据样例。

## 核心字段说明

### 活动类
- `calories`: 当日消耗热量
- `distance`: 当日活动距离
- `steps`: 当日步数
- `lightly_active_minutes`: 轻度活动分钟数
- `moderately_active_minutes`: 中度活动分钟数
- `very_active_minutes`: 高强度活动分钟数
- `sedentary_minutes`: 久坐分钟数

### 睡眠类
- `sleep_duration`: 睡眠时长
- `minutesToFallAsleep`: 入睡所需时间
- `minutesAsleep`: 实际睡着时间
- `minutesAwake`: 夜间清醒时间
- `minutesAfterWakeup`: 起床后清醒时间
- `sleep_efficiency`: 睡眠效率

### 压力 / 恢复类
- `rmssd`: 心率变异性
- `resting_hr`: 静息心率
- `nremhr`: 非快速眼动睡眠心率
- `stress_score`: 压力评分
- `sleep_points_percentage`: 睡眠得分百分比
- `responsiveness_points_percentage`: 恢复/响应得分百分比

### 场景类
- `HOME`
- `HOME_OFFICE`
- `WORK/SCHOOL`
- `OUTDOORS`
- `TRANSIT`
- `OTHER`

### 人群类
- `age`
- `gender`
- `bmi`
- `step_goal`
- `step_goal_label`