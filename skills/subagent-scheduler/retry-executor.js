/**
 * 重试执行器
 * 带指数退避的失败重试机制
 */

const EventEmitter = require('events');

/**
 * 重试执行器 - Phase 2增强版
 * 带指数退避 + 分级失败恢复机制
 */
class RetryExecutor extends EventEmitter {
  constructor(options = {}) {
    super();
    this.maxRetries = options.maxRetries || 5;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.retryableErrors = options.retryableErrors || [
      'TIMEOUT', 'NETWORK', 'RATE_LIMIT', 'RESOURCE'
    ];
    
    // Phase 2: 分级失败恢复配置
    this.enableDowngrade = options.enableDowngrade !== false;
    this.enableCheckpoint = options.enableCheckpoint !== false;
    this.downgradeChain = options.downgradeChain || {
      'Deep': 'Standard',
      'Orchestrator': 'Standard',
      'Batch': 'Standard',
      'Standard': 'Simple'
    };
    this.checkpoints = new Map();
  }

  /**
   * 执行函数，带重试
   * @param {Function} fn - 要执行的函数
   * @param {Object} context - 执行上下文
   * @returns {Promise} 执行结果
   */
  async execute(fn, context = {}) {
    let lastError = null;
    let attempt = 0;
    
    while (attempt <= this.maxRetries) {
      try {
        this.emit('attempt', { attempt, context });
        
        const result = await fn();
        
        if (attempt > 0) {
          this.emit('recovered', { attempt, context, result });
        }
        
        return {
          success: true,
          result,
          attempts: attempt + 1
        };
        
      } catch (error) {
        attempt++;
        lastError = error;
        
        const errorType = this.classifyError(error);
        
        // 不可重试的错误直接抛出
        if (!this.isRetryable(errorType)) {
          this.emit('failed', { 
            attempt, 
            error, 
            errorType, 
            context,
            reason: '不可重试的错误类型'
          });
          
          return {
            success: false,
            error,
            errorType,
            attempts: attempt,
            reason: '不可重试的错误'
          };
        }
        
        // 最后一次尝试失败
        if (attempt > this.maxRetries) {
          this.emit('exhausted', { 
            attempts: attempt, 
            error, 
            errorType, 
            context 
          });
          
          return {
            success: false,
            error,
            errorType,
            attempts: attempt,
            reason: '重试次数耗尽'
          };
        }
        
        // 计算退避延迟
        const delay = this.calculateBackoff(attempt, errorType);
        
        this.emit('retry', { 
          attempt, 
          error, 
          errorType, 
          delay, 
          context 
        });
        
        // 等待后退避
        await this.sleep(delay);
      }
    }
    
    return {
      success: false,
      error: lastError,
      attempts: attempt,
      reason: '未知错误'
    };
  }

  /**
   * 分类错误类型
   */
  classifyError(error) {
    const message = error.message || String(error);
    
    if (/timeout|timed out/i.test(message)) return 'TIMEOUT';
    if (/network|connection|ECONNREFUSED|ETIMEDOUT/i.test(message)) return 'NETWORK';
    if (/rate.limit|too many|429/i.test(message)) return 'RATE_LIMIT';
    if (/memory|out of memory|oom/i.test(message)) return 'RESOURCE';
    if (/permission|unauthorized|403/i.test(message)) return 'PERMISSION';
    if (/not found|404/i.test(message)) return 'NOT_FOUND';
    if (/invalid|bad request|400/i.test(message)) return 'INVALID_INPUT';
    if (/quota|limit exceeded/i.test(message)) return 'QUOTA';
    
    return 'UNKNOWN';
  }

  /**
   * 判断是否可重试
   */
  isRetryable(errorType) {
    return this.retryableErrors.includes(errorType);
  }

  /**
   * 计算退避延迟
   */
  calculateBackoff(attempt, errorType) {
    // 指数退避：2^attempt * baseDelay
    let delay = Math.min(
      this.baseDelay * Math.pow(2, attempt - 1),
      this.maxDelay
    );
    
    // 针对不同错误类型的调整
    const multipliers = {
      'RATE_LIMIT': 2.0,  // 限流时等待更久
      'TIMEOUT': 1.5,
      'NETWORK': 1.0,
      'RESOURCE': 1.2
    };
    
    delay *= multipliers[errorType] || 1.0;
    
    // 添加随机抖动（防止惊群）
    const jitter = Math.random() * 0.3 * delay;
    delay += jitter;
    
    return Math.floor(delay);
  }

  /**
   * 休眠
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 创建子代理执行包装器
   * 适配subagent-adapter使用
   */
  createSubagentWrapper(executor) {
    return async (config) => {
      return this.execute(async () => {
        return await executor.spawn(config);
      }, { task: config.task, branch: config.branch });
    };
  }

  // ========== Phase 2: 分级失败恢复 ==========

  /**
   * 分级错误处理
   * 根据错误类型选择不同的恢复策略
   */
  async handleErrorByType(error, errorType, context, fn) {
    switch (errorType) {
      case 'TRANSIENT':
      case 'TIMEOUT':
      case 'NETWORK':
        // 瞬时错误：指数退避重试
        return await this.retryWithBackoff(fn, context);
        
      case 'RESOURCE':
        // 资源错误：降级策略
        if (this.enableDowngrade && context.branch) {
          return await this.downgradeAndRetry(fn, context);
        }
        break;
        
      case 'RATE_LIMIT':
        // 限流错误：延长退避时间
        return await this.retryWithBackoff(fn, context, { multiplier: 3.0 });
        
      case 'LOGIC':
      case 'INVALID_INPUT':
        // 逻辑错误：不重试，直接失败
        return {
          success: false,
          error,
          errorType,
          reason: '逻辑错误，无法通过重试恢复'
        };
        
      default:
        // 未知错误：尝试重试
        return await this.retryWithBackoff(fn, context);
    }
  }

  /**
   * 策略降级
   * Deep -> Standard -> Simple
   */
  async downgradeAndRetry(fn, context) {
    const currentBranch = context.branch;
    const downgradeTo = this.downgradeChain[currentBranch];
    
    if (!downgradeTo) {
      return {
        success: false,
        error: new Error(`无法降级分支: ${currentBranch}`),
        reason: '已到最低策略级别'
      };
    }
    
    this.emit('downgrade', {
      from: currentBranch,
      to: downgradeTo,
      context
    });
    
    // 更新上下文为降级后的策略
    const downgradedContext = {
      ...context,
      branch: downgradeTo,
      downgraded: true,
      originalBranch: currentBranch
    };
    
    try {
      const result = await fn(downgradedContext);
      return {
        success: true,
        result,
        downgraded: true,
        from: currentBranch,
        to: downgradeTo
      };
    } catch (error) {
      // 降级后仍失败，继续降级
      if (this.downgradeChain[downgradeTo]) {
        return await this.downgradeAndRetry(fn, downgradedContext);
      }
      throw error;
    }
  }

  /**
   * 带退避的重试
   */
  async retryWithBackoff(fn, context, options = {}) {
    const maxRetries = options.maxRetries || this.maxRetries;
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const delay = this.calculateBackoff(attempt, context.lastErrorType) * (options.multiplier || 1);
        await this.sleep(delay);
        
        this.emit('retry', { attempt, delay, context });
        
        const result = await fn(context);
        return { success: true, result, attempts: attempt };
      } catch (error) {
        lastError = error;
        context.lastErrorType = this.classifyError(error);
        
        if (attempt === maxRetries) {
          break;
        }
      }
    }
    
    return {
      success: false,
      error: lastError,
      attempts: maxRetries,
      reason: '重试次数耗尽'
    };
  }

  /**
   * 保存检查点
   */
  saveCheckpoint(taskId, data) {
    this.checkpoints.set(taskId, {
      timestamp: Date.now(),
      data,
      attempt: (this.checkpoints.get(taskId)?.attempt || 0) + 1
    });
    this.emit('checkpoint-saved', { taskId, attempt: this.checkpoints.get(taskId).attempt });
  }

  /**
   * 加载检查点
   */
  loadCheckpoint(taskId) {
    const checkpoint = this.checkpoints.get(taskId);
    if (checkpoint) {
      this.emit('checkpoint-loaded', { taskId, timestamp: checkpoint.timestamp });
    }
    return checkpoint;
  }

  /**
   * 从检查点恢复执行
   */
  async resumeFromCheckpoint(taskId, fn, context) {
    const checkpoint = this.loadCheckpoint(taskId);
    
    if (!checkpoint) {
      return { success: false, reason: '无检查点可恢复' };
    }
    
    this.emit('resuming', { taskId, checkpoint });
    
    try {
      const result = await fn({
        ...context,
        checkpoint: checkpoint.data,
        resumed: true
      });
      
      // 成功后清理检查点
      this.checkpoints.delete(taskId);
      
      return {
        success: true,
        result,
        resumed: true,
        attempts: checkpoint.attempt
      };
    } catch (error) {
      return {
        success: false,
        error,
        resumed: true,
        reason: '从检查点恢复失败'
      };
    }
  }

  /**
   * 清理检查点
   */
  clearCheckpoint(taskId) {
    this.checkpoints.delete(taskId);
  }
}

// 预设配置
RetryExecutor.PRESETS = {
  // 网络请求
  network: {
    maxRetries: 5,
    baseDelay: 1000,
    retryableErrors: ['TIMEOUT', 'NETWORK', 'RATE_LIMIT']
  },
  
  // 子代理任务
  subagent: {
    maxRetries: 3,
    baseDelay: 2000,
    maxDelay: 60000,
    retryableErrors: ['TIMEOUT', 'NETWORK', 'RESOURCE'],
    enableDowngrade: true,
    enableCheckpoint: true
  },
  
  // 数据库操作
  database: {
    maxRetries: 3,
    baseDelay: 500,
    retryableErrors: ['NETWORK', 'TIMEOUT']
  }
};

module.exports = {
  RetryExecutor
};
