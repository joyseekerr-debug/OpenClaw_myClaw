/**
 * 分布式追踪系统
 * 全链路追踪和性能监控
 */

const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');

/**
 * 追踪管理器
 */
class TracingManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this.enabled = options.enabled !== false;
    this.sampleRate = options.sampleRate || 1.0; // 100%采样
    this.includeTools = options.includeTools !== false;
    this.outputDir = options.outputDir || './traces';
    this.maxTraces = options.maxTraces || 100;
    
    this.activeTraces = new Map();
    this.completedTraces = [];
    this.spanIdCounter = 0;
    
    // 确保输出目录存在
    if (this.enabled && !fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * 开始追踪
   */
  startTrace(taskId, metadata = {}) {
    if (!this.enabled) return null;
    
    // 采样检查
    if (Math.random() > this.sampleRate) {
      return null;
    }
    
    const traceId = this.generateTraceId();
    const trace = {
      traceId,
      taskId,
      startTime: Date.now(),
      status: 'running',
      spans: [],
      metadata: {
        branch: metadata.branch,
        model: metadata.model,
        userId: metadata.userId,
        ...metadata
      },
      metrics: {
        toolCalls: 0,
        tokensIn: 0,
        tokensOut: 0,
        errors: 0
      }
    };
    
    this.activeTraces.set(taskId, trace);
    
    this.emit('trace-started', { traceId, taskId });
    
    return traceId;
  }

  /**
   * 开始Span
   */
  startSpan(taskId, name, parentSpanId = null) {
    if (!this.enabled) return null;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return null;
    
    const spanId = this.generateSpanId();
    const span = {
      spanId,
      parentSpanId,
      name,
      startTime: Date.now(),
      status: 'running',
      tags: {},
      logs: []
    };
    
    trace.spans.push(span);
    
    return spanId;
  }

  /**
   * 结束Span
   */
  endSpan(taskId, spanId, tags = {}) {
    if (!this.enabled) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    const span = trace.spans.find(s => s.spanId === spanId);
    if (!span) return;
    
    span.endTime = Date.now();
    span.duration = span.endTime - span.startTime;
    span.status = 'completed';
    span.tags = { ...span.tags, ...tags };
    
    this.emit('span-ended', { traceId: trace.traceId, spanId, duration: span.duration });
  }

  /**
   * 记录Span日志
   */
  logSpan(taskId, spanId, level, message, fields = {}) {
    if (!this.enabled) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    const span = trace.spans.find(s => s.spanId === spanId);
    if (!span) return;
    
    span.logs.push({
      timestamp: Date.now(),
      level,
      message,
      fields
    });
  }

  /**
   * 记录工具调用
   */
  recordToolCall(taskId, toolName, params, result, duration) {
    if (!this.enabled || !this.includeTools) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    trace.metrics.toolCalls++;
    
    // 创建一个工具调用的span
    const spanId = this.startSpan(taskId, `tool:${toolName}`);
    if (spanId) {
      this.endSpan(taskId, spanId, {
        tool: toolName,
        duration,
        success: !result.error
      });
    }
    
    this.emit('tool-recorded', { taskId, tool: toolName, duration });
  }

  /**
   * 记录Token使用
   */
  recordTokens(taskId, tokensIn, tokensOut) {
    if (!this.enabled) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    trace.metrics.tokensIn += tokensIn;
    trace.metrics.tokensOut += tokensOut;
  }

  /**
   * 记录错误
   */
  recordError(taskId, error, spanId = null) {
    if (!this.enabled) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    trace.metrics.errors++;
    
    const errorInfo = {
      timestamp: Date.now(),
      message: error.message || String(error),
      stack: error.stack,
      spanId
    };
    
    if (!trace.errors) trace.errors = [];
    trace.errors.push(errorInfo);
    
    // 标记span为错误
    if (spanId) {
      const span = trace.spans.find(s => s.spanId === spanId);
      if (span) {
        span.status = 'error';
        span.error = errorInfo;
      }
    }
    
    this.emit('error-recorded', { taskId, error: errorInfo });
  }

  /**
   * 结束追踪
   */
  endTrace(taskId, status = 'completed', result = null) {
    if (!this.enabled) return;
    
    const trace = this.activeTraces.get(taskId);
    if (!trace) return;
    
    trace.endTime = Date.now();
    trace.duration = trace.endTime - trace.startTime;
    trace.status = status;
    trace.result = result;
    
    // 结束所有未结束的span
    for (const span of trace.spans) {
      if (span.status === 'running') {
        span.endTime = trace.endTime;
        span.duration = span.endTime - span.startTime;
        span.status = status === 'error' ? 'error' : 'completed';
      }
    }
    
    // 移动到已完成列表
    this.completedTraces.push(trace);
    this.activeTraces.delete(taskId);
    
    // 限制历史数量
    if (this.completedTraces.length > this.maxTraces) {
      this.completedTraces.shift();
    }
    
    // 保存追踪数据
    this.saveTrace(trace);
    
    this.emit('trace-ended', {
      traceId: trace.traceId,
      taskId,
      duration: trace.duration,
      status
    });
    
    return trace;
  }

  /**
   * 保存追踪到文件
   */
  saveTrace(trace) {
    try {
      const filename = `trace_${trace.traceId}_${Date.now()}.json`;
      const filepath = path.join(this.outputDir, filename);
      fs.writeFileSync(filepath, JSON.stringify(trace, null, 2));
    } catch (e) {
      console.error('[TracingManager] 保存追踪失败:', e.message);
    }
  }

  /**
   * 生成追踪ID
   */
  generateTraceId() {
    return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 生成Span ID
   */
  generateSpanId() {
    return `span_${++this.spanIdCounter}_${Math.random().toString(36).substr(2, 5)}`;
  }

  /**
   * 获取追踪数据
   */
  getTrace(taskId) {
    // 先查活跃的
    const active = this.activeTraces.get(taskId);
    if (active) return active;
    
    // 再查已完成的
    return this.completedTraces.find(t => t.taskId === taskId);
  }

  /**
   * 获取所有追踪
   */
  getAllTraces(options = {}) {
    const traces = [...this.completedTraces];
    
    if (options.status) {
      return traces.filter(t => t.status === options.status);
    }
    
    if (options.branch) {
      return traces.filter(t => t.metadata.branch === options.branch);
    }
    
    if (options.since) {
      return traces.filter(t => t.startTime >= options.since);
    }
    
    return traces;
  }

  /**
   * 生成火焰图数据
   */
  generateFlameGraph(taskId) {
    const trace = this.getTrace(taskId);
    if (!trace) return null;
    
    const rootSpans = trace.spans.filter(s => !s.parentSpanId);
    
    return {
      name: trace.metadata.branch || 'root',
      value: trace.duration,
      children: rootSpans.map(span => this.buildFlameNode(span, trace.spans))
    };
  }

  /**
   * 构建火焰图节点
   */
  buildFlameNode(span, allSpans) {
    const children = allSpans.filter(s => s.parentSpanId === span.spanId);
    
    return {
      name: span.name,
      value: span.duration,
      start: span.startTime,
      status: span.status,
      children: children.map(child => this.buildFlameNode(child, allSpans))
    };
  }

  /**
   * 自动诊断异常
   */
  diagnose(taskId) {
    const trace = this.getTrace(taskId);
    if (!trace) return null;
    
    const issues = [];
    
    // 1. 检查错误
    if (trace.metrics.errors > 0) {
      issues.push({
        severity: 'high',
        type: 'error',
        message: `任务执行中出现 ${trace.metrics.errors} 个错误`,
        suggestion: '查看错误详情，检查是否需要重试或调整策略'
      });
    }
    
    // 2. 检查耗时异常
    const expectedDuration = this.getExpectedDuration(trace.metadata.branch);
    if (trace.duration > expectedDuration * 2) {
      issues.push({
        severity: 'medium',
        type: 'slow',
        message: `执行时间 ${trace.duration}ms 远超预期 ${expectedDuration}ms`,
        suggestion: '考虑升级策略或优化任务分解'
      });
    }
    
    // 3. 检查工具调用异常
    const toolCalls = trace.metrics.toolCalls;
    if (toolCalls > 50) {
      issues.push({
        severity: 'low',
        type: 'heavy',
        message: `工具调用次数较多 (${toolCalls}次)`,
        suggestion: '考虑批量处理或减少不必要的工具调用'
      });
    }
    
    // 4. 检查span层级过深
    const maxDepth = this.getMaxSpanDepth(trace.spans);
    if (maxDepth > 5) {
      issues.push({
        severity: 'low',
        type: 'deep',
        message: `调用层级较深 (${maxDepth}层)`,
        suggestion: '考虑简化任务结构'
      });
    }
    
    return {
      traceId: trace.traceId,
      taskId,
      score: this.calculateHealthScore(trace, issues),
      issues,
      recommendations: issues.map(i => i.suggestion)
    };
  }

  /**
   * 获取预期耗时
   */
  getExpectedDuration(branch) {
    const durations = {
      'Simple': 10000,
      'Standard': 60000,
      'Batch': 120000,
      'Orchestrator': 180000,
      'Deep': 300000
    };
    return durations[branch] || 60000;
  }

  /**
   * 计算最大span深度
   */
  getMaxSpanDepth(spans) {
    let maxDepth = 0;
    
    const calcDepth = (spanId, depth) => {
      maxDepth = Math.max(maxDepth, depth);
      const children = spans.filter(s => s.parentSpanId === spanId);
      for (const child of children) {
        calcDepth(child.spanId, depth + 1);
      }
    };
    
    const roots = spans.filter(s => !s.parentSpanId);
    for (const root of roots) {
      calcDepth(root.spanId, 1);
    }
    
    return maxDepth;
  }

  /**
   * 计算健康分数
   */
  calculateHealthScore(trace, issues) {
    let score = 100;
    
    for (const issue of issues) {
      switch (issue.severity) {
        case 'high': score -= 30; break;
        case 'medium': score -= 15; break;
        case 'low': score -= 5; break;
      }
    }
    
    return Math.max(0, score);
  }

  /**
   * 获取统计信息
   */
  getStats() {
    const traces = this.completedTraces;
    
    if (traces.length === 0) {
      return { totalTraces: 0 };
    }
    
    const totalDuration = traces.reduce((sum, t) => sum + (t.duration || 0), 0);
    const totalErrors = traces.reduce((sum, t) => sum + (t.metrics?.errors || 0), 0);
    
    return {
      totalTraces: traces.length,
      activeTraces: this.activeTraces.size,
      avgDuration: Math.floor(totalDuration / traces.length),
      totalErrors,
      errorRate: (totalErrors / traces.length * 100).toFixed(1) + '%',
      byBranch: this.groupByBranch(traces),
      byStatus: this.groupByStatus(traces)
    };
  }

  /**
   * 按分支分组
   */
  groupByBranch(traces) {
    const groups = {};
    for (const trace of traces) {
      const branch = trace.metadata.branch || 'unknown';
      if (!groups[branch]) groups[branch] = { count: 0, avgDuration: 0 };
      groups[branch].count++;
      groups[branch].avgDuration += trace.duration || 0;
    }
    
    for (const branch in groups) {
      groups[branch].avgDuration = Math.floor(groups[branch].avgDuration / groups[branch].count);
    }
    
    return groups;
  }

  /**
   * 按状态分组
   */
  groupByStatus(traces) {
    const groups = {};
    for (const trace of traces) {
      const status = trace.status || 'unknown';
      groups[status] = (groups[status] || 0) + 1;
    }
    return groups;
  }
}

module.exports = {
  TracingManager
};
