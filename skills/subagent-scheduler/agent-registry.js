/**
 * Agent Registry
 * Agent 注册中心 - 管理多 agents 的注册、发现和健康状况
 */

const EventEmitter = require('events');

/**
 * Agent 注册中心类
 */
class AgentRegistry extends EventEmitter {
  constructor(options = {}) {
    super();
    this.agents = new Map();
    this.heartbeatInterval = options.heartbeatInterval || 30000; // 30秒
    this.offlineThreshold = options.offlineThreshold || 90000; // 90秒无心跳视为离线
    
    // 启动健康检查
    this.startHealthCheck();
  }

  /**
   * 注册新 Agent
   * @param {Object} agentInfo - Agent 信息
   * @returns {string} agentId
   */
  register(agentInfo) {
    const agentId = agentInfo.agentId || `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const agent = {
      agentId,
      name: agentInfo.name || agentId,
      capabilities: agentInfo.capabilities || [],
      maxConcurrent: agentInfo.maxConcurrent || 1,
      currentLoad: 0,
      status: 'healthy',
      registeredAt: Date.now(),
      lastHeartbeat: Date.now(),
      metadata: agentInfo.metadata || {},
      endpoint: agentInfo.endpoint || 'local',
      stats: {
        totalTasks: 0,
        successfulTasks: 0,
        failedTasks: 0,
        avgExecutionTime: 0
      }
    };
    
    this.agents.set(agentId, agent);
    
    this.emit('agent-registered', { agentId, agent });
    console.log(`[AgentRegistry] Agent 注册成功: ${agent.name} (${agentId})`);
    
    return agentId;
  }

  /**
   * 注销 Agent
   * @param {string} agentId 
   * @returns {boolean}
   */
  unregister(agentId) {
    const agent = this.agents.get(agentId);
    if (!agent) return false;
    
    this.agents.delete(agentId);
    this.emit('agent-unregistered', { agentId, agent });
    console.log(`[AgentRegistry] Agent 注销: ${agent.name} (${agentId})`);
    
    return true;
  }

  /**
   * 更新心跳
   * @param {string} agentId 
   */
  heartbeat(agentId) {
    const agent = this.agents.get(agentId);
    if (!agent) return false;
    
    agent.lastHeartbeat = Date.now();
    
    // 如果之前是离线状态，恢复为健康
    if (agent.status === 'offline') {
      agent.status = 'healthy';
      this.emit('agent-recovered', { agentId, agent });
      console.log(`[AgentRegistry] Agent 恢复在线: ${agent.name}`);
    }
    
    return true;
  }

  /**
   * 更新 Agent 负载
   * @param {string} agentId 
   * @param {number} delta - 负载变化 (+1/-1)
   */
  updateLoad(agentId, delta) {
    const agent = this.agents.get(agentId);
    if (!agent) return false;
    
    agent.currentLoad = Math.max(0, agent.currentLoad + delta);
    
    // 更新状态
    if (agent.currentLoad >= agent.maxConcurrent) {
      agent.status = 'busy';
    } else if (agent.status === 'busy') {
      agent.status = 'healthy';
    }
    
    return true;
  }

  /**
   * 更新 Agent 统计
   * @param {string} agentId 
   * @param {Object} taskResult 
   */
  updateStats(agentId, taskResult) {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    
    agent.stats.totalTasks++;
    
    if (taskResult.success) {
      agent.stats.successfulTasks++;
    } else {
      agent.stats.failedTasks++;
    }
    
    // 更新平均执行时间
    if (taskResult.duration) {
      const oldAvg = agent.stats.avgExecutionTime;
      const count = agent.stats.totalTasks;
      agent.stats.avgExecutionTime = (oldAvg * (count - 1) + taskResult.duration) / count;
    }
  }

  /**
   * 发现匹配的 Agents
   * @param {Object} requirements - 需求条件
   * @returns {Array} 匹配的 agents
   */
  discover(requirements = {}) {
    const {
      capabilities = [], // 必需的能力
      minAvailable = 1,  // 最小可用槽位
      excludeIds = [],   // 排除的 agent
      preferHealthy = true // 优先健康状态
    } = requirements;
    
    let candidates = Array.from(this.agents.values()).filter(agent => {
      // 排除指定 agent
      if (excludeIds.includes(agent.agentId)) return false;
      
      // 检查是否离线
      if (agent.status === 'offline') return false;
      
      // 检查能力匹配
      if (capabilities.length > 0) {
        const hasAllCapabilities = capabilities.every(capability =>
          agent.capabilities.includes(capability)
        );
        if (!hasAllCapabilities) return false;
      }
      
      // 检查可用槽位
      const availableSlots = agent.maxConcurrent - agent.currentLoad;
      if (availableSlots < minAvailable) return false;
      
      return true;
    });
    
    // 排序：健康 > 忙碌 > 按负载从小到大
    if (preferHealthy) {
      candidates.sort((a, b) => {
        // 健康状态优先
        if (a.status === 'healthy' && b.status !== 'healthy') return -1;
        if (b.status === 'healthy' && a.status !== 'healthy') return 1;
        
        // 负载小的优先
        const loadA = a.currentLoad / a.maxConcurrent;
        const loadB = b.currentLoad / b.maxConcurrent;
        return loadA - loadB;
      });
    }
    
    return candidates;
  }

  /**
   * 获取单个 Agent
   * @param {string} agentId 
   */
  getAgent(agentId) {
    return this.agents.get(agentId);
  }

  /**
   * 获取所有健康 Agents
   */
  getHealthyAgents() {
    return Array.from(this.agents.values()).filter(
      agent => agent.status !== 'offline'
    );
  }

  /**
   * 获取所有 Agents
   */
  getAllAgents() {
    return Array.from(this.agents.values());
  }

  /**
   * 获取注册统计
   */
  getStats() {
    const agents = this.getAllAgents();
    
    return {
      total: agents.length,
      healthy: agents.filter(a => a.status === 'healthy').length,
      busy: agents.filter(a => a.status === 'busy').length,
      offline: agents.filter(a => a.status === 'offline').length,
      totalLoad: agents.reduce((sum, a) => sum + a.currentLoad, 0),
      totalCapacity: agents.reduce((sum, a) => sum + a.maxConcurrent, 0)
    };
  }

  /**
   * 启动健康检查
   */
  startHealthCheck() {
    setInterval(() => {
      const now = Date.now();
      
      for (const [agentId, agent] of this.agents) {
        // 检查是否超时
        if (now - agent.lastHeartbeat > this.offlineThreshold) {
          if (agent.status !== 'offline') {
            agent.status = 'offline';
            agent.currentLoad = 0; // 重置负载
            
            this.emit('agent-offline', { agentId, agent });
            console.warn(`[AgentRegistry] Agent 离线: ${agent.name} (${agentId})`);
          }
        }
      }
    }, this.heartbeatInterval);
  }

  /**
   * 创建本地 Agent
   * @param {string} name 
   * @param {Object} options 
   */
  createLocalAgent(name, options = {}) {
    const agentId = this.register({
      name,
      capabilities: options.capabilities || ['read', 'write'],
      maxConcurrent: options.maxConcurrent || 1,
      metadata: {
        type: 'local',
        ...options.metadata
      },
      endpoint: 'local'
    });
    
    return agentId;
  }

  /**
   * 关闭注册中心
   */
  close() {
    // 清理资源
    this.agents.clear();
    this.removeAllListeners();
  }
}

module.exports = {
  AgentRegistry
};
