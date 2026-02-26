/**
 * Collaboration Hub
 * 协作中心 - Agent间通信、状态共享、进度同步
 */

const EventEmitter = require('events');

/**
 * 消息类型枚举
 */
const MessageType = {
  REQUEST: 'request',       // 请求
  RESPONSE: 'response',     // 响应
  BROADCAST: 'broadcast',   // 广播
  PROGRESS: 'progress',     // 进度更新
  STATE_UPDATE: 'state_update', // 状态更新
  ERROR: 'error',           // 错误
  HEARTBEAT: 'heartbeat'    // 心跳
};

/**
 * 协作中心类
 * 管理多Agent间的通信、状态共享和进度同步
 */
class CollaborationHub extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.agents = new Map();           // agentId -> agentInfo
    this.channels = new Map();         // channelName -> Set<agentId>
    this.globalState = new Map();      // 全局共享状态
    this.taskStates = new Map();       // taskId -> taskState
    this.tempStates = new Map();       // agentId -> tempState
    this.messageHistory = [];          // 消息历史
    this.maxHistorySize = options.maxHistorySize || 1000;
    
    // 启动心跳检查
    this.startHeartbeatCheck();
  }

  /**
   * 注册Agent到协作中心
   */
  registerAgent(agentId, agentInfo = {}) {
    if (this.agents.has(agentId)) {
      console.warn(`[Hub] Agent ${agentId} 已存在，更新信息`);
    }
    
    this.agents.set(agentId, {
      id: agentId,
      name: agentInfo.name || agentId,
      capabilities: agentInfo.capabilities || [],
      status: 'online',
      lastHeartbeat: Date.now(),
      currentTask: null,
      metadata: agentInfo.metadata || {}
    });
    
    // 创建agent专属临时状态存储
    this.tempStates.set(agentId, new Map());
    
    this.emit('agent-registered', { agentId, agentInfo });
    console.log(`[Hub] Agent注册成功: ${agentId}`);
    
    return agentId;
  }

  /**
   * 注销Agent
   */
  unregisterAgent(agentId) {
    if (!this.agents.has(agentId)) {
      return false;
    }
    
    // 从所有频道移除
    for (const [channel, agents] of this.channels) {
      agents.delete(agentId);
    }
    
    // 清理临时状态
    this.tempStates.delete(agentId);
    
    this.agents.delete(agentId);
    this.emit('agent-unregistered', { agentId });
    console.log(`[Hub] Agent注销: ${agentId}`);
    
    return true;
  }

  /**
   * 发送点对点消息
   */
  sendTo(senderId, targetId, message) {
    const target = this.agents.get(targetId);
    if (!target) {
      throw new Error(`目标Agent不存在: ${targetId}`);
    }
    
    if (target.status === 'offline') {
      throw new Error(`目标Agent离线: ${targetId}`);
    }
    
    const envelope = this.createEnvelope(MessageType.REQUEST, senderId, targetId, message);
    this.deliverMessage(envelope);
    
    return envelope.id;
  }

  /**
   * 广播消息
   */
  broadcast(senderId, message, options = {}) {
    const { channel = 'default', exclude = [] } = options;
    
    const targets = this.channels.get(channel) || new Set();
    const onlineAgents = Array.from(targets).filter(id => {
      const agent = this.agents.get(id);
      return agent && agent.status === 'online' && !exclude.includes(id);
    });
    
    const envelope = this.createEnvelope(
      MessageType.BROADCAST, 
      senderId, 
      onlineAgents,
      message,
      { channel }
    );
    
    this.deliverMessage(envelope);
    
    return {
      messageId: envelope.id,
      recipients: onlineAgents.length
    };
  }

  /**
   * 发布-订阅模式
   */
  subscribe(agentId, topic, callback) {
    const channelName = `topic:${topic}`;
    
    if (!this.channels.has(channelName)) {
      this.channels.set(channelName, new Set());
    }
    
    this.channels.get(channelName).add(agentId);
    
    // 监听该主题的消息
    this.on(`topic:${topic}`, callback);
    
    return {
      unsubscribe: () => {
        this.channels.get(channelName)?.delete(agentId);
        this.off(`topic:${topic}`, callback);
      }
    };
  }

  /**
   * 发布消息到主题
   */
  publish(topic, message, senderId = 'system') {
    const channelName = `topic:${topic}`;
    const subscribers = this.channels.get(channelName) || new Set();
    
    const envelope = this.createEnvelope(
      MessageType.BROADCAST,
      senderId,
      Array.from(subscribers),
      message,
      { topic }
    );
    
    this.deliverMessage(envelope);
    this.emit(`topic:${topic}`, message, senderId);
    
    return envelope.id;
  }

  /**
   * 加入频道
   */
  joinChannel(agentId, channelName) {
    if (!this.channels.has(channelName)) {
      this.channels.set(channelName, new Set());
    }
    
    this.channels.get(channelName).add(agentId);
    this.emit('channel-joined', { agentId, channelName });
  }

  /**
   * 离开频道
   */
  leaveChannel(agentId, channelName) {
    this.channels.get(channelName)?.delete(agentId);
    this.emit('channel-left', { agentId, channelName });
  }

  /**
   * 设置全局状态（所有Agent可读写）
   */
  setGlobal(key, value, options = {}) {
    const { ttl, agentId } = options;
    
    this.globalState.set(key, {
      value,
      agentId: agentId || 'system',
      timestamp: Date.now(),
      ttl: ttl || null
    });
    
    this.emit('state-changed', { scope: 'global', key, value });
    
    // 广播状态更新
    this.broadcast('system', {
      type: 'state_update',
      scope: 'global',
      key,
      value
    }, { channel: 'state_updates' });
  }

  /**
   * 获取全局状态
   */
  getGlobal(key) {
    const state = this.globalState.get(key);
    if (!state) return undefined;
    
    // 检查TTL
    if (state.ttl && Date.now() - state.timestamp > state.ttl) {
      this.globalState.delete(key);
      return undefined;
    }
    
    return state.value;
  }

  /**
   * 设置任务级状态
   */
  setTask(taskId, key, value) {
    if (!this.taskStates.has(taskId)) {
      this.taskStates.set(taskId, new Map());
    }
    
    const taskState = this.taskStates.get(taskId);
    taskState.set(key, {
      value,
      timestamp: Date.now()
    });
    
    this.emit('task-state-changed', { taskId, key, value });
  }

  /**
   * 获取任务级状态
   */
  getTask(taskId, key) {
    const taskState = this.taskStates.get(taskId);
    if (!taskState) return undefined;
    
    const entry = taskState.get(key);
    return entry ? entry.value : undefined;
  }

  /**
   * 获取任务所有状态
   */
  getTaskState(taskId) {
    const taskState = this.taskStates.get(taskId);
    if (!taskState) return {};
    
    const result = {};
    for (const [key, entry] of taskState) {
      result[key] = entry.value;
    }
    return result;
  }

  /**
   * 设置临时状态（Agent私有）
   */
  setTemp(agentId, key, value) {
    const agentTemp = this.tempStates.get(agentId);
    if (!agentTemp) {
      throw new Error(`Agent不存在: ${agentId}`);
    }
    
    agentTemp.set(key, {
      value,
      timestamp: Date.now()
    });
  }

  /**
   * 获取临时状态
   */
  getTemp(agentId, key) {
    const agentTemp = this.tempStates.get(agentId);
    if (!agentTemp) return undefined;
    
    const entry = agentTemp.get(key);
    return entry ? entry.value : undefined;
  }

  /**
   * 报告进度
   */
  reportProgress(agentId, taskId, progress, metadata = {}) {
    const progressData = {
      agentId,
      taskId,
      progress: Math.min(100, Math.max(0, progress)),
      metadata,
      timestamp: Date.now()
    };
    
    // 更新Agent当前任务状态
    const agent = this.agents.get(agentId);
    if (agent) {
      agent.currentTask = { taskId, progress: progressData.progress };
    }
    
    this.emit('progress-updated', progressData);
    
    // 广播进度到任务频道
    this.publish(`task:${taskId}:progress`, progressData, agentId);
  }

  /**
   * 发送心跳
   */
  heartbeat(agentId) {
    const agent = this.agents.get(agentId);
    if (agent) {
      agent.lastHeartbeat = Date.now();
      agent.status = 'online';
    }
  }

  /**
   * 启动心跳检查
   */
  startHeartbeatCheck() {
    const checkInterval = 30000; // 30秒检查一次
    
    setInterval(() => {
      const now = Date.now();
      const timeout = 120000; // 2分钟无心跳视为离线
      
      for (const [agentId, agent] of this.agents) {
        if (now - agent.lastHeartbeat > timeout) {
          agent.status = 'offline';
          this.emit('agent-offline', { agentId });
          console.warn(`[Hub] Agent离线: ${agentId}`);
        }
      }
    }, checkInterval);
  }

  /**
   * 创建消息信封
   */
  createEnvelope(type, senderId, targetId, payload, options = {}) {
    return {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      senderId,
      targetId: Array.isArray(targetId) ? targetId : [targetId],
      payload,
      timestamp: Date.now(),
      ...options
    };
  }

  /**
   * 投递消息
   */
  deliverMessage(envelope) {
    // 记录消息历史
    this.messageHistory.push(envelope);
    
    // 限制历史大小
    if (this.messageHistory.length > this.maxHistorySize) {
      this.messageHistory = this.messageHistory.slice(-this.maxHistorySize);
    }
    
    // 触发事件
    this.emit('message', envelope);
    
    // 针对特定类型的额外处理
    switch (envelope.type) {
      case MessageType.PROGRESS:
        this.emit('progress', envelope);
        break;
      case MessageType.STATE_UPDATE:
        this.emit('state-update', envelope);
        break;
      case MessageType.ERROR:
        this.emit('error-message', envelope);
        break;
    }
  }

  /**
   * 获取系统统计
   */
  getStats() {
    return {
      agents: {
        total: this.agents.size,
        online: Array.from(this.agents.values()).filter(a => a.status === 'online').length,
        offline: Array.from(this.agents.values()).filter(a => a.status === 'offline').length
      },
      channels: this.channels.size,
      globalState: this.globalState.size,
      activeTasks: this.taskStates.size,
      messageHistory: this.messageHistory.length
    };
  }

  /**
   * 获取Agent列表
   */
  getAgents() {
    return Array.from(this.agents.values());
  }

  /**
   * 获取频道列表
   */
  getChannels() {
    const result = {};
    for (const [name, agents] of this.channels) {
      result[name] = Array.from(agents);
    }
    return result;
  }

  /**
   * 清理过期状态
   */
  cleanup() {
    const now = Date.now();
    
    // 清理过期的全局状态
    for (const [key, state] of this.globalState) {
      if (state.ttl && now - state.timestamp > state.ttl) {
        this.globalState.delete(key);
      }
    }
    
    // 清理过期的任务状态（1小时后）
    for (const [taskId, taskState] of this.taskStates) {
      const lastUpdate = Array.from(taskState.values())
        .reduce((max, entry) => Math.max(max, entry.timestamp), 0);
      
      if (now - lastUpdate > 3600000) {
        this.taskStates.delete(taskId);
      }
    }
  }

  /**
   * 关闭协作中心
   */
  close() {
    this.agents.clear();
    this.channels.clear();
    this.globalState.clear();
    this.taskStates.clear();
    this.tempStates.clear();
    this.messageHistory = [];
    this.removeAllListeners();
  }
}

module.exports = {
  CollaborationHub,
  MessageType
};
