# 子代理方案决策树

## 分支一：极简模式（Simple）

**触发条件：**
- 任务可预估耗时 < 10秒
- 仅需 1-2 个工具调用
- 无外部依赖
- 输出长度 < 500 字

**策略：**
- 不 spawn，主代理直接处理
- 串行执行工具

**配置：**
```json
{
  "strategy": "simple",
  "spawn": false
}
```

**优点：** 零开销、低延迟
**缺点：** 阻塞主线程

---

## 分支二：标准模式（Standard）

**触发条件：**
- 任务耗时 10-60秒
- 需 3+ 工具调用或 I/O 等待
- 可独立执行
- 输出长度 500-2000 字

**策略：**
- spawn，run 模式
- cleanup: "delete"
- timeout: 60-120s
- 模型：继承或降级到便宜模型

**配置：**
```json
{
  "strategy": "standard",
  "spawn": true,
  "mode": "run",
  "cleanup": "delete",
  "runTimeoutSeconds": 90,
  "model": "openai/gpt-4.1-mini",
  "thinking": "low"
}
```

**优点：** 隔离性好、成本可控
**缺点：** spawn 有固定开销 (~1-2s)

---

## 分支三：批量模式（Batch）

**触发条件：**
- 同类任务数量 3-20 个
- 任务间无依赖
- 每个子任务可独立执行
- 需要汇总结果

**策略：**
- 单个子代理内顺序/并行处理
- 或 spawn 编排器 → 批量 spawn 叶子
- maxChildrenPerAgent: 5

**配置：**
```json
{
  "strategy": "batch",
  "spawn": true,
  "mode": "run",
  "batchSize": 5,
  "orchestrator": {
    "model": "kimi-coding/k2p5",
    "maxChildren": 5
  },
  "worker": {
    "model": "openai/gpt-4.1-mini",
    "timeout": 60
  }
}
```

**优点：** 减少 spawn 次数、并行效率高
**缺点：** 单点失败影响整批、需要结果汇总逻辑

---

## 分支四：编排模式（Orchestrator）

**触发条件：**
- 任务有明确依赖关系
- 需要多阶段处理（获取→分析→汇总）
- 涉及不同类型子任务
- 需要动态决策

**策略：**
- maxSpawnDepth: 2
- 编排器子代理管理 workers
- DAG 拓扑排序执行
- 级联终止

**配置：**
```json
{
  "strategy": "orchestrator",
  "spawn": true,
  "maxSpawnDepth": 2,
  "mode": "run",
  "orchestrator": {
    "tools": ["sessions_spawn", "subagents", "sessions_list"],
    "model": "anthropic/claude-sonnet-4-5"
  },
  "worker": {
    "model": "openai/gpt-4.1-mini",
    "cleanup": "delete"
  }
}
```

**优点：** 复杂任务拆解清晰、可动态调整
**缺点：** 层级增加延迟、调试困难

---

## 分支五：深度模式（Deep）

**触发条件：**
- 需要长时间运行（>5分钟）
- 需要多轮交互/迭代
- 需要保持上下文状态
- 输出长度 > 5000 字

**策略：**
- mode: "session"
- thread: true（Discord）
- cleanup: "keep"
- 定期发送进度更新

**配置：**
```json
{
  "strategy": "deep",
  "spawn": true,
  "mode": "session",
  "thread": true,
  "cleanup": "keep",
  "model": "anthropic/claude-opus-4-5",
  "thinking": "medium",
  "progressInterval": 30
}
```

**优点：** 支持复杂长任务、可交互
**缺点：** 资源占用高、需手动管理生命周期

---

## 自动选择逻辑

```
function selectStrategy(task):
  # 1. 极简检查
  if task.estimatedTime < 10s && task.toolCount <= 2:
    return SIMPLE

  # 2. 深度检查
  if task.estimatedTime > 300s || task.requiresIteration:
    return DEEP

  # 3. 批量检查
  if task.subTasks?.length >= 3 && task.subTasks.areIndependent:
    return BATCH

  # 4. 编排检查
  if task.hasDependencies || task.requiresCoordination:
    return ORCHESTRATOR

  # 5. 默认标准
  return STANDARD
```

---

## 关键词触发映射

| 关键词 | 倾向分支 |
|--------|----------|
| "快速查询"、"查一下" | Simple |
| "分析文件"、"生成报告" | Standard |
| "批量处理"、"所有文件" | Batch |
| "先获取再分析"、"分步骤" | Orchestrator |
| "深度研究"、"详细分析" | Deep |
