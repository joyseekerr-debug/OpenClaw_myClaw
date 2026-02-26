# MEMORY.md - 长期记忆

## 系统配置

### 指令队列 (Command Queue)
**状态:** ✅ 已启用，自动启动
**配置:** `skills/subagent-scheduler/queue-config.json`

**功能:**
- 飞书消息自动排队执行
- 单线程顺序处理，避免冲突
- 高优先级关键词插队
- 自动通知队列状态

**使用方式:**
```javascript
const { getMessageHandler } = require('./skills/subagent-scheduler');
const handler = getMessageHandler();

// 处理消息（自动排队）
await handler.handleMessage(message, chatId, userInfo);
```

### 每日学习定时任务
**状态:** ✅ 已启用，自动启动（每天6:00分析，9:00推送）
**配置:** `config.json` - `phase4.learning.autoStart: true`

### 自动路由 (Auto Router)
**状态:** ✅ 已启用
**配置:** `config.json` - `phase5.autoRouter.enabled: true`
- 任务复杂度自动检测
- 复杂任务自动触发用户确认

### 多Agent协作
**状态:** ✅ 已启用
**配置:** `config.json` - `phase5.multiAgent.autoTrigger: true`
- 复杂度≥70分自动启用多Agent模式

## 工作流程约定

### 知识积累流程
当获得新的使用技巧或经验时：
1. 更新到 `OpenClaw_myClaw` 项目
2. 推送到 GitHub（包括记忆文件 memory/ 和 MEMORY.md）

## 用户偏好

### 语言
- 用户使用中文交流
- 我应该使用中文回复

### 记录原则
- 精简、准确
- 减少 token，提高速度

## 重要教训

### 阶段性工作汇报原则
**问题:** 2026-02-24 完成 Phase 3 开发后，未及时汇报，导致用户等待19分钟

**根因:** 优先处理技术收尾（文档/提交），而非先告知用户

**规则:**
1. 完成阶段性目标 → **立即汇报** → 再做技术收尾
2. 用户询问进展时 → 先回答状态 → 再解释细节
3. 预计耗时 >10分钟的任务 → 开始前告知，完成后立即汇报

**正确流程:**
```
完成任务 → 通知用户 ✅ → 推送代码/更新文档
```

**避免:**
```
完成任务 → 推送代码/更新文档 → 通知用户 ❌
```
