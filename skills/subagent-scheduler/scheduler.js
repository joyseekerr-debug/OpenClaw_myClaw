/**
 * 子代理调度器核心模块
 * 实现任务分类、执行、重试、成本管理
 */

const config = require('./config.json');

/**
 * 计算任务特征哈希（用于历史查询）
 */
function hashTask(task) {
  // 简化实现：取任务描述前50字 + 长度
  const preview = task.substring(0, 50).trim();
  return `${preview}_${task.length}`;
}

/**
 * 快速规则分类器
 */
function fastRules(task) {
  const length = task.length;
  const wordCount = task.split(/\s+/).length;
  const hasAttachment = task.includes('[文件]') || task.includes('[附件]');
  const hasBatchKeyword = /批量|所有|多个|列表/.test(task);
  const hasDeepKeyword = /深度|详细|全面|彻底/.test(task);
  const hasOrchestratorKeyword = /先.*然后|步骤|流程|依赖/.test(task);
  
  // Deep: 明确深度要求 (优先于Orchestrator)
  if (hasDeepKeyword && length > 100) {
    return { branch: 'Deep', confidence: 0.8, reason: '深度分析任务' };
  }
  
  // Orchestrator: 流程关键词 (避免被Simple覆盖)
  if (hasOrchestratorKeyword) {
    return { branch: 'Orchestrator', confidence: 0.7, reason: '多阶段流程任务' };
  }
  
  // Batch: 批量关键词
  if (hasBatchKeyword || task.includes('10个') || task.includes('20个')) {
    return { branch: 'Batch', confidence: 0.75, reason: '批量处理任务' };
  }
  
  // Simple: 短文本、无附件、简单查询
  if (length < 100 && !hasAttachment && wordCount < 20) {
    return { branch: 'Simple', confidence: 0.85, reason: '短文本简单任务' };
  }
  
  // 默认 Standard
  return { branch: 'Standard', confidence: 0.6, reason: '默认标准任务' };
}

/**
 * 任务分类主函数
 */
async function classifyTask(task, db = null) {
  // 1. 快速规则
  const result = fastRules(task);
  
  if (result.confidence >= 0.6) {
    return result;
  }
  
  // 2. 如果有数据库，查询历史
  if (db) {
    const similar = await db.query(
      `SELECT branch, AVG(duration_ms) as avg_duration, COUNT(*) as count
       FROM task_history 
       WHERE task_hash LIKE ? AND success = 1
       GROUP BY branch 
       ORDER BY count DESC 
       LIMIT 1`,
      [hashTask(task).substring(0, 20) + '%']
    );
    
    if (similar && similar.count >= 3) {
      return {
        branch: similar.branch,
        confidence: 0.7,
        reason: `基于${similar.count}次相似任务历史`,
        estimatedDuration: similar.avg_duration
      };
    }
  }
  
  return result;
}

/**
 * 估算任务成本
 */
function estimateCost(branch, taskLength) {
  const baseRates = {
    'Simple': { input: 0.001, output: 0.003 },
    'Standard': { input: 0.001, output: 0.003 },
    'Batch': { input: 0.001, output: 0.003 },
    'Orchestrator': { input: 0.002, output: 0.006 },
    'Deep': { input: 0.002, output: 0.006 }
  };
  
  const rate = baseRates[branch] || baseRates['Standard'];
  const estimatedInput = Math.min(taskLength * 2, 8000);
  const estimatedOutput = estimatedInput * (branch === 'Deep' ? 1.5 : 0.8);
  
  return {
    input: estimatedInput,
    output: estimatedOutput,
    total: (estimatedInput * rate.input + estimatedOutput * rate.output) / 1000
  };
}

/**
 * 估算任务耗时
 */
function estimateDuration(branch, taskLength) {
  const baseDurations = {
    'Simple': 5,
    'Standard': 45,
    'Batch': Math.min(30 + (taskLength / 100) * 10, 180),
    'Orchestrator': 120,
    'Deep': 300
  };
  
  return baseDurations[branch] || 60;
}

/**
 * 执行子代理任务（带重试）
 */
async function executeWithRetry(taskConfig, maxRetries = 5) {
  let lastError = null;
  let retryCount = 0;
  
  while (retryCount <= maxRetries) {
    try {
      // 调用子代理
      const result = await sessions_spawn(taskConfig);
      
      return {
        success: true,
        result: result,
        retryCount: retryCount
      };
    } catch (error) {
      retryCount++;
      lastError = error;
      
      // 分析错误类型
      const errorType = analyzeError(error);
      
      // 某些错误不重试
      if (errorType === 'INVALID_INPUT' || errorType === 'PERMISSION_DENIED') {
        break;
      }
      
      // 指数退避
      if (retryCount <= maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }
  
  return {
    success: false,
    error: lastError,
    errorType: analyzeError(lastError),
    retryCount: retryCount - 1
  };
}

/**
 * 分析错误类型
 */
function analyzeError(error) {
  const message = error.message || String(error);
  
  if (/timeout|timed out/i.test(message)) return 'TIMEOUT';
  if (/network|connection|ECONNREFUSED/i.test(message)) return 'NETWORK';
  if (/rate limit|too many requests/i.test(message)) return 'RATE_LIMIT';
  if (/permission|unauthorized|forbidden/i.test(message)) return 'PERMISSION_DENIED';
  if (/invalid|bad request/i.test(message)) return 'INVALID_INPUT';
  if (/memory|out of memory/i.test(message)) return 'RESOURCE';
  
  return 'UNKNOWN';
}

/**
 * 构建任务配置
 */
function buildTaskConfig(branch, task, options = {}) {
  const branchConfig = config.branches[branch];
  
  const baseConfig = {
    task: task,
    model: config.model,
    reasoning: config.reasoning,
    label: options.label || `${branch}_${Date.now()}`,
    cleanup: branchConfig.cleanup || 'delete'
  };
  
  if (branch !== 'Simple') {
    baseConfig.mode = branchConfig.mode;
    baseConfig.runTimeoutSeconds = options.timeout || branchConfig.timeout;
  }
  
  if (branch === 'Batch') {
    baseConfig.batchSize = branchConfig.batchSize;
  }
  
  if (branch === 'Deep') {
    baseConfig.thread = true;
  }
  
  return baseConfig;
}

/**
 * 主执行函数
 */
async function execute(taskInput, options = {}) {
  const startTime = Date.now();
  const task = typeof taskInput === 'string' ? taskInput : taskInput.task;
  
  try {
    // 1. 任务分类
    const classification = await classifyTask(task, options.db);
    const branch = options.forceBranch || classification.branch;
    
    // 2. Simple分支直接执行（不spawn）
    if (branch === 'Simple') {
      // 直接处理，不创建子代理
      return {
        success: true,
        branch: 'Simple',
        result: '直接执行完成',
        duration: Date.now() - startTime
      };
    }
    
    // 3. 估算成本和时间
    const costEstimate = estimateCost(branch, task.length);
    const durationEstimate = estimateDuration(branch, task.length);
    
    // 4. 检查成本上限
    if (costEstimate.total > config.costLimits.perTask) {
      return {
        success: false,
        error: `预估成本 ${costEstimate.total.toFixed(4)} USD 超过上限 ${config.costLimits.perTask} USD`,
        errorType: 'COST_LIMIT'
      };
    }
    
    // 5. 构建任务配置
    const taskConfig = buildTaskConfig(branch, task, options);
    
    // 6. 执行（带重试）
    const maxRetries = config.branches[branch].maxRetries || 5;
    const execution = await executeWithRetry(taskConfig, maxRetries);
    
    // 7. 记录历史
    const duration = Date.now() - startTime;
    if (options.db) {
      await options.db.run(
        `INSERT INTO task_history 
         (task_hash, task_preview, branch, duration_ms, estimated_cost, actual_cost, success, retry_count, error_message)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [hashTask(task), task.substring(0, 100), branch, duration, costEstimate.total, 
         costEstimate.total, execution.success ? 1 : 0, execution.retryCount || 0, 
         execution.error ? execution.error.message : null]
      );
    }
    
    return {
      success: execution.success,
      branch: branch,
      result: execution.result,
      duration: duration,
      retryCount: execution.retryCount || 0,
      error: execution.error
    };
    
  } catch (error) {
    return {
      success: false,
      error: error,
      errorType: analyzeError(error),
      duration: Date.now() - startTime
    };
  }
}

// 导出模块
module.exports = {
  classifyTask,
  estimateCost,
  estimateDuration,
  execute,
  executeWithRetry,
  buildTaskConfig,
  hashTask
};
