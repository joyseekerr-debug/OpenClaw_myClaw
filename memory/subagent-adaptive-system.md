# 子代理自适应调度系统 - 最终方案

## 一、核心架构

### 1.1 五大策略分支

| 分支 | 触发条件 | 核心配置 | 适用场景 |
|------|----------|----------|----------|
| **Simple** | <10s, <2工具, 无依赖 | `spawn: false` | 快速查询、简单计算 |
| **Standard** | 10-120s, 独立任务 | `mode: run, cleanup: delete, timeout: 90s` | 常规分析、文件处理 |
| **Batch** | 3-20个同类子任务 | `orchestrator + workers, batchSize: 5` | 批量处理、数据转换 |
| **Orchestrator** | 有依赖关系、多阶段 | `maxSpawnDepth: 2, DAG执行` | 复杂流程、流水线 |
| **Deep** | >2分钟或需多轮 | `mode: session, thread: true, cleanup: keep` | 深度研究、长任务 |

### 1.2 三层决策器 + 用户确认层

```
输入：任务描述 + 附件 + 用户偏好
    ↓
┌─────────────────────────────────────────┐
│ 第一层：快速规则（0成本）                │
│   - 字数<50 + 无附件 → Simple           │
│   - 含"批量/所有" → Batch候选           │
│   - 含"详细/深度" → Deep候选            │
│   - 置信度>0.6 → 直接返回               │
└─────────────────────────────────────────┘
    ↓ 置信度不足
┌─────────────────────────────────────────┐
│ 第二层：试探执行（动态调整）             │
│   启动后监控前15秒                       │
│   - 进度正常 → 维持策略                  │
│   - 卡住/超时风险 → 自动升级策略         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 第三层：用户确认（非Simple分支）         │
│   展示选择的分支及预估信息：             │
│   - 策略：Standard/Batch/Deep等          │
│   - 预估耗时：XX秒                       │
│   - 预估成本：$X.XX（可选）              │
│   [确认执行] [换Simple] [取消]           │
└─────────────────────────────────────────┘
```

## 二、10轮优化整合

### 2.1 智能识别（第1轮）

**问题：** 规则判断误判率高
**方案：** 三层决策器 + 历史校准

```javascript
function classifyTask(task) {
  // 快速规则
  const fastResult = fastRules(task);
  if (fastResult.confidence > 0.6) return fastResult;
  
  // 试探执行标记（由执行层处理）
  return {branch: fastResult.branch, probe: true};
}
```

### 2.2 加权并发（第2轮）

**问题：** 固定并发资源利用率低
**方案：** 动态权重分配

```json
{
  "concurrency": {
    "totalCapacity": 100,
    "weights": {
      "Simple": 0.3,
      "Standard": 1.0,
      "Batch": 1.5,
      "Orchestrator": 2.0,
      "Deep": 3.0
    },
    "lanes": {
      "fast": {"maxPercent": 50, "maxWeight": 0.5},
      "standard": {"maxPercent": 40, "maxWeight": 2.0},
      "heavy": {"maxPercent": 10, "minGuaranteed": 1}
    }
  }
}
```

### 2.3 分级失败恢复（第3轮）

**问题：** 失败处理一刀切
**方案：** 错误分类 + 检查点

```python
def handleError(error, context):
    if error.type == "TRANSIENT":  # 网络/超时
        return retryWithBackoff(context, maxRetries=5)
    
    elif error.type == "RESOURCE":  # 内存/CPU
        return downgradeStrategy(context)  # Deep→Standard→Simple
    
    elif error.type == "LOGIC":  # 代码异常
        return abortAndAlert(context, preservePartial=True)
    
    elif error.type == "TIMEOUT":
        return checkpointRecovery(context)  # 从检查点恢复
```

### 2.4 三层成本防护（第4轮）

**问题：** 成本不可控
**方案：** 预估 + 监控 + 审计

```json
{
  "costControl": {
    "budgets": {
      "perTask": {"max": 0.5, "action": "downgrade"},
      "perSession": {"max": 5.0, "action": "warn"},
      "perDay": {"max": 20.0, "action": "block"}
    },
    "estimation": {
      "enabled": true,
      "threshold": 0.1,  // >$0.1需要确认
      "model": "historical_average"
    },
    "monitoring": {
      "alertAtPercent": 80,
      "interval": 10
    }
  }
}
```

### 2.5 渐进式交付（第5轮）

**问题：** 用户感知延迟高
**方案：** 非阻塞启动 + 流式进度

```javascript
// 立即响应
const run = await sessions_spawn({
  task: "分析代码库",
  onProgress: (percent) => {
    sessions_send(parent, `进度: ${percent}%`);
  }
});

return {status: "started", runId: run.id, eta: "60s"};
```

### 2.6 分层上下文（第6轮）

**问题：** 上下文膨胀超限
**方案：** 三层架构 + 智能压缩

```
全局层（只读共享）：AGENTS.md, 项目背景
任务层（当前相关）：输入、中间结果摘要
临时层（动态）：工具输出、思考过程（用完即删）

压缩触发：上下文达80%
- 保留：关键结论、决策依据
- 丢弃：详细过程、已执行工具输出
- 存档：完整历史写入文件，仅保留路径
```

### 2.7 策略权限（第7轮）

**问题：** 过度授权风险
**方案：** 分支绑定策略

```json
{
  "security": {
    "policies": {
      "Simple": {"allow": ["read"], "deny": ["write", "exec"]},
      "Standard": {"allow": ["read", "write"], "deny": ["exec", "cron"]},
      "Batch": {"allow": ["read", "write", "exec"], "rateLimit": 10},
      "Deep": {"dynamic": true}  // 按需申请
    },
    "sensitiveData": {
      "autoMask": true,
      "placeholder": "[REDACTED]"
    }
  }
}
```

### 2.8 分布式追踪（第8轮）

**问题：** 黑盒执行难排查
**方案：** Trace ID + 火焰图

```json
{
  "observability": {
    "tracing": {
      "enabled": true,
      "sampleRate": 1.0,
      "includeTools": true
    },
    "metrics": {
      "realtime": ["activeAgents", "queueWait", "successRate"],
      "trends": ["avgDuration", "costTrend", "branchUsage"]
    },
    "autoDiagnose": {
      "enabled": true,
      "anomalies": ["failureSpike", "latencyOutlier"]
    }
  }
}
```

### 2.9 智能交互（第9轮）

**问题：** 用户不清楚进展
**方案：** 分级通知 + 交互控制

```javascript
const notificationRules = {
  critical: ["start", "complete", "fail"],  // 必通知
  progress: {interval: 120, minDuration: 300},  // 长任务才通知
  detail: {mode: "debug"}  // 仅调试模式
};

// 执行中可交互
const controls = {
  "加速": () => increaseConcurrency(),
  "详细点": () => upgradeToDeep(),
  "够了": () => earlyTermination(),
  "暂停": () => checkpointAndPause()
};
```

### 2.10 自适应学习（第10轮）

**问题：** 无法持续优化
**方案：** 反馈闭环 + 插件化

```
反馈数据收集：
- 决策输入（任务特征、系统状态）
- 决策输出（选择的分支、配置）
- 执行结果（耗时、成本、成功率）
- 用户反馈（满意度评分）

定期优化：
- 每周：分析分支选择准确率
- 每月：调整超时阈值、成本预估模型
- 每季：评估新增分支类型需求

插件接口：
- 新模型接入：配置化
- 新分支类型：实现Strategy接口
- 自定义规则：用户级覆盖
```

### 2.11 用户确认提醒（新增功能）

**问题：** 用户不清楚系统选择了什么策略，可能产生意外成本或等待时间
**方案：** 非Simple分支执行前主动提醒

**提醒时机：**
- 决策器选择 Standard/Batch/Orchestrator/Deep 后
- 执行前（pre-execution）

**提醒内容：**
```
🤖 任务分析完成

选择策略：{Branch}
预估耗时：{X} 秒
预估成本：${X.XX}（可选）
资源占用：{并发权重}

[✓ 确认执行]  [⇄ 换用简单模式]  [✕ 取消]
```

**用户选项：**
- **确认执行**：按选定策略继续
- **换用简单模式**：降级为 Simple（主代理直接处理，无spawn开销）
- **取消**：终止任务

**配置：**
```json5
{
  "userConfirmation": {
    "enabled": true,
    "excludeSimple": true,      // Simple分支不提醒
    "showEstimation": true,     // 显示预估耗时/成本
    "timeout": 30,              // 30秒无响应自动确认
    "allowDowngrade": true      // 允许降级到Simple
  }
}
```

**例外情况（免确认）：**
- 用户明确指定了策略（如 `--strategy deep`）
- 历史任务（相同任务已确认过）
- 紧急模式（`--urgent` 标志）

## 三、实施路线图

### Phase 1: MVP（立即，1-2周）
- [ ] 五大分支策略实现
- [ ] 基础决策树（规则层）
- [ ] 用户确认提醒功能
- [ ] 成本预算硬限制
- [ ] 基础超时机制

**收益：** 80%场景有合适策略，用户知情同意，成本可控

### Phase 2: 增强（短期，1个月）
- [ ] LLM分类层（轻量模型）
- [ ] 加权并发系统
- [ ] 分级失败恢复
- [ ] 流式进度通知

**收益：** 准确率提升至90%，用户体验改善

### Phase 3: 智能化（中期，2-3个月）
- [ ] 试探执行 + 动态调整
- [ ] 分层上下文压缩
- [ ] 策略权限系统
- [ ] 分布式追踪

**收益：** 资源利用率提升50%，问题可定位

### Phase 4: 自适应（长期，持续）
- [ ] 历史数据学习
- [ ] 自动优化建议
- [ ] 插件化架构
- [ ] 预测性调度

**收益：** 系统越用越智能，维护成本降低

## 四、配置示例

### 4.1 完整配置模板

```json5
{
  "adaptiveSubagent": {
    "branches": {
      "Simple": {"spawn": false},
      "Standard": {
        "mode": "run",
        "cleanup": "delete",
        "timeout": 90,
        "model": "kimi-coding/k2p5",
        "reasoning": true
      },
      "Batch": {
        "batchSize": 5,
        "orchestrator": {"model": "kimi-coding/k2p5", "reasoning": true},
        "worker": {"model": "kimi-coding/k2p5", "reasoning": true, "timeout": 60}
      },
      "Orchestrator": {
        "maxSpawnDepth": 2,
        "model": "kimi-coding/k2p5",
        "reasoning": true
      },
      "Deep": {
        "mode": "session",
        "thread": true,
        "cleanup": "keep",
        "model": "kimi-coding/k2p5",
        "reasoning": true
      }
    },
    
    "decision": {
      "layers": [
        {"type": "rules", "confidence": 0.6},
        {"type": "probe", "duration": 15}
      ]
    },
    
    "concurrency": {
      "totalCapacity": 100,
      "weights": {"Simple": 0.3, "Standard": 1, "Batch": 1.5, "Orchestrator": 2, "Deep": 3},
      "lanes": {
        "fast": {"maxPercent": 50},
        "standard": {"maxPercent": 40},
        "heavy": {"maxPercent": 10, "minGuaranteed": 1}
      }
    },
    
    "costControl": {
      "budgets": {
        "perTask": {"max": 0.5, "action": "downgrade"},
        "perDay": {"max": 20, "action": "block"}
      },
      "estimation": {"enabled": true, "threshold": 0.1}
    },
    
    "resilience": {
      "retry": {"transient": {"max": 5, "backoff": "exponential"}},
      "downgrade": {"resource": true, "timeout": true},
      "checkpoint": {"enabled": true, "interval": 600}
    },
    
    "security": {
      "policies": {
        "Simple": {"allow": ["read"]},
        "Standard": {"allow": ["read", "write"]},
        "Deep": {"dynamic": true}
      }
    },
    
    "observability": {
      "tracing": {"enabled": true},
      "metrics": {"realtime": true, "trends": true},
      "autoDiagnose": true
    }
  }
}
```

### 4.2 使用示例

```javascript
// 系统自动选择
const result = await adaptiveSubagent.execute({
  task: "分析这10个日志文件，找出错误模式"
});
// → 自动选择 Batch 策略

// 用户指定预算
const result = await adaptiveSubagent.execute({
  task: "深度分析代码库",
  budget: {max: 1.0, currency: "USD"}
});
// → 可能降级为 Standard 以控制成本

// 截止时间驱动
const result = await adaptiveSubagent.execute({
  task: "生成报告",
  deadline: "2025-02-24T18:00:00Z"
});
// → 选择能满足截止时间的最快策略
```

## 五、关键指标

| 指标 | 当前 | 目标 | 测量方式 |
|------|------|------|----------|
| 策略选择准确率 | - | >90% | 人工标注样本验证 |
| 平均任务耗时 | - | -30% | 对比基线数据 |
| 成本超预算率 | - | <5% | 预算告警次数/总任务数 |
| 失败恢复成功率 | - | >95% | 恢复成功次数/失败次数 |
| 用户满意度 | - | >4.5/5 | 反馈评分 |
| 资源利用率 | - | >70% | CPU/内存平均使用率 |

---

**版本：** v1.0  
**创建时间：** 2025-02-24  
**文档路径：** `memory/subagent-adaptive-system.md`
