/**
 * 子代理调度器主入口 - 完整版
 * 整合所有模块：SQLite、Redis、Cron、成本监控、重试机制
 */

const EventEmitter = require('events');
const scheduler = require('./scheduler');
const database = require('./database');
const feishu = require('./feishu');
const { FeishuCallbackHandler } = require('./feishu-callback');
const { getCronManager } = require('./cron-manager');
const { CostMonitor } = require('./cost-monitor');
const { RetryExecutor } = require('./retry-executor');
const { StreamingProgress } = require('./streaming-progress');
const { LLMClassifier } = require('./llm-classifier');
const { ProbeExecutor } = require('./probe-executor');
const { LayeredContext } = require('./layered-context');
const { PolicyManager } = require('./policy-manager');
const { TracingManager } = require('./tracing-manager');
const { LearningEngine } = require('./learning-engine');
const { AgentRegistry } = require('./agent-registry');
const { TaskDecomposer } = require('./task-decomposer');
const { AgentRouter, RoutingStrategy } = require('./agent-router');
const { ResultAggregator, AggregationStrategy } = require('./result-aggregator');
const { CollaborationHub } = require('./collaboration-hub');
const { ExecutionMonitor } = require('./execution-monitor');
const config = require('./config.json');

// 可选模块（需要外部依赖）
let RedisController = null;
let SubagentAdapter = null;

try {
  const redisModule = require('./redis-concurrency');
  RedisController = redisModule.RedisConcurrencyController;
} catch (e) {
  console.log('[Scheduler] Redis模块未加载');
}

try {
  SubagentAdapter = require('./subagent-adapter');
} catch (e) {
  console.log('[Scheduler] 子代理适配器未加载');
}

/**
 * 子代理调度器类 - Phase 2增强版
 */
class SubagentScheduler extends EventEmitter {
  constructor(options = {}) {
    super(); // 初始化EventEmitter
    
    this.db = database;
    this.cronManager = getCronManager();
    this.costMonitor = new CostMonitor(this.db, options.budget);
    this.retryExecutor = new RetryExecutor({
      ...options.retry,
      enableDowngrade: config.phase2?.resilience?.enableDowngrade !== false,
      enableCheckpoint: config.phase2?.resilience?.enableCheckpoint !== false,
      downgradeChain: config.phase2?.resilience?.downgradeChain
    });
    this.feishuCallback = new FeishuCallbackHandler(feishu);
    this.concurrencyController = null;
    
    // Phase 2: 流式进度
    this.streamingProgress = new StreamingProgress(
      config.phase2?.streamingProgress || {}
    );
    
    // Phase 2: LLM分类器
    this.llmClassifier = new LLMClassifier(
      config.phase2?.llmClassifier || {}
    );
    
    // Phase 4: 学习引擎
    this.learningEngine = new LearningEngine(this.db, {
      outputDir: './learning-reports',
      minSamples: config.phase4?.learning?.minSamples || 5
    });
    
    // Multi-Agent: 多 agents 协作组件
    this.agentRegistry = new AgentRegistry(options.agentRegistry || {});
    this.taskDecomposer = new TaskDecomposer(options.taskDecomposer || {});
    this.agentRouter = new AgentRouter(this.agentRegistry, options.agentRouter || {});
    this.resultAggregator = new ResultAggregator(options.resultAggregator || {});
    
    // Multi-Agent: 协作中心和执行监控
    this.collaborationHub = new CollaborationHub(options.collaborationHub || {});
    this.executionMonitor = new ExecutionMonitor(options.executionMonitor || {});
    
    // 设置默认本地 agents
    this.setupDefaultAgents();
    
    // 初始化并发控制
    this.initConcurrency(options.redis);
    
    // 设置事件监听
    this.setupEventListeners();
  }

  /**
   * 初始化并发控制
   */
  async initConcurrency(redisConfig) {
    if (RedisController && redisConfig) {
      try {
        this.concurrencyController = new RedisController(redisConfig);
        console.log('[Scheduler] Redis并发控制已启用');
      } catch (e) {
        console.log('[Scheduler] Redis连接失败，使用本地并发控制');
      }
    }
    
    if (!this.concurrencyController) {
      const { LocalConcurrencyController } = require('./redis-concurrency');
      this.concurrencyController = new LocalConcurrencyController();
      console.log('[Scheduler] 本地并发控制已启用');
    }
  }

  /**
   * 初始化
   * @param {Object} options - 初始化选项
   * @param {string} options.chatId - 飞书聊天ID（用于推送报告）
   * @param {boolean} options.autoStartLearning - 是否自动启动学习定时任务
   */
  async init(options = {}) {
    this.db.initDatabase();
    console.log('[Scheduler] 初始化完成');
    
    // 自动启动定时任务（如果配置了chatId或明确设置autoStartLearning）
    if (options.chatId || options.autoStartLearning) {
      const chatId = options.chatId || config.feishu?.defaultChatId;
      if (chatId) {
        console.log('[Scheduler] 自动启动每日学习定时任务...');
        this.startDailyLearning(chatId);
      }
    }
    
    return this;
  }

  /**
   * 设置默认本地 Agents
   */
  setupDefaultAgents() {
    // 简单 Agent - 处理快速任务
    this.agentRegistry.createLocalAgent('SimpleAgent', {
      capabilities: ['read', 'write', 'simple_analysis'],
      maxConcurrent: 5,
      metadata: { type: 'simple', costLevel: 'low' }
    });
    
    // 标准 Agent - 处理常规任务
    this.agentRegistry.createLocalAgent('StandardAgent', {
      capabilities: ['read', 'write', 'analyze', 'search'],
      maxConcurrent: 3,
      metadata: { type: 'standard', costLevel: 'medium' }
    });
    
    // 深度 Agent - 处理复杂任务
    this.agentRegistry.createLocalAgent('DeepAgent', {
      capabilities: ['read', 'write', 'analyze', 'deep_research', 'reasoning'],
      maxConcurrent: 1,
      metadata: { type: 'deep', costLevel: 'high' }
    });
    
    console.log('[Scheduler] 默认 Agents 已创建');
  }

  /**
   * 判断是否需要使用多 Agent
   */
  async shouldUseMultiAgent(task) {
    const analysis = this.taskDecomposer.analyzeComplexity(task);
    return analysis.shouldDecompose && analysis.estimatedSubtasks > 2;
  }

  /**
   * 执行多 Agent 协作任务
   */
  async executeMultiAgent(task, options = {}) {
    const startTime = Date.now();
    const taskId = `multi_${Date.now()}`;
    
    console.log(`[MultiAgent] 开始执行多 Agent 任务: ${taskId}`);
    this.emit('multiagent-started', { taskId, task: task.substring(0, 100) });
    
    try {
      // 1. 分解任务
      const dag = await this.taskDecomposer.decompose(task, options.decompose);
      console.log(`[MultiAgent] 任务分解完成: ${dag.totalSubtasks} 个子任务`);
      
      // 2. 路由所有子任务
      const routes = await this.routeSubtasks(dag);
      console.log(`[MultiAgent] 子任务路由完成: ${routes.size} 个路由`);
      
      // 3. 执行 DAG
      const results = await this.executeDAG(dag, routes, options);
      console.log(`[MultiAgent] DAG 执行完成: ${results.size} 个结果`);
      
      // 4. 聚合结果
      const aggregated = await this.resultAggregator.aggregateByDAG(dag, results);
      console.log(`[MultiAgent] 结果聚合完成`);
      
      const duration = Date.now() - startTime;
      
      this.emit('multiagent-completed', { taskId, duration });
      
      return {
        success: true,
        taskId,
        strategy: 'multi_agent',
        subtaskCount: dag.totalSubtasks,
        result: aggregated.result,
        duration,
        dag: {
          parallelGroups: dag.parallelGroups.length,
          totalSubtasks: dag.totalSubtasks
        }
      };
      
    } catch (error) {
      this.emit('multiagent-error', { taskId, error });
      throw error;
    }
  }

  /**
   * 路由子任务
   */
  async routeSubtasks(dag) {
    const routes = new Map();
    const completed = new Set();
    
    for (const group of dag.parallelGroups) {
      // 获取当前组可执行的子任务
      const executable = dag.subtasks.filter(st => {
        if (routes.has(st.id)) return false;
        return st.dependsOn.every(depId => completed.has(depId));
      });
      
      // 并行路由
      const routePromises = executable.map(async subtask => {
        try {
          const route = await this.agentRouter.route(subtask, {
            strategy: RoutingStrategy.CAPABILITY_MATCH
          });
          routes.set(subtask.id, { ...route, subtask });
          return { success: true, subtaskId: subtask.id };
        } catch (error) {
          console.error(`[MultiAgent] 路由失败: ${subtask.id}`, error.message);
          return { success: false, subtaskId: subtask.id, error };
        }
      });
      
      await Promise.all(routePromises);
      
      // 标记为已完成（路由阶段）
      executable.forEach(st => completed.add(st.id));
    }
    
    return routes;
  }

  /**
   * 执行 DAG
   */
  async executeDAG(dag, routes, options = {}) {
    const results = new Map();
    const completed = new Set();
    
    for (const group of dag.parallelGroups) {
      // 获取当前组可执行的子任务
      const executable = group.filter(id => {
        const route = routes.get(id);
        if (!route) return false;
        
        const subtask = dag.subtasks.find(st => st.id === id);
        if (!subtask) return false;
        
        return subtask.dependsOn.every(depId => completed.has(depId));
      });
      
      // 并行执行
      const executePromises = executable.map(async id => {
        const route = routes.get(id);
        const subtask = dag.subtasks.find(st => st.id === id);
        
        try {
          // 模拟执行子任务（实际应调用 agent 执行）
          const result = await this.executeSubtask(route, subtask, options);
          
          results.set(id, result);
          completed.add(id);
          
          // 更新 Agent 负载
          this.agentRegistry.updateLoad(route.agentId, -1);
          
          return { success: true, subtaskId: id };
        } catch (error) {
          console.error(`[MultiAgent] 子任务执行失败: ${id}`, error.message);
          
          // 尝试重路由
          if (options.retry !== false) {
            try {
              const newRoute = await this.agentRouter.reRoute(route);
              const result = await this.executeSubtask(newRoute, subtask, options);
              results.set(id, result);
              completed.add(id);
              return { success: true, subtaskId: id, retried: true };
            } catch (retryError) {
              return { success: false, subtaskId: id, error: retryError };
            }
          }
          
          return { success: false, subtaskId: id, error };
        }
      });
      
      await Promise.all(executePromises);
    }
    
    return results;
  }

  /**
   * 执行单个子任务
   */
  async executeSubtask(route, subtask, options) {
    // 这里应该调用实际的 agent 执行
    // 简化：使用现有的调度器执行
    
    const agent = this.agentRegistry.getAgent(route.agentId);
    
    console.log(`[MultiAgent] Agent ${agent.name} 执行子任务: ${subtask.id}`);
    
    // 根据 agent 类型选择分支
    let branch = 'Standard';
    if (agent.metadata?.type === 'simple') branch = 'Simple';
    if (agent.metadata?.type === 'deep') branch = 'Deep';
    
    // 使用现有调度器执行
    const result = await this.execute({
      task: subtask.task,
      forceBranch: branch,
      ...options
    });
    
    return {
      subtaskId: subtask.id,
      result: result.result,
      success: result.success,
      agentId: route.agentId,
      agentName: agent.name,
      duration: result.duration
    };
  }

  /**
   * 主执行函数（整合多 Agent）
   */
  async execute(taskInput, options = {}) {
    const task = typeof taskInput === 'string' ? taskInput : taskInput.task;
    
    // 判断是否使用多 Agent
    if (options.multiAgent !== false && await this.shouldUseMultiAgent(task)) {
      console.log('[Scheduler] 使用多 Agent 协作模式');
      return await this.executeMultiAgent(task, options);
    }
    
    // 使用原有的单 Agent 调度
    return await this.executeSingle(taskInput, options);
  }

  /**
   * 单 Agent 执行（原有的 execute 逻辑）
   */
  async executeSingle(taskInput, options = {}) {
    const startTime = Date.now();
    const task = typeof taskInput === 'string' ? taskInput : taskInput.task;
    const chatId = options.chatId || config.feishu.defaultChatId;
    
    try {
      // 1. 任务分类
      const classification = await scheduler.classifyTask(task, this.db);
      let branch = options.forceBranch || classification.branch;
      
      // 2. Simple分支直接执行
      if (branch === 'Simple') {
        return await this.executeSimple(task, startTime);
      }
      
      // 3. 成本估算和预算检查
      const costEstimate = this.costMonitor.estimateCost(branch, task.length);
      const budgetCheck = await this.costMonitor.checkBudget(costEstimate.total);
      
      if (!budgetCheck.allowed) {
        return {
          success: false,
          error: `预算检查失败: ${budgetCheck.reasons.join(', ')}`,
          errorType: 'BUDGET_EXCEEDED'
        };
      }
      
      // 4. 用户确认（飞书）
      if (chatId && config.confirmation.enabled) {
        const historyStats = await this.db.getHistoryStats(branch, 7);
        
        const confirmResult = await this.feishuCallback.sendTextConfirm({
          branch,
          duration: costEstimate.estimatedTime,
          cost: costEstimate.total,
          history: historyStats
        }, chatId);
        
        if (confirmResult.action === 'cancel') {
          return { success: false, error: '用户取消', errorType: 'USER_CANCELLED' };
        }
        
        if (confirmResult.action === 'downgrade') {
          branch = 'Simple';
          return await this.executeSimple(task, startTime);
        }
      }
      
      // 5. 并发控制 - 获取槽位
      const taskId = `task_${Date.now()}`;
      await this.concurrencyController.waitForSlot(branch, taskId, 30000);
      
      // 6. 构建任务配置
      const taskConfig = scheduler.buildTaskConfig(branch, task, options);
      
      // 7. 发送进度消息
      let progressMessageId = null;
      if (chatId) {
        const progressMsg = await feishu.sendMessage(
          chatId,
          feishu.buildProgressMessage(0, 0)
        );
        progressMessageId = progressMsg.message_id;
        
        // 启动进度更新定时任务
        this.cronManager.startFeishuUpdater(
          taskId,
          progressMessageId,
          async (msgId, status) => {
            await feishu.updateMessage(
              msgId,
              feishu.buildProgressMessage(status.progress, Math.floor((Date.now() - startTime) / 1000))
            );
          },
          config.monitoring.progressUpdateInterval
        );
      }
      
      // 8. 执行子代理（带重试）
      let executionResult;
      
      if (options.toolExecutor) {
        // 使用主会话传入的toolExecutor
        const adapter = SubagentAdapter?.createSubagentExecutor(options.toolExecutor);
        executionResult = await this.retryExecutor.execute(async () => {
          return await adapter.spawn(taskConfig);
        }, { task, branch });
      } else {
        // 模拟执行（实际应在主会话中执行）
        executionResult = await this.simulateExecution(taskConfig);
      }
      
      // 9. 停止进度更新
      this.cronManager.stop(taskId);
      
      // 10. 释放并发槽位
      await this.concurrencyController.releaseSlot(branch, taskId);
      
      // 11. 记录历史
      const duration = Date.now() - startTime;
      await this.db.insertTaskHistory({
        task_hash: scheduler.hashTask(task),
        task_preview: task.substring(0, 100),
        branch,
        duration_ms: duration,
        estimated_cost: costEstimate.total,
        actual_cost: executionResult.success ? costEstimate.total : 0,
        success: executionResult.success ? 1 : 0,
        retry_count: executionResult.attempts || 0,
        error_message: executionResult.error?.message
      });
      
      // 12. 发送完成消息
      if (chatId && progressMessageId) {
        await feishu.updateMessage(
          progressMessageId,
          feishu.buildCompleteMessage(
            executionResult.success,
            Math.floor(duration / 1000),
            costEstimate.total,
            executionResult.result,
            executionResult.error
          )
        );
      }
      
      return {
        success: executionResult.success,
        branch,
        result: executionResult.result,
        duration,
        attempts: executionResult.attempts || 1,
        error: executionResult.error
      };
      
    } catch (error) {
      // 错误处理
      const duration = Date.now() - startTime;
      const errorBranch = typeof branch !== 'undefined' ? branch : 'Unknown';
      
      await this.db.insertTaskHistory({
        task_hash: scheduler.hashTask(task),
        task_preview: task.substring(0, 100),
        branch: errorBranch,
        duration_ms: duration,
        success: 0,
        retry_count: 0,
        error_message: error.message
      });
      
      return {
        success: false,
        error,
        errorType: 'EXECUTION_ERROR',
        duration
      };
    }
  }

  /**
   * 执行Simple任务
   */
  async executeSimple(task, startTime) {
    // Simple任务直接处理，不spawn
    return {
      success: true,
      branch: 'Simple',
      result: '直接执行完成',
      duration: Date.now() - startTime
    };
  }

  /**
   * 模拟子代理执行（测试用）
   */
  async simulateExecution(config) {
    // 模拟执行时间
    const delay = config.runTimeoutSeconds > 60000 ? 5000 : 2000;
    await new Promise(r => setTimeout(r, delay));
    
    return {
      success: true,
      result: '模拟执行结果',
      attempts: 1
    };
  }

  /**
   * 生成日报
   */
  async generateDailyReport(chatId) {
    const stats = await this.costMonitor.generateReport();
    
    if (!stats || stats.length === 0) {
      await feishu.sendMessage(chatId, {
        msg_type: 'text',
        content: { text: '暂无历史数据' }
      });
      return;
    }
    
    // 构建日报
    const report = this.buildReport(stats);
    await feishu.sendMessage(chatId, feishu.buildDailyReport(report));
  }

  /**
   * 构建报告数据
   */
  buildReport(stats) {
    const today = new Date().toISOString().split('T')[0];
    const todayStats = stats.filter(s => s.date === today);
    
    return {
      date: today,
      totalTasks: todayStats.reduce((sum, s) => sum + s.count, 0),
      totalCost: todayStats.reduce((sum, s) => sum + s.total_cost, 0),
      byBranch: todayStats.reduce((obj, s) => {
        obj[s.branch] = {
          count: s.count,
          totalCost: s.total_cost,
          avgCost: s.avg_cost
        };
        return obj;
      }, {})
    };
  }

  /**
   * 获取并发状态
   */
  async getConcurrencyStatus() {
    return await this.concurrencyController.getAllStatus();
  }

  /**
   * 启动每日学习定时任务（6点分析，9点推送）
   * @param {string} chatId - 飞书聊天ID（可选）
   */
  startDailyLearning(chatId = null) {
    // 启动6点分析任务
    this.cronManager.startLearningAnalysis(this.learningEngine);
    
    // 如果有chatId，启动9点推送任务
    if (chatId) {
      const feishuSender = async (card) => {
        await feishu.sendMessage(chatId, card);
      };
      this.cronManager.startLearningReport(this.learningEngine, feishuSender);
    }
    
    return ['daily-learning-analysis', 'daily-learning-report'];
  }

  /**
   * 设置事件监听器
   * 连接协作中心和执行监控
   */
  setupEventListeners() {
    // 监听Agent注册，同步到协作中心
    this.agentRegistry.on('agent-registered', ({ agentId, agentInfo }) => {
      this.collaborationHub.registerAgent(agentId, agentInfo);
      this.executionMonitor.registerAgent(agentId, agentInfo);
    });
    
    // 监听Agent注销
    this.agentRegistry.on('agent-unregistered', ({ agentId }) => {
      this.collaborationHub.unregisterAgent(agentId);
    });
    
    // 监听任务事件，同步到执行监控
    this.on('task-started', ({ taskId, agentId }) => {
      this.executionMonitor.startTask(taskId);
      if (agentId) {
        this.executionMonitor.updateAgentLoad(agentId, 1);
      }
    });
    
    this.on('task-completed', ({ taskId, agentId }) => {
      this.executionMonitor.completeTask(taskId);
    });
    
    this.on('task-failed', ({ taskId, error, agentId }) => {
      this.executionMonitor.failTask(taskId, error);
    });
    
    // 监听进度更新
    this.on('progress-updated', ({ taskId, progress }) => {
      this.executionMonitor.updateProgress(taskId, progress);
      this.collaborationHub.reportProgress('system', taskId, progress);
    });
  }

  /**
   * 获取协作中心实例
   */
  getCollaborationHub() {
    return this.collaborationHub;
  }

  /**
   * 获取执行监控实例
   */
  getExecutionMonitor() {
    return this.executionMonitor;
  }

  /**
   * 获取监控仪表板数据
   */
  getDashboard() {
    return this.executionMonitor.getDashboard();
  }

  /**
   * 手动发送学习报告
   * @param {string} chatId - 飞书聊天ID
   * @param {string} date - 报告日期，null表示最新
   */
  async sendLearningReport(chatId, date = null) {
    const feishuSender = async (card) => {
      await feishu.sendMessage(chatId, card);
    };
    return await this.learningEngine.sendReport(date, feishuSender);
  }

  /**
   * 手动执行学习（用于测试）
   */
  async runLearningNow() {
    return await this.learningEngine.dailyLearning();
  }

  /**
   * 获取最新学习报告
   */
  getLatestLearningReport() {
    return this.learningEngine.getLatestReport();
  }

  /**
   * 关闭资源
   */
  async close() {
    this.cronManager.stopAll();
    
    if (this.concurrencyController) {
      await this.concurrencyController.close();
    }
    
    if (this.collaborationHub) {
      this.collaborationHub.close();
    }
    
    if (this.executionMonitor) {
      this.executionMonitor.close();
    }
    
    this.removeAllListeners();
  }
}

// 兼容旧版API
async function init() {
  const scheduler = new SubagentScheduler();
  return scheduler.init();
}

async function executeWithConfirm(taskInput, options = {}) {
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  return scheduler.execute(taskInput, options);
}

module.exports = {
  SubagentScheduler,
  init,
  executeWithConfirm,
  generateDailyReport: async (chatId) => {
    const scheduler = new SubagentScheduler();
    await scheduler.init();
    return scheduler.generateDailyReport(chatId);
  },
  // 多 Agents 模块
  AgentRegistry,
  TaskDecomposer,
  AgentRouter,
  RoutingStrategy,
  ResultAggregator,
  AggregationStrategy,
  // 新增模块
  CollaborationHub,
  ExecutionMonitor,
  // 自动路由模块
  AutoRouter: require('./auto-router').AutoRouter,
  TaskComplexityAnalyzer: require('./auto-router').TaskComplexityAnalyzer,
  createAutoRouter: require('./auto-router').createAutoRouter,
  // 指令队列模块
  CommandQueue: require('./command-queue').CommandQueue,
  TaskStatus: require('./command-queue').TaskStatus,
  createFeishuCommandQueue: require('./feishu-queue').createFeishuCommandQueue,
  // 飞书消息处理器
  createFeishuMessageHandler: require('./feishu-message-handler').createFeishuMessageHandler,
  getMessageHandler: require('./feishu-message-handler').getMessageHandler,
  // 子模块
  scheduler,
  database,
  feishu,
  getCronManager,
  CostMonitor,
  RetryExecutor,
  FeishuCallbackHandler
};
