/**
 * 策略权限系统
 * 根据策略分支控制可用工具和权限
 */

const EventEmitter = require('events');
const config = require('./config.json');

/**
 * 权限管理器
 */
class PolicyManager extends EventEmitter {
  constructor(options = {}) {
    super();
    
    // 默认权限策略
    this.policies = options.policies || {
      'Simple': {
        description: '最小权限 - 只读访问',
        tools: {
          allow: ['read', 'web_search', 'web_fetch'],
          deny: ['write', 'exec', 'delete', 'sessions_spawn']
        },
        resources: {
          maxFileSize: 1024 * 1024, // 1MB
          maxFiles: 5,
          allowNetwork: true,
          allowFileAccess: true
        },
        rateLimit: {
          requestsPerMinute: 30,
          tokensPerMinute: 10000
        }
      },
      
      'Standard': {
        description: '标准权限 - 读写访问',
        tools: {
          allow: ['read', 'write', 'web_search', 'web_fetch', 'image'],
          deny: ['exec', 'delete', 'cron', 'sessions_spawn']
        },
        resources: {
          maxFileSize: 10 * 1024 * 1024, // 10MB
          maxFiles: 20,
          allowNetwork: true,
          allowFileAccess: true
        },
        rateLimit: {
          requestsPerMinute: 60,
          tokensPerMinute: 50000
        }
      },
      
      'Batch': {
        description: '批处理权限 - 批量操作',
        tools: {
          allow: ['read', 'write', 'exec', 'web_search', 'web_fetch', 'sessions_spawn'],
          deny: ['delete', 'cron']
        },
        resources: {
          maxFileSize: 50 * 1024 * 1024, // 50MB
          maxFiles: 100,
          maxBatchSize: 20,
          allowNetwork: true,
          allowFileAccess: true
        },
        rateLimit: {
          requestsPerMinute: 30,
          tokensPerMinute: 100000
        }
      },
      
      'Orchestrator': {
        description: '编排权限 - 协调多个子代理',
        tools: {
          allow: ['read', 'write', 'exec', 'web_search', 'web_fetch', 'sessions_spawn', 'subagents'],
          deny: ['delete', 'cron']
        },
        resources: {
          maxFileSize: 50 * 1024 * 1024,
          maxFiles: 100,
          maxDepth: 2, // 最大spawn深度
          maxChildren: 5,
          allowNetwork: true,
          allowFileAccess: true
        },
        rateLimit: {
          requestsPerMinute: 20,
          tokensPerMinute: 100000
        }
      },
      
      'Deep': {
        description: '深度权限 - 动态申请',
        tools: {
          allow: ['read', 'write', 'exec', 'web_search', 'web_fetch', 'image'],
          deny: ['delete', 'cron'],
          dynamic: true // 需要动态申请
        },
        resources: {
          maxFileSize: 100 * 1024 * 1024, // 100MB
          maxFiles: 500,
          allowNetwork: true,
          allowFileAccess: true,
          requireApproval: true
        },
        rateLimit: {
          requestsPerMinute: 10,
          tokensPerMinute: 200000
        }
      }
    };
    
    this.requestHistory = [];
    this.activeGrants = new Map();
  }

  /**
   * 检查工具权限
   */
  canUseTool(branch, toolName) {
    const policy = this.policies[branch];
    if (!policy) return false;
    
    // 检查是否在允许列表
    if (policy.tools.allow.includes(toolName)) {
      return true;
    }
    
    // 检查是否在禁止列表
    if (policy.tools.deny.includes(toolName)) {
      return false;
    }
    
    // 默认允许（不在任何列表中）
    return true;
  }

  /**
   * 检查资源权限
   */
  checkResource(branch, resourceType, value) {
    const policy = this.policies[branch];
    if (!policy) return { allowed: false, reason: '未知策略' };
    
    const limits = policy.resources;
    
    switch (resourceType) {
      case 'fileSize':
        if (value > limits.maxFileSize) {
          return {
            allowed: false,
            reason: `文件大小 ${this.formatSize(value)} 超过限制 ${this.formatSize(limits.maxFileSize)}`,
            limit: limits.maxFileSize
          };
        }
        break;
        
      case 'fileCount':
        if (value > limits.maxFiles) {
          return {
            allowed: false,
            reason: `文件数量 ${value} 超过限制 ${limits.maxFiles}`,
            limit: limits.maxFiles
          };
        }
        break;
        
      case 'batchSize':
        if (limits.maxBatchSize && value > limits.maxBatchSize) {
          return {
            allowed: false,
            reason: `批处理大小 ${value} 超过限制 ${limits.maxBatchSize}`,
            limit: limits.maxBatchSize
          };
        }
        break;
        
      case 'spawnDepth':
        if (limits.maxDepth && value > limits.maxDepth) {
          return {
            allowed: false,
            reason: `嵌套深度 ${value} 超过限制 ${limits.maxDepth}`,
            limit: limits.maxDepth
          };
        }
        break;
        
      case 'network':
        if (!limits.allowNetwork) {
          return { allowed: false, reason: '策略禁止网络访问' };
        }
        break;
    }
    
    return { allowed: true };
  }

  /**
   * 申请动态权限（用于Deep策略）
   */
  async requestPermission(taskId, request, context = {}) {
    const { branch, tool, resource, reason } = request;
    
    // 记录申请
    const requestRecord = {
      taskId,
      timestamp: Date.now(),
      branch,
      request,
      context,
      status: 'pending'
    };
    
    this.requestHistory.push(requestRecord);
    
    // 触发申请事件
    this.emit('permission-requested', {
      taskId,
      request,
      context
    });
    
    // 对于Deep策略，自动批准基本权限
    if (branch === 'Deep' && this.isBasicTool(tool)) {
      this.grantPermission(taskId, request);
      requestRecord.status = 'granted-auto';
      return { granted: true, auto: true };
    }
    
    // 敏感操作需要人工确认
    if (this.isSensitiveTool(tool)) {
      requestRecord.status = 'awaiting-approval';
      return {
        granted: false,
        awaitingApproval: true,
        message: `需要用户确认: ${reason || tool}`
      };
    }
    
    // 其他情况自动批准
    this.grantPermission(taskId, request);
    requestRecord.status = 'granted';
    return { granted: true };
  }

  /**
   * 授权权限
   */
  grantPermission(taskId, request) {
    const grant = {
      taskId,
      request,
      grantedAt: Date.now(),
      expiresAt: Date.now() + 3600000 // 1小时过期
    };
    
    this.activeGrants.set(`${taskId}_${request.tool}`, grant);
    
    this.emit('permission-granted', {
      taskId,
      request
    });
  }

  /**
   * 检查是否已授权
   */
  hasPermission(taskId, tool) {
    const key = `${taskId}_${tool}`;
    const grant = this.activeGrants.get(key);
    
    if (!grant) return false;
    
    // 检查是否过期
    if (Date.now() > grant.expiresAt) {
      this.activeGrants.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * 撤销权限
   */
  revokePermission(taskId, tool) {
    const key = `${taskId}_${tool}`;
    this.activeGrants.delete(key);
    
    this.emit('permission-revoked', { taskId, tool });
  }

  /**
   * 检查是否是基本工具
   */
  isBasicTool(tool) {
    const basicTools = ['read', 'write', 'web_search', 'web_fetch'];
    return basicTools.includes(tool);
  }

  /**
   * 检查是否是敏感工具
   */
  isSensitiveTool(tool) {
    const sensitiveTools = ['delete', 'exec', 'sessions_spawn', 'cron'];
    return sensitiveTools.includes(tool);
  }

  /**
   * 验证操作
   */
  validateOperation(branch, operation, context = {}) {
    const { tool, params } = operation;
    
    // 1. 检查工具权限
    if (!this.canUseTool(branch, tool)) {
      return {
        allowed: false,
        reason: `策略 '${branch}' 不允许使用工具 '${tool}'`,
        policy: this.policies[branch]?.description
      };
    }
    
    // 2. 检查资源限制
    if (params) {
      if (params.fileSize) {
        const check = this.checkResource(branch, 'fileSize', params.fileSize);
        if (!check.allowed) return check;
      }
      
      if (params.fileCount) {
        const check = this.checkResource(branch, 'fileCount', params.fileCount);
        if (!check.allowed) return check;
      }
    }
    
    // 3. Deep策略动态检查
    if (branch === 'Deep' && this.policies[Deep]?.tools?.dynamic) {
      const taskId = context.taskId;
      if (!this.hasPermission(taskId, tool)) {
        return {
          allowed: false,
          reason: `Deep策略需要动态授权 '${tool}'`,
          requiresPermission: true
        };
      }
    }
    
    return { allowed: true };
  }

  /**
   * 获取策略详情
   */
  getPolicy(branch) {
    return this.policies[branch] || null;
  }

  /**
   * 获取所有策略
   */
  getAllPolicies() {
    return Object.entries(this.policies).map(([name, policy]) => ({
      name,
      description: policy.description,
      allowedTools: policy.tools.allow,
      deniedTools: policy.tools.deny
    }));
  }

  /**
   * 获取权限申请历史
   */
  getRequestHistory(taskId = null) {
    if (taskId) {
      return this.requestHistory.filter(r => r.taskId === taskId);
    }
    return this.requestHistory;
  }

  /**
   * 格式化大小
   */
  formatSize(bytes) {
    if (bytes < 1024) return bytes + 'B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + 'MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + 'GB';
  }

  /**
   * 清理过期授权
   */
  cleanupExpiredGrants() {
    const now = Date.now();
    let count = 0;
    
    for (const [key, grant] of this.activeGrants) {
      if (now > grant.expiresAt) {
        this.activeGrants.delete(key);
        count++;
      }
    }
    
    return count;
  }
}

module.exports = {
  PolicyManager
};
