/**
 * 自动路由中间件
 * 检测任务复杂度并自动路由到调度器
 */

const { SubagentScheduler } = require('./index');

/**
 * 任务复杂度分析器
 */
class TaskComplexityAnalyzer {
  constructor() {
    // 复杂度阈值
    this.thresholds = {
      simple: {
        maxLength: 100,
        maxTools: 2,
        keywords: ['简单', '快速', '查询', '查看']
      },
      complex: {
        minLength: 200,
        minTools: 3,
        keywords: ['分析', '优化', '重构', '完整', '详细', '深度', '复杂', '批量', '所有']
      }
    };
  }

  /**
   * 分析任务复杂度
   */
  analyze(task) {
    const text = typeof task === 'string' ? task : task.text || '';
    const length = text.length;
    
    // 计算复杂度分数
    let complexityScore = 0;
    
    // 基于长度
    if (length < this.thresholds.simple.maxLength) {
      complexityScore += 10;
    } else if (length > this.thresholds.complex.minLength) {
      complexityScore += 50;
    } else {
      complexityScore += 30;
    }
    
    // 基于关键词
    const hasSimpleKeywords = this.thresholds.simple.keywords.some(k => text.includes(k));
    const hasComplexKeywords = this.thresholds.complex.keywords.some(k => text.includes(k));
    
    if (hasSimpleKeywords) complexityScore -= 15;
    if (hasComplexKeywords) complexityScore += 30;
    
    // 基于工具调用预估
    const estimatedTools = this.estimateTools(text);
    complexityScore += estimatedTools * 10;
    
    // 判断复杂度等级
    let level = 'simple';
    if (complexityScore >= 60) {
      level = 'complex';
    } else if (complexityScore >= 30) {
      level = 'medium';
    }
    
    return {
      score: complexityScore,
      level,
      estimatedTools,
      estimatedTime: this.estimateTime(level, estimatedTools),
      shouldUseScheduler: level === 'complex' || level === 'medium',
      suggestedBranch: this.suggestBranch(level)
    };
  }
  
  /**
   * 预估工具调用数量
   */
  estimateTools(text) {
    let count = 1;
    
    // 文件操作
    if (/文件|代码|读取|写入|修改/.test(text)) count += 1;
    
    // 网络请求
    if (/查询|获取|下载|API|数据/.test(text)) count += 1;
    
    // 分析操作
    if (/分析|统计|计算|比较/.test(text)) count += 1;
    
    // 多步骤
    if (/然后|接着|最后|第一步|第二步/.test(text)) count += 2;
    
    // 批量操作
    if (/所有|批量|多个|列表/.test(text)) count += 2;
    
    return Math.min(count, 10);
  }
  
  /**
   * 预估执行时间
   */
  estimateTime(level, tools) {
    const baseTime = {
      simple: 10,
      medium: 60,
      complex: 180
    };
    
    return baseTime[level] + tools * 15;
  }
  
  /**
   * 建议分支
   */
  suggestBranch(level) {
    const branchMap = {
      simple: 'Simple',
      medium: 'Standard',
      complex: 'Deep'
    };
    return branchMap[level];
  }
}

/**
 * 自动路由器
 */
class AutoRouter {
  constructor(options = {}) {
    this.analyzer = new TaskComplexityAnalyzer();
    this.scheduler = null;
    this.enabled = options.enabled !== false;
    this.confirmThreshold = options.confirmThreshold || 'medium'; // simple/medium/complex
    this.chatId = options.chatId || null;
  }
  
  /**
   * 初始化调度器
   */
  async init() {
    if (!this.scheduler) {
      this.scheduler = new SubagentScheduler();
      await this.scheduler.init({
        autoStartLearning: false
      });
    }
  }
  
  /**
   * 处理任务
   */
  async handle(task, options = {}) {
    if (!this.enabled) {
      return { useScheduler: false, reason: 'auto_router_disabled' };
    }
    
    // 分析复杂度
    const analysis = this.analyzer.analyze(task);
    
    // 如果复杂度低于阈值，直接返回不调度
    if (analysis.level === 'simple' && this.confirmThreshold !== 'simple') {
      return {
        useScheduler: false,
        analysis,
        reason: 'task_too_simple'
      };
    }
    
    // 初始化调度器
    await this.init();
    
    // 获取chatId
    const chatId = options.chatId || this.chatId;
    
    if (!chatId) {
      console.warn('[AutoRouter] 未配置chatId，跳过确认');
      return {
        useScheduler: true,
        analysis,
        reason: 'no_chat_id_for_confirmation'
      };
    }
    
    // 通过调度器执行
    console.log(`[AutoRouter] 复杂任务检测，使用调度器执行 (${analysis.suggestedBranch})`);
    
    const result = await this.scheduler.execute({
      task: typeof task === 'string' ? task : task.text,
      chatId: chatId,
      forceBranch: options.forceBranch || analysis.suggestedBranch
    });
    
    return {
      useScheduler: true,
      analysis,
      result
    };
  }
  
  /**
   * 快速检查是否需要调度
   */
  shouldRoute(task) {
    const analysis = this.analyzer.analyze(task);
    return analysis.shouldUseScheduler;
  }
  
  /**
   * 关闭资源
   */
  async close() {
    if (this.scheduler) {
      await this.scheduler.close();
      this.scheduler = null;
    }
  }
}

/**
 * 创建自动路由处理器
 */
function createAutoRouter(options = {}) {
  return new AutoRouter(options);
}

module.exports = {
  TaskComplexityAnalyzer,
  AutoRouter,
  createAutoRouter
};
