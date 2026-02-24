/**
 * Agent Router
 * Agent 路由中心 - 负责子任务分配给合适的 Agent
 */

const EventEmitter = require('events');

/**
 * 路由策略枚举
 */
const RoutingStrategy = {
  CAPABILITY_MATCH: 'capability_match',  // 能力匹配
  LOAD_BALANCE: 'load_balance',          // 负载均衡
  COST_OPTIMIZE: 'cost_optimize',        // 成本优化
  PERFORMANCE: 'performance',            // 性能优先
  ROUND_ROBIN: 'round_robin'             // 轮询
};

/**
 * Agent 路由器类
 */
class AgentRouter extends EventEmitter {
  constructor(registry, options = {}) {
    super();
    this.registry = registry;
    this.strategy = options.strategy || RoutingStrategy.CAPABILITY_MATCH;
    this.retryCount = options.retryCount || 3;
    this.fallbackEnabled = options.fallbackEnabled !== false;
    
    // 轮询计数器
    this.roundRobinIndex = 0;
    
    // 路由统计
    this.stats = {
      totalRoutes: 0,
      successfulRoutes: 0,
      failedRoutes: 0,
      retryRoutes: 0
    };
  }

  /**
   * 路由子任务到 Agent
   * @param {Object} subtask - 子任务
   * @param {Object} options - 路由选项
   * @returns {Object} 路由结果
   */
  async route(subtask, options = {}) {
    const { 
      strategy = this.strategy,
      excludeAgents = [],
      requireConfirmation = false
    } = options;
    
    this.stats.totalRoutes++;
    
    try {
      // 1. 发现候选 Agents
      const candidates = this.registry.discover({
        capabilities: subtask.requiredCapabilities || [],
        minAvailable: 1,
        excludeIds: excludeAgents,
        preferHealthy: true
      });
      
      if (candidates.length === 0) {
        // 没有可用 Agent，尝试降级或失败
        if (this.fallbackEnabled && !options.isFallback) {
          return await this.fallbackRoute(subtask, options);
        }
        throw new Error('没有可用的 Agent 处理该子任务');
      }
      
      // 2. 根据策略选择 Agent
      const selectedAgent = this.selectAgent(candidates, subtask, strategy);
      
      if (!selectedAgent) {
        throw new Error('无法选择合适的 Agent');
      }
      
      // 3. 分配任务
      this.registry.updateLoad(selectedAgent.agentId, 1);
      
      const routeResult = {
        subtaskId: subtask.id,
        agentId: selectedAgent.agentId,
        agentName: selectedAgent.name,
        strategy: strategy,
        assignedAt: Date.now(),
        estimatedDuration: subtask.estimatedDuration || 60000
      };
      
      this.emit('task-routed', routeResult);
      this.stats.successfulRoutes++;
      
      return routeResult;
      
    } catch (error) {
      this.stats.failedRoutes++;
      this.emit('route-failed', { subtask, error });
      throw error;
    }
  }

  /**
   * 根据策略选择 Agent
   */
  selectAgent(candidates, subtask, strategy) {
    switch (strategy) {
      case RoutingStrategy.CAPABILITY_MATCH:
        return this.selectByCapability(candidates, subtask);
        
      case RoutingStrategy.LOAD_BALANCE:
        return this.selectByLoadBalance(candidates);
        
      case RoutingStrategy.COST_OPTIMIZE:
        return this.selectByCost(candidates, subtask);
        
      case RoutingStrategy.PERFORMANCE:
        return this.selectByPerformance(candidates);
        
      case RoutingStrategy.ROUND_ROBIN:
        return this.selectByRoundRobin(candidates);
        
      default:
        return candidates[0];
    }
  }

  /**
   * 能力匹配选择
   */
  selectByCapability(candidates, subtask) {
    const requiredCaps = subtask.requiredCapabilities || [];
    
    // 按能力匹配度排序
    const scored = candidates.map(agent => {
      const matchedCaps = requiredCaps.filter(capability =>
        agent.capabilities.includes(capability)
      );
      const score = matchedCaps.length / requiredCaps.length;
      
      return { agent, score };
    });
    
    scored.sort((a, b) => b.score - a.score);
    
    // 返回得分最高且可用的
    return scored[0]?.agent;
  }

  /**
   * 负载均衡选择
   */
  selectByLoadBalance(candidates) {
    // 选择负载率最低的
    return candidates.reduce((best, current) => {
      const bestLoad = best.currentLoad / best.maxConcurrent;
      const currentLoad = current.currentLoad / current.maxConcurrent;
      return currentLoad < bestLoad ? current : best;
    });
  }

  /**
   * 成本优化选择
   */
  selectByCost(candidates, subtask) {
    // 简化：假设 metadata 中有 costPerToken
    return candidates.reduce((best, current) => {
      const bestCost = best.metadata?.costPerToken || 1;
      const currentCost = current.metadata?.costPerToken || 1;
      return currentCost < bestCost ? current : best;
    });
  }

  /**
   * 性能优先选择
   */
  selectByPerformance(candidates) {
    // 选择平均执行时间最短的
    return candidates.reduce((best, current) => {
      const bestTime = best.stats?.avgExecutionTime || Infinity;
      const currentTime = current.stats?.avgExecutionTime || Infinity;
      return currentTime < bestTime ? current : best;
    });
  }

  /**
   * 轮询选择
   */
  selectByRoundRobin(candidates) {
    const index = this.roundRobinIndex % candidates.length;
    this.roundRobinIndex++;
    return candidates[index];
  }

  /**
   * 降级路由
   */
  async fallbackRoute(subtask, options) {
    console.log(`[AgentRouter] 尝试降级路由: ${subtask.id}`);
    
    // 1. 尝试降低要求
    const relaxedSubtask = {
      ...subtask,
      requiredCapabilities: subtask.requiredCapabilities?.slice(0, 1) || ['read']
    };
    
    try {
      return await this.route(relaxedSubtask, {
        ...options,
        strategy: RoutingStrategy.LOAD_BALANCE,
        excludeAgents: [],
        isFallback: true  // 标记为降级路由，避免无限递归
      });
    } catch (error) {
      // 2. 如果还失败，使用默认 Agent
      const defaultAgent = this.registry.getAllAgents()[0];
      if (defaultAgent) {
        console.log(`[AgentRouter] 使用默认 Agent: ${defaultAgent.name}`);
        
        this.registry.updateLoad(defaultAgent.agentId, 1);
        
        return {
          subtaskId: subtask.id,
          agentId: defaultAgent.agentId,
          agentName: defaultAgent.name,
          strategy: 'fallback_default',
          isFallback: true,
          assignedAt: Date.now()
        };
      }
      
      throw new Error('降级路由也失败，没有可用 Agent');
    }
  }

  /**
   * 重路由失败的子任务
   * @param {Object} failedRoute 
   * @returns {Object} 新的路由
   */
  async reRoute(failedRoute) {
    const { subtaskId, agentId } = failedRoute;
    
    // 释放原 Agent 负载
    this.registry.updateLoad(agentId, -1);
    
    // 更新统计
    this.stats.retryRoutes++;
    
    // 重新路由
    const subtask = failedRoute.subtask;
    
    return await this.route(subtask, {
      excludeAgents: [agentId],
      strategy: RoutingStrategy.LOAD_BALANCE
    });
  }

  /**
   * 批量路由
   * @param {Array} subtasks 
   * @param {Object} options 
   * @returns {Array} 路由结果
   */
  async routeBatch(subtasks, options = {}) {
    const routes = [];
    
    for (const subtask of subtasks) {
      try {
        const route = await this.route(subtask, options);
        routes.push({ success: true, ...route });
      } catch (error) {
        routes.push({ 
          success: false, 
          subtaskId: subtask.id, 
          error: error.message 
        });
      }
    }
    
    return routes;
  }

  /**
   * 路由 DAG 的所有子任务
   * @param {Object} dag 
   * @returns {Map} subtaskId -> route
   */
  async routeDAG(dag) {
    const routes = new Map();
    const completed = new Set();
    const pending = new Set(dag.subtasks.map(s => s.id));
    
    while (pending.size > 0) {
      // 获取可执行的子任务
      const executable = dag.subtasks.filter(st => {
        if (completed.has(st.id) || routes.has(st.id)) return false;
        return st.dependsOn.every(depId => completed.has(depId));
      });
      
      if (executable.length === 0 && pending.size > 0) {
        throw new Error('DAG 执行死锁，无法继续');
      }
      
      // 并行路由所有可执行任务
      const routePromises = executable.map(async subtask => {
        try {
          const route = await this.route(subtask);
          routes.set(subtask.id, route);
          pending.delete(subtask.id);
          return { success: true, subtaskId: subtask.id };
        } catch (error) {
          return { 
            success: false, 
            subtaskId: subtask.id, 
            error: error.message 
          };
        }
      });
      
      await Promise.all(routePromises);
      
      // 标记已完成（实际执行由调用方处理）
      // 这里只是路由分配，所以不做 completed 标记
    }
    
    return routes;
  }

  /**
   * 获取路由统计
   */
  getStats() {
    return {
      ...this.stats,
      successRate: this.stats.totalRoutes > 0 
        ? (this.stats.successfulRoutes / this.stats.totalRoutes * 100).toFixed(2)
        : 0
    };
  }

  /**
   * 设置路由策略
   */
  setStrategy(strategy) {
    if (!Object.values(RoutingStrategy).includes(strategy)) {
      throw new Error(`未知的路由策略: ${strategy}`);
    }
    this.strategy = strategy;
  }
}

module.exports = {
  AgentRouter,
  RoutingStrategy
};
