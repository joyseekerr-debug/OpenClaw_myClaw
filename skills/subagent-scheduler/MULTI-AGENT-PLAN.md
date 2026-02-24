# 多 Agents 协作系统拓展方案

## 目标
将现有的"单 Agent 多策略调度"扩展为"多 Agents 协作系统"，支持复杂任务的分解、分配、协作执行。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户任务输入                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   任务分解器 (Orchestrator)                   │
│  - 分析任务复杂度                                             │
│  - 拆解为可并行/串行的子任务                                   │
│  - 生成执行 DAG                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Agent 路由中心                              │
│  - 查询可用 Agent 列表                                        │
│  - 根据能力匹配分配子任务                                      │
│  - 负载均衡决策                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────┬───────────┬───────────┐
        ↓           ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Agent 1  │ │ Agent 2  │ │ Agent 3  │ │ Agent N  │
│ (Simple) │ │(Standard)│ │ (Deep)   │ │(Special) │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
        ↓           ↓           ↓           ↓
        └───────────┴───────────┴───────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   结果聚合器 (Aggregator)                     │
│  - 收集子任务结果                                             │
│  - 冲突检测与解决                                             │
│  - 生成最终输出                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   协作状态管理                                │
│  - 共享上下文                                                │
│  - 进度同步                                                  │
│  - 故障恢复                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 1. Agent Registry (Agent 注册中心)

**功能：**
- Agent 注册/注销
- 能力描述与发现
- 健康检查

**数据结构：**
```javascript
{
  agentId: "agent_001",
  name: "CodeAnalyzer",
  capabilities: ["read", "write", "exec", "analyze_code"],
  maxConcurrent: 3,
  currentLoad: 1,
  status: "healthy", // healthy, busy, offline
  lastHeartbeat: timestamp,
  metadata: {
    model: "kimi-coding/k2p5",
    maxTokens: 8000,
    specialties: ["javascript", "python"]
  }
}
```

**接口：**
- `register(agentInfo)` - 注册新 agent
- `unregister(agentId)` - 注销 agent
- `discover(requirements)` - 发现匹配的 agents
- `heartbeat(agentId)` - 心跳更新
- `getHealthyAgents()` - 获取健康 agents

---

### 2. Task Decomposer (任务分解器)

**功能：**
- 分析任务复杂度
- 拆分为子任务
- 生成执行依赖图 (DAG)

**分解策略：**
```javascript
// 示例：复杂分析任务
task: "分析整个代码库并生成架构报告"
↓
subtasks: [
  { id: 1, task: "扫描项目结构", dependsOn: [], agent: "Scanner" },
  { id: 2, task: "分析依赖关系", dependsOn: [1], agent: "Analyzer" },
  { id: 3, task: "识别关键模块", dependsOn: [1], agent: "Analyzer" },
  { id: 4, task: "评估代码质量", dependsOn: [2, 3], agent: "Reviewer" },
  { id: 5, task: "生成架构图", dependsOn: [2, 3], agent: "Visualizer" },
  { id: 6, task: "汇总报告", dependsOn: [4, 5], agent: "Reporter" }
]
```

**接口：**
- `decompose(task, options)` - 分解任务
- `analyzeDependencies(subtasks)` - 分析依赖
- `estimateComplexity(subtask)` - 估算复杂度

---

### 3. Agent Router (Agent 路由中心)

**功能：**
- 子任务分配
- 负载均衡
- 失败重路由

**路由策略：**
1. **能力匹配** - 选择具备所需能力的 agent
2. **负载均衡** - 优先分配给负载低的 agent
3. **就近原则** - 优先选择本地 agent
4. **成本优化** - 考虑执行成本

**接口：**
- `route(subtask, availableAgents)` - 路由子任务
- `reRoute(failedSubtask)` - 失败重路由
- `getRoutingStats()` - 获取路由统计

---

### 4. Collaboration Hub (协作中心)

**功能：**
- Agent 间通信
- 共享状态管理
- 进度同步

**通信模式：**
```javascript
// 1. 点对点通信
agentA.sendTo(agentB, { type: "request", data: {} })

// 2. 广播
hub.broadcast({ type: "progress", progress: 50 })

// 3. 发布-订阅
hub.subscribe("topic", callback)
hub.publish("topic", message)
```

**状态共享：**
```javascript
// 全局共享状态
hub.setGlobal("projectConfig", config)

// 任务级共享
hub.setTask(taskId, "intermediateResult", result)

// 临时状态
hub.setTemp(agentId, "scratchpad", notes)
```

---

### 5. Result Aggregator (结果聚合器)

**功能：**
- 收集子任务结果
- 冲突检测
- 结果合并

**聚合策略：**
1. **顺序合并** - 按执行顺序拼接
2. **智能合并** - 基于内容去重/整合
3. **投票机制** - 多 agent 结果投票
4. **优先级** - 高优先级 agent 结果优先

**接口：**
- `collect(subtaskId, result)` - 收集结果
- `aggregate(results, strategy)` - 聚合结果
- `resolveConflicts(conflicts)` - 解决冲突

---

### 6. Execution Monitor (执行监控)

**功能：**
- 跟踪多 agent 执行状态
- 性能监控
- 故障检测与恢复

**监控指标：**
- 每个 agent 的任务队列长度
- 执行耗时
- 成功率
- 资源使用率

**故障处理：**
- Agent 失联 → 重新路由任务
- 任务超时 → 重试或降级
- 结果冲突 → 人工介入或自动仲裁

---

## 实施阶段

### Phase 1: Agent Registry + 本地多实例 (1-2天)
- 实现 Agent 注册/发现
- 支持本地启动多个 agent 实例
- 基础路由功能

### Phase 2: Task Decomposer (2-3天)
- 任务分解逻辑
- DAG 执行引擎
- 依赖管理

### Phase 3: Collaboration Hub (2-3天)
- Agent 间通信
- 状态共享
- 进度同步

### Phase 4: Result Aggregator (1-2天)
- 结果收集
- 冲突解决
- 智能合并

### Phase 5: 监控与优化 (2-3天)
- 执行监控
- 性能优化
- 故障恢复

**预计总工期：8-13天**

---

## 与现有技能整合

```javascript
// 扩展现有调度器
class MultiAgentScheduler extends SubagentScheduler {
  constructor(options) {
    super(options);
    
    // 新增组件
    this.registry = new AgentRegistry();
    this.decomposer = new TaskDecomposer();
    this.router = new AgentRouter();
    this.hub = new CollaborationHub();
    this.aggregator = new ResultAggregator();
    this.monitor = new ExecutionMonitor();
  }
  
  async executeComplex(task, options) {
    // 1. 判断是否需要多 agent
    if (await this.shouldUseMultiAgent(task)) {
      return await this.executeMultiAgent(task, options);
    }
    
    // 2. 否则使用单 agent 调度
    return await super.execute(task, options);
  }
  
  async executeMultiAgent(task, options) {
    // 1. 分解任务
    const dag = await this.decomposer.decompose(task);
    
    // 2. 获取可用 agents
    const agents = await this.registry.getHealthyAgents();
    
    // 3. 执行 DAG
    const results = await this.executeDAG(dag, agents);
    
    // 4. 聚合结果
    return await this.aggregator.aggregate(results);
  }
}
```

---

## 关键设计决策

### 1. 中心化 vs 去中心化
**选择：中心化路由 + 分布式执行**
- 路由中心负责任务分配
- 各 agent 独立执行
- 平衡可控性和灵活性

### 2. 同步 vs 异步协作
**选择：异步为主，同步为辅**
- 子任务并行执行（异步）
- 依赖任务等待（同步）
- 通过 Promise/async 管理

### 3. 强一致性 vs 最终一致性
**选择：最终一致性**
- 共享状态允许短暂不一致
- 结果聚合时统一处理
- 更适合分布式场景

---

## 预期收益

1. **能力扩展** - 复杂任务可分解为子任务并行处理
2. **效率提升** - 多 agents 并行执行，缩短总耗时
3. **容错增强** - 单 agent 失败可重路由，不影响整体
4. **专业化** - 不同 agent 可专精不同领域

---

**是否确认实施？或需要调整方案？**
