# Subagent Scheduler Skill

自适应子代理调度系统 - 技能增强版

## 功能特性

- 智能任务分类（Simple/Standard/Batch/Deep）
- SQLite历史数据存储
- 飞书卡片交互确认
- 实时进度推送
- 失败重试机制（最多5次）
- 成本预估与控制

## 文件结构

```
subagent-scheduler/
├── SKILL.md              # 本文件
├── schema.sql            # 数据库表结构
├── scheduler.js          # 核心调度逻辑
├── feishu.js             # 飞书交互模块
├── database.js           # SQLite操作封装
└── config.json           # 配置文件
```

## 使用方法

```javascript
const scheduler = require('./scheduler');

// 执行任务
const result = await scheduler.execute({
  task: "分析这10个日志文件",
  userId: "user_123"
});
```

## 配置说明

见 config.json
