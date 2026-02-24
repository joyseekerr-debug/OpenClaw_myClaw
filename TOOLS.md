# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 核心技能 (Core Skills)

### 子代理自适应调度器

**路径:** `skills/subagent-scheduler/`
**版本:** v1.3.0 (Phase 4)

**使用方式:**
```javascript
const { SubagentScheduler } = require('./skills/subagent-scheduler');
const scheduler = new SubagentScheduler();
await scheduler.init();

// 执行任务（自动决策是否spawn）
const result = await scheduler.execute({
  task: "用户任务描述",
  chatId: currentChatId
});
```

**关键配置:**
- 每日6:00 自动分析历史数据
- 每日9:00 推送优化报告
- 成本上限: 单任务$1, 日$50

**详细文档:** 见 `CORE-SKILL.md`

---

Add whatever helps you do your job. This is your cheat sheet.
