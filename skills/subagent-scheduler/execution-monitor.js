/**
 * Execution Monitor
 * 执行监控 - 多Agent执行状态实时监控、性能监控、故障检测与恢复
 */

const EventEmitter = require('events');

/**
 * 监控指标类型
 */
const MetricType = {
  EXECUTION_TIME: 'execution_time',     // 执行时间
  QUEUE_LENGTH: 'queue_length',         // 队列长度
  SUCCESS_RATE: 'success_rate',         // 成功率
  ERROR_RATE: 'error_rate',             // 错误率
  THROUGHPUT: 'throughput',             // 吞吐量
  RESOURCE_USAGE: 'resource_usage'      // 资源使用
};

/**
 * 故障类型
 */
const FailureType = {
  TIMEOUT: 'timeout',                   // 超时
  CRASH: 'crash',                       // 崩溃
  RESOURCE_EXHAUSTED: 'resource_exhausted', // 资源耗尽
  COMMUNICATION_ERROR: 'communication_error', // 通信错误
  LOGIC_ERROR: 'logic_error',           // 逻辑错误
  UNKNOWN: 'unknown'                    // 未知
};

/**
 * 执行监控类
 */
class ExecutionMonitor extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.tasks = new Map();              // taskId -> taskInfo
    this.agents = new Map();             // agentId -> agentMetrics
    this.metrics = new Map();            // 指标数据
    this.alerts = [];                    // 告警列表
    this.rules = [];                     // 告警规则
    
    // 配置
    this.config = {
      checkInterval: options.checkInterval || 5000,      // 检查间隔
      metricWindow: options.metricWindow || 3600000,     // 指标窗口(1小时)
      alertCooldown: options.alertCooldown || 300000,    // 告警冷却(5分钟)
      maxTasksHistory: options.maxTasksHistory || 1000,  // 最大任务历史
      ...options
    };
    
    // 启动监控循环
    this.startMonitoring();
  }

  /**
   * 注册任务监控
   */
  registerTask(taskId, taskInfo = {}) {
    const task = {
      id: taskId,
      name: taskInfo.name || taskId,
      agentId: taskInfo.agentId,
      branch: taskInfo.branch || 'Standard',
      status: 'pending',                  // pending, running, completed, failed, cancelled
      progress: 0,
      startTime: null,
      endTime: null,
      duration: 0,
      retries: 0,
      maxRetries: taskInfo.maxRetries || 3,
      metadata: taskInfo.metadata || {},
      checkpoints: [],                    // 检查点
      logs: [],                           // 执行日志
      errors: [],                         // 错误记录
      createdAt: Date.now()
    };
    
    this.tasks.set(taskId, task);
    this.emit('task-registered', task);
    
    return task;
  }

  /**
   * 开始任务执行
   */
  startTask(taskId) {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error(`任务不存在: ${taskId}`);
    }
    
    task.status = 'running';
    task.startTime = Date.now();
    task.progress = 0;
    
    this.emit('task-started', task);
    this.logTaskEvent(taskId, 'STARTED');
  }

  /**
   * 更新任务进度
   */
  updateProgress(taskId, progress, metadata = {}) {
    const task = this.tasks.get(taskId);
    if (!task || task.status !== 'running') {
      return false;
    }
    
    task.progress = Math.min(100, Math.max(0, progress));
    task.duration = Date.now() - task.startTime;
    
    if (metadata.checkpoint) {
      task.checkpoints.push({
        name: metadata.checkpoint,
        progress: task.progress,
        timestamp: Date.now()
      });
    }
    
    this.emit('task-progress', {
      taskId,
      progress: task.progress,
      duration: task.duration,
      metadata
    });
    
    return true;
  }

  /**
   * 完成任务
   */
  completeTask(taskId, result = {}) {
    const task = this.tasks.get(taskId);
    if (!task) return false;
    
    task.status = 'completed';
    task.endTime = Date.now();
    task.duration = task.endTime - (task.startTime || task.endTime);
    task.progress = 100;
    task.result = result;
    
    this.emit('task-completed', task);
    this.logTaskEvent(taskId, 'COMPLETED');
    this.recordMetrics(task);
    
    return true;
  }

  /**
   * 任务失败
   */
  failTask(taskId, error, options = {}) {
    const task = this.tasks.get(taskId);
    if (!task) return false;
    
    task.status = 'failed';
    task.endTime = Date.now();
    task.duration = task.endTime - (task.startTime || task.endTime);
    
    const failureInfo = {
      type: options.type || FailureType.UNKNOWN,
      error: error.message || String(error),
      stack: error.stack,
      timestamp: Date.now(),
      recoverable: options.recoverable !== false
    };
    
    task.errors.push(failureInfo);
    
    this.emit('task-failed', { task, error, failureInfo });
    this.logTaskEvent(taskId, 'FAILED', failureInfo);
    this.recordMetrics(task);
    
    // 尝试恢复
    if (failureInfo.recoverable && task.retries < task.maxRetries) {
      this.attemptRecovery(taskId);
    }
    
    return true;
  }

  /**
   * 取消任务
   */
  cancelTask(taskId, reason = '') {
    const task = this.tasks.get(taskId);
    if (!task || task.status === 'completed') return false;
    
    task.status = 'cancelled';
    task.endTime = Date.now();
    task.cancelReason = reason;
    
    this.emit('task-cancelled', task);
    this.logTaskEvent(taskId, 'CANCELLED', { reason });
    
    return true;
  }

  /**
   * 尝试恢复任务
   */
  attemptRecovery(taskId) {
    const task = this.tasks.get(taskId);
    if (!task || task.status !== 'failed') return false;
    
    task.retries++;
    task.status = 'pending';
    
    // 找到最近的检查点
    const lastCheckpoint = task.checkpoints[task.checkpoints.length - 1];
    const resumeFrom = lastCheckpoint ? lastCheckpoint.name : null;
    
    this.emit('task-recovery-attempted', {
      taskId,
      retryCount: task.retries,
      maxRetries: task.maxRetries,
      resumeFrom
    });
    
    this.logTaskEvent(taskId, 'RECOVERY_ATTEMPTED', {
      retryCount: task.retries,
      resumeFrom
    });
    
    return true;
  }

  /**
   * 注册Agent监控
   */
  registerAgent(agentId, agentInfo = {}) {
    this.agents.set(agentId, {
      id: agentId,
      name: agentInfo.name || agentId,
      status: 'healthy',              // healthy, warning, critical, offline
      currentLoad: 0,
      maxConcurrent: agentInfo.maxConcurrent || 1,
      metrics: {
        tasksCompleted: 0,
        tasksFailed: 0,
        totalExecutionTime: 0,
        averageExecutionTime: 0,
        lastHeartbeat: Date.now()
      },
      activeTasks: new Set(),
      ...agentInfo
    });
  }

  /**
   * 更新Agent负载
   */
  updateAgentLoad(agentId, delta) {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    
    agent.currentLoad = Math.max(0, agent.currentLoad + delta);
    agent.metrics.lastHeartbeat = Date.now();
    
    // 更新状态
    const loadRatio = agent.currentLoad / agent.maxConcurrent;
    if (loadRatio >= 1) {
      agent.status = 'critical';
    } else if (loadRatio >= 0.8) {
      agent.status = 'warning';
    } else {
      agent.status = 'healthy';
    }
  }

  /**
   * Agent心跳
   */
  agentHeartbeat(agentId) {
    const agent = this.agents.get(agentId);
    if (agent) {
      agent.metrics.lastHeartbeat = Date.now();
      if (agent.status === 'offline') {
        agent.status = 'healthy';
        this.emit('agent-recovered', { agentId });
      }
    }
  }

  /**
   * 记录Agent指标
   */
  recordAgentMetrics(agentId, task) {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    
    if (task.status === 'completed') {
      agent.metrics.tasksCompleted++;
      agent.metrics.totalExecutionTime += task.duration;
      agent.metrics.averageExecutionTime = 
        agent.metrics.totalExecutionTime / agent.metrics.tasksCompleted;
    } else if (task.status === 'failed') {
      agent.metrics.tasksFailed++;
    }
    
    agent.activeTasks.delete(task.id);
    this.updateAgentLoad(agentId, -1);
  }

  /**
   * 添加告警规则
   */
  addAlertRule(rule) {
    this.rules.push({
      id: `rule_${Date.now()}`,
      name: rule.name,
      condition: rule.condition,      // 条件函数
      severity: rule.severity || 'warning', // info, warning, critical
      cooldown: rule.cooldown || this.config.alertCooldown,
      action: rule.action,            // 触发动作
      lastTriggered: 0
    });
  }

  /**
   * 检查告警规则
   */
  checkAlerts() {
    const now = Date.now();
    
    for (const rule of this.rules) {
      // 检查冷却期
      if (now - rule.lastTriggered < rule.cooldown) continue;
      
      // 评估条件
      const shouldTrigger = rule.condition({
        tasks: this.tasks,
        agents: this.agents,
        metrics: this.metrics
      });
      
      if (shouldTrigger) {
        rule.lastTriggered = now;
        this.triggerAlert(rule);
      }
    }
  }

  /**
   * 触发告警
   */
  triggerAlert(rule) {
    const alert = {
      id: `alert_${Date.now()}`,
      ruleId: rule.id,
      ruleName: rule.name,
      severity: rule.severity,
      timestamp: Date.now(),
      details: this.gatherAlertDetails(rule)
    };
    
    this.alerts.push(alert);
    this.emit('alert', alert);
    
    // 执行动作
    if (rule.action) {
      rule.action(alert);
    }
    
    console.warn(`[Monitor] 告警触发: ${rule.name} (${rule.severity})`);
  }

  /**
   * 收集告警详情
   */
  gatherAlertDetails(rule) {
    return {
      activeTasks: Array.from(this.tasks.values()).filter(t => t.status === 'running').length,
      failedTasksLastHour: this.getFailedTasksCount(3600000),
      agentStatuses: Array.from(this.agents.entries()).map(([id, a]) => ({
        id, status: a.status, load: a.currentLoad
      }))
    };
  }

  /**
   * 获取最近失败任务数
   */
  getFailedTasksCount(windowMs) {
    const cutoff = Date.now() - windowMs;
    return Array.from(this.tasks.values())
      .filter(t => t.status === 'failed' && t.endTime > cutoff)
      .length;
  }

  /**
   * 记录指标
   */
  recordMetrics(task) {
    const timestamp = Date.now();
    const branch = task.branch;
    
    // 执行时间指标
    this.addMetric(MetricType.EXECUTION_TIME, branch, {
      value: task.duration,
      timestamp,
      taskId: task.id
    });
    
    // 成功率指标
    const success = task.status === 'completed' ? 1 : 0;
    this.addMetric(MetricType.SUCCESS_RATE, branch, {
      value: success,
      timestamp
    });
    
    // Agent指标
    if (task.agentId) {
      this.recordAgentMetrics(task.agentId, task);
    }
  }

  /**
   * 添加指标
   */
  addMetric(type, category, data) {
    const key = `${type}:${category}`;
    
    if (!this.metrics.has(key)) {
      this.metrics.set(key, []);
    }
    
    const series = this.metrics.get(key);
    series.push(data);
    
    // 清理过期数据
    const cutoff = Date.now() - this.config.metricWindow;
    while (series.length > 0 && series[0].timestamp < cutoff) {
      series.shift();
    }
  }

  /**
   * 获取指标统计
   */
  getMetricStats(type, category) {
    const key = `${type}:${category}`;
    const series = this.metrics.get(key) || [];
    
    if (series.length === 0) return null;
    
    const values = series.map(d => d.value);
    const sum = values.reduce((a, b) => a + b, 0);
    
    return {
      count: values.length,
      sum,
      average: sum / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      p50: this.percentile(values, 0.5),
      p90: this.percentile(values, 0.9),
      p95: this.percentile(values, 0.95)
    };
  }

  /**
   * 计算百分位数
   */
  percentile(sorted, p) {
    const values = [...sorted].sort((a, b) => a - b);
    const index = Math.ceil(values.length * p) - 1;
    return values[Math.max(0, index)];
  }

  /**
   * 记录任务事件
   */
  logTaskEvent(taskId, event, data = {}) {
    const task = this.tasks.get(taskId);
    if (task) {
      task.logs.push({
        event,
        timestamp: Date.now(),
        data
      });
    }
  }

  /**
   * 启动监控循环
   */
  startMonitoring() {
    // 定期检查
    this.monitorInterval = setInterval(() => {
      this.performChecks();
    }, this.config.checkInterval);
    
    // 检查Agent健康状态
    this.healthCheckInterval = setInterval(() => {
      this.checkAgentHealth();
    }, 30000); // 30秒检查一次
    
    console.log('[Monitor] 监控已启动');
  }

  /**
   * 执行检查
   */
  performChecks() {
    // 检查任务超时
    this.checkTaskTimeouts();
    
    // 检查告警规则
    this.checkAlerts();
    
    // 清理历史数据
    this.cleanup();
  }

  /**
   * 检查任务超时
   */
  checkTaskTimeouts() {
    const now = Date.now();
    const timeoutThreshold = 300000; // 5分钟无进度视为超时
    
    for (const [taskId, task] of this.tasks) {
      if (task.status !== 'running') continue;
      
      const lastUpdate = task.checkpoints.length > 0
        ? task.checkpoints[task.checkpoints.length - 1].timestamp
        : task.startTime;
      
      if (now - lastUpdate > timeoutThreshold) {
        this.emit('task-stalled', { taskId, stallDuration: now - lastUpdate });
        console.warn(`[Monitor] 任务停滞警告: ${taskId}`);
      }
    }
  }

  /**
   * 检查Agent健康状态
   */
  checkAgentHealth() {
    const now = Date.now();
    const heartbeatTimeout = 60000; // 1分钟无心跳视为离线
    
    for (const [agentId, agent] of this.agents) {
      if (now - agent.metrics.lastHeartbeat > heartbeatTimeout) {
        agent.status = 'offline';
        this.emit('agent-offline', { agentId });
        console.warn(`[Monitor] Agent离线: ${agentId}`);
      }
    }
  }

  /**
   * 清理历史数据
   */
  cleanup() {
    // 清理已完成的旧任务
    const cutoff = Date.now() - this.config.metricWindow;
    
    for (const [taskId, task] of this.tasks) {
      if ((task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled')
          && task.endTime < cutoff) {
        this.tasks.delete(taskId);
      }
    }
    
    // 限制告警历史
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100);
    }
  }

  /**
   * 获取监控仪表板数据
   */
  getDashboard() {
    const tasks = Array.from(this.tasks.values());
    
    return {
      summary: {
        total: tasks.length,
        running: tasks.filter(t => t.status === 'running').length,
        completed: tasks.filter(t => t.status === 'completed').length,
        failed: tasks.filter(t => t.status === 'failed').length,
        pending: tasks.filter(t => t.status === 'pending').length
      },
      agents: Array.from(this.agents.entries()).map(([id, a]) => ({
        id,
        name: a.name,
        status: a.status,
        load: `${a.currentLoad}/${a.maxConcurrent}`,
        tasksCompleted: a.metrics.tasksCompleted,
        tasksFailed: a.metrics.tasksFailed
      })),
      metrics: {
        executionTime: this.getMetricStats(MetricType.EXECUTION_TIME, 'Standard'),
        successRate: this.getMetricStats(MetricType.SUCCESS_RATE, 'Standard')
      },
      recentAlerts: this.alerts.slice(-5),
      activeTasks: tasks
        .filter(t => t.status === 'running')
        .map(t => ({
          id: t.id,
          name: t.name,
          progress: t.progress,
          duration: t.duration,
          agentId: t.agentId
        }))
    };
  }

  /**
   * 获取任务详情
   */
  getTaskDetails(taskId) {
    return this.tasks.get(taskId);
  }

  /**
   * 停止监控
   */
  stop() {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
    }
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    console.log('[Monitor] 监控已停止');
  }

  /**
   * 关闭监控器
   */
  close() {
    this.stop();
    this.tasks.clear();
    this.agents.clear();
    this.metrics.clear();
    this.alerts = [];
    this.rules = [];
    this.removeAllListeners();
  }
}

module.exports = {
  ExecutionMonitor,
  MetricType,
  FailureType
};
