/**
 * 飞书回调处理器
 * 由于网关是loopback无法接收回调，使用轮询方式处理
 */

const { getCronManager } = require('./cron-manager');

class FeishuCallbackHandler {
  constructor(feishuApi) {
    this.feishuApi = feishuApi;
    this.pendingCallbacks = new Map();
    this.cronManager = getCronManager();
  }

  /**
   * 发送确认卡片并等待用户响应
   * 使用轮询方式检查用户是否回复
   */
  async sendConfirmAndWait(card, chatId, options = {}) {
    const { timeout = 60000, checkInterval = 5 } = options;
    const messageId = await this.sendCard(card, chatId);
    
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let checkCount = 0;
      
      // 启动轮询检查用户回复
      const checkReply = async () => {
        checkCount++;
        
        try {
          // 检查是否有新消息
          const messages = await this.getRecentMessages(chatId);
          const userReply = this.findUserReply(messages, messageId);
          
          if (userReply) {
            // 解析用户回复
            const action = this.parseUserReply(userReply);
            resolve({ action, messageId, userReply });
            return;
          }
          
          // 检查是否超时
          if (Date.now() - startTime > timeout) {
            reject(new Error('用户确认超时'));
            return;
          }
          
          // 继续轮询
          setTimeout(checkReply, checkInterval * 1000);
          
        } catch (error) {
          reject(error);
        }
      };
      
      // 开始轮询
      checkReply();
    });
  }

  /**
   * 解析用户回复为操作
   * 支持多种回复格式
   */
  parseUserReply(message) {
    const text = message.toLowerCase().trim();
    
    // 确认执行
    if (/确认|执行|开始|yes|ok|确定/.test(text)) {
      return { action: 'confirm' };
    }
    
    // 降级到Simple
    if (/简单|降级|simple|换/.test(text)) {
      return { action: 'downgrade', target: 'Simple' };
    }
    
    // 取消
    if (/取消|停止|cancel|no|否/.test(text)) {
      return { action: 'cancel' };
    }
    
    // 默认确认（如果用户回复了任何内容）
    return { action: 'confirm' };
  }

  /**
   * 发送卡片消息
   */
  async sendCard(card, chatId) {
    // 实际应调用飞书API
    console.log('[FeishuCallback] 发送卡片:', card);
    return `msg_${Date.now()}`;
  }

  /**
   * 获取最近消息
   * 模拟实现，实际应调用飞书API
   */
  async getRecentMessages(chatId) {
    // 模拟返回消息列表
    return [];
  }

  /**
   * 查找用户回复
   */
  findUserReply(messages, cardMessageId) {
    // 查找在卡片发送后的用户消息
    return messages.find(m => m.type === 'text' && m.timestamp > cardMessageId);
  }

  /**
   * 替代方案：使用文字指令代替按钮
   * 发送文字说明，让用户回复指令
   */
  async sendTextConfirm(taskInfo, chatId) {
    const text = `🤖 任务分析完成

选择策略：${taskInfo.branch}
预估耗时：${taskInfo.duration}秒
预估成本：$${taskInfo.cost.toFixed(4)}

请回复以下指令：
• "确认" - 执行该策略
• "简单" - 降级为简单模式
• "取消" - 取消任务

（60秒内无回复将自动确认）`;

    await this.feishuApi.sendMessage(chatId, { msg_type: 'text', content: { text } });
    
    // 等待用户回复
    return this.waitForReply(chatId, 60);
  }

  /**
   * 等待用户回复
   */
  async waitForReply(chatId, timeoutSeconds) {
    return new Promise((resolve) => {
      const startTime = Date.now();
      
      const check = async () => {
        const messages = await this.getRecentMessages(chatId);
        const lastMessage = messages[messages.length - 1];
        
        if (lastMessage && lastMessage.timestamp > startTime) {
          resolve(this.parseUserReply(lastMessage));
          return;
        }
        
        if (Date.now() - startTime > timeoutSeconds * 1000) {
          resolve({ action: 'confirm' }); // 超时自动确认
          return;
        }
        
        setTimeout(check, 3000); // 每3秒检查一次
      };
      
      check();
    });
  }
}

module.exports = {
  FeishuCallbackHandler
};
