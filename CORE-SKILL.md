# 核心技能配置

## 子代理自适应调度器 (Primary Skill)

这是我最核心的技能，用于智能决定是否以及如何使用子代理。

### 技能路径
`skills/subagent-scheduler/`

### 集成方式

在主会话中初始化并使用：

```javascript
const { SubagentScheduler } = require('./skills/subagent-scheduler');

// 初始化调度器
const scheduler = new SubagentScheduler({
  // 可选：预算配置
  budget: {
    perTask: 1.0,
    perSession: 10.0,
    perDay: 50.0
  }
});

await scheduler.init();
```

### 使用场景

#### 1. 用户提交任务时自动分类

```javascript
// 用户发来任务
const userTask = "分析这20个日志文件找出错误模式";

// 使用调度器自动决策
const result = await scheduler.execute({
  task: userTask,
  chatId: currentChatId,  // 用于飞书确认和进度通知
  useLLM: true            // 启用LLM分类层
});

// 根据结果处理
if (result.branch === 'Simple') {
  // 直接处理，不spawn
} else {
  // 已经自动spawn子代理执行
}
```

#### 2. 手动分类检查

```javascript
// 先检查应该使用什么策略
const classification = await scheduler.scheduler.classifyTask(task);
console.log(`推荐策略: ${classification.branch} (置信度: ${classification.confidence})`);

// 根据分类决定是否spawn
if (classification.branch === 'Simple') {
  // 自己处理
} else {
  // 使用execute自动spawn
  await scheduler.execute({ task });
}
```

#### 3. 批量任务处理

```javascript
const tasks = ["任务1", "任务2", "任务3", ...];

for (const task of tasks) {
  const result = await scheduler.execute({
    task,
    chatId: currentChatId
  });
  
  // 结果会包含分支、耗时、成本等信息
  console.log(`任务完成: ${result.branch}, ${result.duration}ms`);
}
```

### 决策流程

当我收到一个任务时：

```
1. 分析任务特征
   ↓
2. 三层决策器分类
   - 快速规则 (高置信度 → 直接返回)
   - 历史数据校准
   - LLM智能分类
   ↓
3. 检查成本预算
   ↓
4. [非Simple分支] 用户确认
   ↓
5. 执行
   - Simple: 直接处理
   - 其他: spawn子代理
   ↓
6. 记录历史 → 用于学习优化
```

### 日常自动化

启动每日学习和报告：

```javascript
// 启动定时任务
// - 每天6:00 分析历史数据
// - 每天9:00 推送优化报告
scheduler.startDailyLearning(feishuChatId);
```

### 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| costLimits.perTask | 1.0 USD | 单任务成本上限 |
| confirmation.enabled | true | 非Simple分支需要用户确认 |
| phase2.llmClassifier.enabled | true | 启用LLM分类层 |
| phase4.learning.enabled | true | 启用每日学习 |

### 我的使用原则

1. **所有任务先过调度器** - 不再凭感觉决定是否spawn
2. **尊重用户确认** - 非Simple分支必须等用户确认
3. **记录所有执行** - 用于学习优化
4. **关注每日报告** - 根据优化建议调整策略

### 技能文件清单

- `index.js` - 主入口
- `scheduler.js` - 核心调度
- `llm-classifier.js` - LLM分类
- `learning-engine.js` - 学习引擎
- `streaming-progress.js` - 流式进度
- `retry-executor.js` - 失败恢复
- `probe-executor.js` - 试探执行
- `layered-context.js` - 上下文管理
- `policy-manager.js` - 权限控制
- `tracing-manager.js` - 分布式追踪
