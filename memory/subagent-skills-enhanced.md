# 子代理自适应调度系统 - 技能增强版（飞书+SQLite+可视化）

## 一、架构升级（基于可学习技能）

### 1.1 渠道层：飞书（Feishu）
**能力：**
- 卡片消息：带按钮的确认界面
- 消息更新：实时进度推送
- 线程绑定：Deep模式会话保持
- 群聊/@提及：多用户协作场景

### 1.2 数据层：SQLite
**能力：**
- 任务历史记录（输入、策略、耗时、成本）
- 成本预估模型训练数据
- 并发计数（轻量级全局状态）
- 检查点状态存储

### 1.3 调度层：Cron
**能力：**
- 定时轮询子代理状态
- 超时检测和告警
- 进度汇报触发

### 1.4 可视化层：Plotly/Canvas
**能力：**
- 生成成本趋势图
- 任务成功率统计图
- 资源利用率仪表盘

---

## 二、核心功能实现

### 2.1 智能决策（规则+历史数据）

```javascript
// 使用 SQLite 历史数据优化决策
function classifyTaskWithHistory(task) {
  // 1. 快速规则
  const fastResult = fastRules(task);
  if (fastResult.confidence > 0.6) return fastResult;
  
  // 2. 历史相似任务查询（SQLite）
  const similar = db.query(`
    SELECT branch, AVG(duration) as avg_duration, AVG(cost) as avg_cost
    FROM task_history
    WHERE input_hash LIKE ?
    ORDER BY created_at DESC
    LIMIT 10
  `, [task.hashPrefix]);
  
  // 3. 基于历史校准
  if (similar.length > 3) {
    return calibrateWithHistory(fastResult, similar);
  }
  
  return fastResult;
}
```

**数据表设计：**
```sql
CREATE TABLE task_history (
  id INTEGER PRIMARY KEY,
  input_hash TEXT,
  input_preview TEXT,
  branch TEXT,
  duration INTEGER,
  cost REAL,
  success BOOLEAN,
  created_at TIMESTAMP
);
```

---

### 2.2 飞书卡片确认界面

**用户输入任务 → 我分析 → 发送卡片：**

```json
{
  "msg_type": "interactive",
  "card": {
    "config": {"wide_screen_mode": true},
    "header": {
      "title": {"tag": "plain_text", "content": "🤖 任务分析完成"},
      "template": "blue"
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**选择策略：** Standard\n**预估耗时：** 45-60秒\n**预估成本：** ¥0.05\n**历史成功率：** 92%（基于12次相似任务）"
        }
      },
      {
        "tag": "action",
        "actions": [
          {"tag": "button", "text": {"tag": "plain_text", "content": "✓ 确认执行"}, "type": "primary", "value": {"action": "confirm", "branch": "Standard"}},
          {"tag": "button", "text": {"tag": "plain_text", "content": "⇄ 换简单模式"}, "type": "default", "value": {"action": "downgrade", "branch": "Simple"}},
          {"tag": "button", "text": {"tag": "plain_text", "content": "✕ 取消"}, "type": "danger", "value": {"action": "cancel"}}
        ]
      }
    ]
  }
}
```

**用户点击后 → 我收到回调 → 执行对应操作**

---

### 2.3 实时进度推送（消息更新）

**实现机制：**
```javascript
// 1. 先发送初始消息，记录 message_id
const progressMsg = await sendFeishuMessage({
  content: "⏳ 任务执行中... 0%"
});
const messageId = progressMsg.message_id;

// 2. 定时轮询子代理状态（Cron）
cron.schedule('*/10 * * * * *', async () => {
  const status = await checkSubagentStatus(runId);
  
  // 3. 更新消息
  await updateFeishuMessage(messageId, {
    content: `⏳ 任务执行中... ${status.progress}%\n已耗时：${status.elapsed}s`
  });
  
  // 4. 完成时更新为结果
  if (status.completed) {
    await updateFeishuMessage(messageId, {
      content: `✅ 任务完成\n耗时：${status.duration}s\n成本：¥${status.cost}`
    });
  }
});
```

---

### 2.4 轻量级并发控制（SQLite模拟）

```sql
-- 并发状态表
CREATE TABLE concurrency_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  running_standard INTEGER DEFAULT 0,
  running_batch INTEGER DEFAULT 0,
  running_deep INTEGER DEFAULT 0,
  updated_at TIMESTAMP
);

-- 检查是否有容量
SELECT 
  CASE 
    WHEN running_standard < 4 THEN 'available'
    ELSE 'full'
  END as status
FROM concurrency_state;

-- 占用槽位
UPDATE concurrency_state 
SET running_standard = running_standard + 1,
    updated_at = CURRENT_TIMESTAMP;

-- 释放槽位（子代理完成时）
UPDATE concurrency_state 
SET running_standard = running_standard - 1;
```

**说明：** 不是真正的全局锁，但在单飞书群聊/单用户场景下足够用。

---

### 2.5 成本预估与监控

**预估模型（基于历史数据）：**
```javascript
function estimateCost(task, branch) {
  const history = db.query(`
    SELECT AVG(cost) as avg_cost, 
           AVG(duration) as avg_duration,
           COUNT(*) as count
    FROM task_history
    WHERE branch = ? 
      AND input_length BETWEEN ? AND ?
  `, [branch, task.length * 0.8, task.length * 1.2]);
  
  if (history.count > 5) {
    return {
      cost: history.avg_cost * 1.1,  // 加10%缓冲
      duration: history.avg_duration * 1.2,
      confidence: 'high'
    };
  }
  
  // 无历史数据时用启发式
  return heuristicEstimate(task, branch);
}
```

**实时监控（通过消息更新）：**
```
进度更新包含：
- 当前token使用量（子代理定期报告）
- 预估剩余token
- 当前成本（基于token数 × 模型单价）
- 若超80%预算 → 消息变红警告
```

---

### 2.6 失败恢复与检查点

**SQLite存储检查点：**
```sql
CREATE TABLE checkpoints (
  id INTEGER PRIMARY KEY,
  task_id TEXT,
  progress INTEGER,
  intermediate_result TEXT,
  created_at TIMESTAMP
);
```

**恢复逻辑：**
```javascript
async function resumeFromCheckpoint(taskId) {
  const checkpoint = db.query(`
    SELECT * FROM checkpoints 
    WHERE task_id = ? 
    ORDER BY created_at DESC 
    LIMIT 1
  `, [taskId]);
  
  if (checkpoint) {
    // 从检查点恢复，而非从头开始
    return spawnWithContext(taskId, checkpoint.intermediate_result);
  }
  
  // 无检查点，全新启动
  return spawnNew(taskId);
}
```

---

### 2.7 可视化报表（Plotly生成图片）

**每日/周报自动生成：**
```javascript
// 查询统计数据
const stats = db.query(`
  SELECT 
    DATE(created_at) as date,
    branch,
    COUNT(*) as count,
    AVG(duration) as avg_duration,
    SUM(cost) as total_cost
  FROM task_history
  WHERE created_at > DATE('now', '-7 days')
  GROUP BY DATE(created_at), branch
`);

// 生成图表
const chart = await generateChart(stats, {
  type: 'line',
  title: '7日任务统计',
  x: 'date',
  y: ['count', 'total_cost']
});

// 发送飞书
await sendFeishuImage(chart);
```

---

## 三、完整配置（飞书+SQLite版）

```json5
{
  "adaptiveSubagent": {
    "channel": "feishu",
    
    "database": {
      "type": "sqlite",
      "path": "~/.openclaw/workspace/subagent.db",
      "tables": ["task_history", "concurrency_state", "checkpoints"]
    },
    
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
      "Deep": {
        "mode": "session",
        "thread": true,
        "cleanup": "keep",
        "model": "kimi-coding/k2p5",
        "reasoning": true
      }
    },
    
    "userConfirmation": {
      "enabled": true,
      "excludeSimple": true,
      "showEstimation": true,
      "showHistoryStats": true,  // 新增：显示历史成功率
      "timeout": 60
    },
    
    "concurrency": {
      "localMode": true,  // SQLite模拟，非真正全局
      "limits": {
        "Standard": 4,
        "Batch": 2,
        "Deep": 1
      }
    },
    
    "monitoring": {
      "progressUpdateInterval": 10,  // 每10秒更新
      "costAlertThreshold": 0.8,
      "checkpointInterval": 300      // 每5分钟存检查点
    },
    
    "reporting": {
      "dailyReport": true,
      "chartType": "plotly",
      "sendTo": "feishu"
    }
  }
}
```

---

## 四、实施路线图（技能版）

### Phase 1: 飞书基础（1周）
- [ ] 飞书卡片确认界面
- [ ] 按钮交互处理
- [ ] 基础消息更新

### Phase 2: SQLite数据层（1周）
- [ ] 历史记录表
- [ ] 成本预估查询
- [ ] 轻量级并发计数

### Phase 3: 监控增强（1周）
- [ ] Cron定时轮询
- [ ] 实时进度更新
- [ ] 成本告警

### Phase 4: 可视化（1周）
- [ ] Plotly图表生成
- [ ] 日报/周报自动发送
- [ ] 趋势分析

---

## 五、架构限制说明

**依然无法实现（架构限制）：**
1. ❌ 真正的全局并发控制（跨会话）
2. ❌ 动态升级子代理策略（子代理启动后不可变）
3. ❌ 子代理内部实时干预（只能kill后重开）

**通过技能近似实现：**
1. ✅ 本地并发控制（SQLite单文件）
2. ✅ 成本预估（历史数据训练）
3. ✅ 进度监控（定时轮询+消息更新）
4. ✅ 检查点恢复（定期存储状态）

---

**文档路径：** `memory/subagent-skills-enhanced.md`
