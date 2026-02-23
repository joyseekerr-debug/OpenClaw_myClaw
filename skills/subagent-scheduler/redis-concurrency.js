/**
 * Redis全局并发控制器
 * 使用Redis实现跨会话的并发控制
 */

const Redis = require('ioredis');

class RedisConcurrencyController {
  constructor(redisConfig = {}) {
    this.redis = new Redis({
      host: redisConfig.host || 'localhost',
      port: redisConfig.port || 6379,
      db: redisConfig.db || 0,
      retryStrategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      }
    });
    
    this.limits = {
      Simple: 10,
      Standard: 4,
      Batch: 2,
      Orchestrator: 2,
      Deep: 1
    };
    
    this.prefix = 'subagent:concurrency:';
  }

  /**
   * 尝试获取执行槽位
   * @param {string} branch - 分支类型
   * @param {string} taskId - 任务ID
   * @returns {Promise<boolean>} 是否成功
   */
  async acquireSlot(branch, taskId) {
    const key = `${this.prefix}${branch}`;
    const limit = this.limits[branch] || 1;
    
    // 使用Redis Lua脚本实现原子操作
    const luaScript = `
      local key = KEYS[1]
      local limit = tonumber(ARGV[1])
      local taskId = ARGV[2]
      local current = redis.call('scard', key)
      
      if current < limit then
        redis.call('sadd', key, taskId)
        redis.call('expire', key, 3600)  -- 1小时过期
        return 1
      else
        return 0
      end
    `;
    
    const result = await this.redis.eval(luaScript, 1, key, limit, taskId);
    return result === 1;
  }

  /**
   * 释放执行槽位
   */
  async releaseSlot(branch, taskId) {
    const key = `${this.prefix}${branch}`;
    await this.redis.srem(key, taskId);
  }

  /**
   * 获取当前并发数
   */
  async getCurrentConcurrency(branch) {
    const key = `${this.prefix}${branch}`;
    return await this.redis.scard(key);
  }

  /**
   * 等待槽位可用
   */
  async waitForSlot(branch, taskId, timeout = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const acquired = await this.acquireSlot(branch, taskId);
      if (acquired) return true;
      
      // 等待500ms后重试
      await new Promise(r => setTimeout(r, 500));
    }
    
    throw new Error(`等待${branch}槽位超时`);
  }

  /**
   * 获取所有分支的并发状态
   */
  async getAllStatus() {
    const status = {};
    for (const branch of Object.keys(this.limits)) {
      status[branch] = {
        current: await this.getCurrentConcurrency(branch),
        limit: this.limits[branch]
      };
    }
    return status;
  }

  /**
   * 关闭连接
   */
  async close() {
    await this.redis.quit();
  }
}

// 本地模拟模式（当Redis不可用时）
class LocalConcurrencyController {
  constructor() {
    this.slots = new Map();
    this.limits = {
      Simple: 10,
      Standard: 4,
      Batch: 2,
      Orchestrator: 2,
      Deep: 1
    };
  }

  async acquireSlot(branch, taskId) {
    if (!this.slots.has(branch)) {
      this.slots.set(branch, new Set());
    }
    
    const slot = this.slots.get(branch);
    if (slot.size < this.limits[branch]) {
      slot.add(taskId);
      return true;
    }
    return false;
  }

  async releaseSlot(branch, taskId) {
    const slot = this.slots.get(branch);
    if (slot) {
      slot.delete(taskId);
    }
  }

  async getCurrentConcurrency(branch) {
    const slot = this.slots.get(branch);
    return slot ? slot.size : 0;
  }

  async getAllStatus() {
    const status = {};
    for (const [branch, limit] of Object.entries(this.limits)) {
      status[branch] = {
        current: await this.getCurrentConcurrency(branch),
        limit
      };
    }
    return status;
  }

  async close() {}
}

module.exports = {
  RedisConcurrencyController,
  LocalConcurrencyController
};
