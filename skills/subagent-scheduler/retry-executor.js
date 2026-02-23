/**
 * 重试执行器
 * 带指数退避的失败重试机制
 */

const EventEmitter = require('events');

class RetryExecutor extends EventEmitter {
  constructor(options = {}) {
    super();
    this.maxRetries = options.maxRetries || 5;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.retryableErrors = options.retryableErrors || [
      'TIMEOUT', 'NETWORK', 'RATE_LIMIT', 'RESOURCE'
    ];
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
    retryableErrors: ['TIMEOUT', 'NETWORK', 'RESOURCE']
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
