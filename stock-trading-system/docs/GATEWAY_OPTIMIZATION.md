# OpenClaw Gateway 性能优化配置

## 当前问题
- 飞书消息响应较慢
- Gateway轮询间隔可能过长

## 优化目标
- 减少消息处理延迟
- 提高响应速度

---

## 优化方案

### 1. 异步消息处理 (已实现)

文件位置: `utils/async_handler.py` 和 `utils/feishu_fast_notifier.py`

**工作原理:**
```
用户发送消息
    ↓
立即回复"处理中" (100ms内)
    ↓
后台异步处理 (不阻塞)
    ↓
处理完成推送结果
```

**使用方式:**
```python
from utils.feishu_fast_notifier import FeishuFastNotifier

notifier = FeishuFastNotifier()

# 异步执行耗时任务
task_id = notifier.execute_async(long_task_function, arg1, arg2)

# 立即返回"处理中"给用户
return "⏳ 正在处理中，请稍候..."
```

---

### 2. Gateway配置优化

**建议配置调整:**

```yaml
# ~/.openclaw/config.yaml

# 消息轮询间隔 (默认可能较长)
polling:
  interval_ms: 500  # 降低到500ms
  
# 飞书特定配置
feishu:
  # Webhook超时时间
  webhook_timeout: 5  # 5秒
  
  # 连接池设置
  connection_pool:
    max_connections: 10
    max_keepalive: 30
  
  # 重试配置
  retry:
    max_retries: 3
    retry_delay: 1
```

**Gateway启动参数:**
```bash
# 启动Gateway时指定优化参数
openclaw gateway start --polling-interval=500ms
```

---

## 具体优化命令

### 查看当前配置
```bash
openclaw config get
```

### 调整轮询间隔
```bash
# 设置轮询间隔为500ms
openclaw config set gateway.polling_interval 500
```

### 调整消息处理超时
```bash
# 设置消息处理超时为30秒
openclaw config set feishu.message_timeout 30
```

### 启用连接池
```bash
openclaw config set feishu.connection_pool.enabled true
openclaw config set feishu.connection_pool.max_connections 10
```

---

## 性能测试

### 测试脚本
```bash
# 测试飞书消息响应时间
python utils/test_feishu_latency.py
```

### 预期结果
- **优化前**: 2-5秒响应
- **优化后**: 
  - 立即响应: <100ms ("处理中")
  - 完整响应: 取决于任务复杂度

---

## 注意事项

1. **异步处理适用于:**
   - 耗时超过1秒的任务
   - 文件读写操作
   - API调用
   - 复杂计算

2. **同步处理适用于:**
   - 简单查询 (<500ms)
   - 快速响应类任务
   - 需要立即反馈的操作

3. **Gateway配置调整:**
   - 轮询间隔过短会增加CPU负载
   - 需要根据服务器性能调整
   - 建议范围: 100ms - 1000ms

---

## 进一步优化建议

1. **Redis缓存**: 缓存常用数据减少API调用
2. **连接池**: 复用HTTP连接减少握手时间
3. **批量处理**: 合并多个消息批量推送
4. **CDN加速**: 如果飞书服务器在海外

---

**更新日期**: 2026-02-24
**版本**: v0.1.0
