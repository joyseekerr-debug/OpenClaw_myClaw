-- SQLite数据库表结构
-- 子代理调度系统数据库

-- 任务历史表：记录所有任务执行情况，用于成本预估
CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_hash TEXT NOT NULL,
    task_preview TEXT,
    branch TEXT NOT NULL,  -- Simple/Standard/Batch/Orchestrator/Deep
    duration_ms INTEGER,   -- 实际耗时（毫秒）
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost REAL,   -- 预估成本
    actual_cost REAL,      -- 实际成本
    success BOOLEAN DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 并发状态表：本地并发控制
CREATE TABLE IF NOT EXISTS concurrency_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    running_simple INTEGER DEFAULT 0,
    running_standard INTEGER DEFAULT 0,
    running_batch INTEGER DEFAULT 0,
    running_orchestrator INTEGER DEFAULT 0,
    running_deep INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 检查点表：任务失败恢复
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    run_id TEXT,
    progress INTEGER DEFAULT 0,  -- 0-100
    intermediate_result TEXT,
    metadata TEXT,  -- JSON格式存储额外信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 飞书消息记录表：跟踪消息ID用于更新
CREATE TABLE IF NOT EXISTS feishu_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    chat_id TEXT,
    msg_type TEXT,  -- card/text/image
    content_preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_task_hash ON task_history(task_hash);
CREATE INDEX IF NOT EXISTS idx_branch ON task_history(branch);
CREATE INDEX IF NOT EXISTS idx_created_at ON task_history(created_at);
CREATE INDEX IF NOT EXISTS idx_task_id ON checkpoints(task_id);

-- 初始化并发状态（如果不存在）
INSERT OR IGNORE INTO concurrency_state (id) VALUES (1);
