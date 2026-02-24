/**
 * 流式进度通知系统
 * 实时向飞书推送子代理执行进度
 */

const EventEmitter = require('events');
const config = require('./config.json');

/**
 * 流式进度管理器
 */
class StreamingProgress extends EventEmitter {
  constructor(options = {}) {
    super();
    this.updateInterval = options.updateInterval || config.monitoring?.progressUpdateInterval || 10;
    this.minUpdateDelta = options.minUpdateDelta || 5; // 最小进度变化才更新（避免刷屏）
    this.activeStreams = new Map();
  }

  /**
   * 启动流式进度监控
   * @param {string} taskId - 任务ID
   * @param {string} messageId - 飞书消息ID
   * @param {Function} feishuUpdater - 飞书消息更新函数
   * @param {Object} options - 配置选项
   */
  start(taskId, messageId, feishuUpdater, options = {}) {
    const stream = {
      taskId,
      messageId,
      feishuUpdater,
      startTime: Date.now(),
      lastUpdate: 0,
      lastProgress: 0,
      estimatedDuration: options.estimatedDuration || 60,
      branch: options.branch || 'Standard',
      status: 'running',
      metadata: options.metadata || {}
    };

    this.activeStreams.set(taskId, stream);

    // 立即发送初始进度
    this.updateProgress(taskId, 0, '任务启动中...');

    // 启动定时更新
    const intervalId = setInterval(() => {
      this.autoUpdateProgress(taskId);
    }, this.updateInterval * 1000);

    stream.intervalId = intervalId;

    console.log(`[StreamingProgress] 启动进度流: ${taskId}, 预估: ${stream.estimatedDuration}秒`);
    
    this.emit('started', { taskId, messageId });
    
    return stream;
  }

  /**
   * 自动更新进度（基于时间估算）
   */
  autoUpdateProgress(taskId) {
    const stream = this.activeStreams.get(taskId);
    if (!stream || stream.status !== 'running') return;

    const elapsed = (Date.now() - stream.startTime) / 1000;
    const estimated = stream.estimatedDuration;
    
    // 基于时间的进度估算
    let progress = Math.min(95, Math.floor((elapsed / estimated) * 100));
    
    // 添加一些随机波动使其更自然
    if (progress < stream.lastProgress) {
      progress = stream.lastProgress;
    }
    
    // 确保进度在增长
    if (progress <= stream.lastProgress) {
      progress = Math.min(95, stream.lastProgress + Math.floor(Math.random() * 3) + 1);
    }

    const status = this.getStatusText(progress);
    this.updateProgress(taskId, progress, status);
  }

  /**
   * 获取状态文本
   */
  getStatusText(progress) {
    if (progress < 20) return '分析任务中...';
    if (progress < 40) return '收集数据中...';
    if (progress < 60) return '处理数据中...';
    if (progress < 80) return '分析结果中...';
    if (progress < 95) return '整理输出中...';
    return '即将完成...';
  }

  /**
   * 手动更新进度
   */
  updateProgress(taskId, progress, statusText = null) {
    const stream = this.activeStreams.get(taskId);
    if (!stream) return false;

    // 检查最小变化阈值
    if (Math.abs(progress - stream.lastProgress) < this.minUpdateDelta && progress < 100) {
      return false;
    }

    stream.lastProgress = progress;
    stream.lastUpdate = Date.now();

    const elapsed = Math.floor((Date.now() - stream.startTime) / 1000);
    const status = statusText || this.getStatusText(progress);

    // 构建进度消息
    const message = this.buildProgressMessage(progress, elapsed, status, stream);

    // 发送更新
    try {
      stream.feishuUpdater(stream.messageId, message);
      this.emit('update', { taskId, progress, elapsed, status });
      return true;
    } catch (error) {
      console.error(`[StreamingProgress] 更新失败: ${taskId}`, error.message);
      return false;
    }
  }

  /**
   * 构建进度消息
   */
  buildProgressMessage(progress, elapsed, status, stream) {
    const emoji = progress < 30 ? '⏳' : progress < 70 ? '🔧' : '🔍';
    const elapsedStr = this.formatTime(elapsed);
    
    // 估算剩余时间
    const remaining = progress > 0 
      ? Math.floor((elapsed / progress) * (100 - progress))
      : stream.estimatedDuration;
    const remainingStr = this.formatTime(remaining);

    // 进度条
    const filled = Math.floor(progress / 10);
    const empty = 10 - filled;
    const bar = '█'.repeat(filled) + '░'.repeat(empty);

    return {
      msg_type: 'text',
      content: {
        text: `${emoji} **${stream.branch}任务执行中... ${progress}%**\n\n` +
              `${bar}\n\n` +
              `📊 ${status}\n` +
              `⏱️ 已用时: ${elapsedStr} | 预计剩余: ${remainingStr}`
      }
    };
  }

  /**
   * 格式化时间
   */
  formatTime(seconds) {
    if (seconds < 60) return `${seconds}秒`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  }

  /**
   * 完成任务
   */
  complete(taskId, result = null, error = null) {
    const stream = this.activeStreams.get(taskId);
    if (!stream) return false;

    // 停止定时器
    if (stream.intervalId) {
      clearInterval(stream.intervalId);
    }

    stream.status = error ? 'failed' : 'completed';
    const elapsed = Math.floor((Date.now() - stream.startTime) / 1000);

    // 发送最终消息
    const message = error 
      ? this.buildErrorMessage(error, elapsed, stream)
      : this.buildCompleteMessage(result, elapsed, stream);

    try {
      stream.feishuUpdater(stream.messageId, message);
      this.emit(stream.status, { taskId, elapsed, result, error });
    } catch (e) {
      console.error(`[StreamingProgress] 发送完成消息失败: ${taskId}`, e.message);
    }

    // 清理
    this.activeStreams.delete(taskId);
    
    return true;
  }

  /**
   * 构建完成消息
   */
  buildCompleteMessage(result, elapsed, stream) {
    const resultText = result 
      ? (typeof result === 'string' ? result : JSON.stringify(result)).substring(0, 200)
      : '执行完成';

    return {
      msg_type: 'interactive',
      card: {
        config: { wide_screen_mode: true },
        header: {
          title: { tag: 'plain_text', content: '✅ 任务完成' },
          template: 'green'
        },
        elements: [
          {
            tag: 'div',
            text: {
              tag: 'lark_md',
              content: `**执行策略：** ${stream.branch}\n**总耗时：** ${this.formatTime(elapsed)}\n\n**结果摘要：**\n${resultText}${resultText.length >= 200 ? '...' : ''}`
            }
          }
        ]
      }
    };
  }

  /**
   * 构建错误消息
   */
  buildErrorMessage(error, elapsed, stream) {
    return {
      msg_type: 'interactive',
      card: {
        config: { wide_screen_mode: true },
        header: {
          title: { tag: 'plain_text', content: '❌ 任务失败' },
          template: 'red'
        },
        elements: [
          {
            tag: 'div',
            text: {
              tag: 'lark_md',
              content: `**执行策略：** ${stream.branch}\n**已用时：** ${this.formatTime(elapsed)}\n**失败原因：** ${error.message || error}\n\n建议：检查任务内容或稍后重试`
            }
          }
        ]
      }
    };
  }

  /**
   * 取消任务
   */
  cancel(taskId, reason = '用户取消') {
    const stream = this.activeStreams.get(taskId);
    if (!stream) return false;

    if (stream.intervalId) {
      clearInterval(stream.intervalId);
    }

    stream.status = 'cancelled';
    const elapsed = Math.floor((Date.now() - stream.startTime) / 1000);

    const message = {
      msg_type: 'text',
      content: {
        text: `⛔ **任务已取消**\n\n原因：${reason}\n已用时：${this.formatTime(elapsed)}`
      }
    };

    try {
      stream.feishuUpdater(stream.messageId, message);
      this.emit('cancelled', { taskId, reason, elapsed });
    } catch (e) {
      console.error(`[StreamingProgress] 发送取消消息失败: ${taskId}`, e.message);
    }

    this.activeStreams.delete(taskId);
    return true;
  }

  /**
   * 获取所有活跃流
   */
  getActiveStreams() {
    return Array.from(this.activeStreams.entries()).map(([id, stream]) => ({
      taskId: id,
      branch: stream.branch,
      progress: stream.lastProgress,
      elapsed: Math.floor((Date.now() - stream.startTime) / 1000),
      status: stream.status
    }));
  }

  /**
   * 停止所有流
   */
  stopAll() {
    for (const [taskId, stream] of this.activeStreams) {
      if (stream.intervalId) {
        clearInterval(stream.intervalId);
      }
    }
    this.activeStreams.clear();
    this.emit('stopped-all');
  }
}

module.exports = {
  StreamingProgress
};
