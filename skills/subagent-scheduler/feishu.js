/**
 * 飞书交互模块
 * 实现卡片消息、按钮交互、消息更新
 */

const config = require('./config.json');

/**
 * 构建确认卡片消息
 */
function buildConfirmCard(branch, estimation, historyStats = null) {
  const elements = [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": `**🤖 任务分析完成**\n\n**选择策略：** ${branch}\n**预估耗时：** ${estimation.duration} 秒\n**预估成本：** $${estimation.cost.toFixed(4)}`
      }
    }
  ];
  
  // 添加历史统计（如果有）
  if (historyStats) {
    elements.push({
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": `📊 **历史数据：** 成功率 ${historyStats.successRate}%（${historyStats.count}次任务，平均耗时${historyStats.avgDuration}秒）`
      }
    });
  }
  
  // 添加按钮
  elements.push({
    "tag": "action",
    "actions": [
      {
        "tag": "button",
        "text": {"tag": "plain_text", "content": "✓ 确认执行"},
        "type": "primary",
        "value": {"action": "confirm", "branch": branch}
      },
      {
        "tag": "button",
        "text": {"tag": "plain_text", "content": "⇄ 换简单模式"},
        "type": "default",
        "value": {"action": "downgrade", "branch": "Simple"}
      },
      {
        "tag": "button",
        "text": {"tag": "plain_text", "content": "✕ 取消"},
        "type": "danger",
        "value": {"action": "cancel"}
      }
    ]
  });
  
  return {
    "msg_type": "interactive",
    "card": {
      "config": {"wide_screen_mode": true},
      "header": {
        "title": {"tag": "plain_text", "content": "子代理任务确认"},
        "template": "blue"
      },
      "elements": elements
    }
  };
}

/**
 * 构建进度更新消息
 */
function buildProgressMessage(progress, elapsed, cost = null) {
  const emoji = progress < 30 ? '⏳' : progress < 70 ? '🔧' : '🔍';
  let content = `${emoji} **任务执行中... ${progress}%**\n\n已耗时：${elapsed}秒`;
  
  if (cost) {
    content += `\n当前成本：$${cost.toFixed(4)}`;
  }
  
  // 进度条
  const filled = Math.floor(progress / 10);
  const empty = 10 - filled;
  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  content += `\n\n${bar} ${progress}%`;
  
  return {
    "msg_type": "text",
    "content": {
      "text": content
    }
  };
}

/**
 * 构建完成消息
 */
function buildCompleteMessage(success, duration, cost, result, error = null) {
  if (success) {
    return {
      "msg_type": "interactive",
      "card": {
        "config": {"wide_screen_mode": true},
        "header": {
          "title": {"tag": "plain_text", "content": "✅ 任务完成"},
          "template": "green"
        },
        "elements": [
          {
            "tag": "div",
            "text": {
              "tag": "lark_md",
              "content": `**执行时间：** ${duration}秒\n**实际成本：** $${cost.toFixed(4)}\n\n**结果摘要：**\n${result ? result.substring(0, 200) : '（无结果）'}${result && result.length > 200 ? '...' : ''}`
            }
          }
        ]
      }
    };
  } else {
    return {
      "msg_type": "interactive",
      "card": {
        "config": {"wide_screen_mode": true},
        "header": {
          "title": {"tag": "plain_text", "content": "❌ 任务失败"},
          "template": "red"
        },
        "elements": [
          {
            "tag": "div",
            "text": {
              "tag": "lark_md",
              "content": `**执行时间：** ${duration}秒\n**失败原因：** ${error || '未知错误'}\n\n已尝试重试5次，建议检查任务内容或稍后重试。`
            }
          }
        ]
      }
    };
  }
}

/**
 * 构建日报卡片
 */
function buildDailyReport(stats) {
  const branches = Object.keys(stats.byBranch || {});
  let branchText = '';
  
  branches.forEach(branch => {
    const b = stats.byBranch[branch];
    branchText += `- **${branch}：** ${b.count}次，成功率${b.successRate}%，平均${b.avgDuration}秒\n`;
  });
  
  return {
    "msg_type": "interactive",
    "card": {
      "config": {"wide_screen_mode": true},
      "header": {
        "title": {"tag": "plain_text", "content": "📊 子代理调度日报"},
        "template": "blue"
      },
      "elements": [
        {
          "tag": "div",
          "text": {
            "tag": "lark_md",
            "content": `**统计周期：** ${stats.date}\n**总任务数：** ${stats.totalTasks}\n**总成本：** $${stats.totalCost.toFixed(4)}\n**整体成功率：** ${stats.overallSuccessRate}%\n\n**分策略统计：**\n${branchText}`
          }
        }
      ]
    }
  };
}

/**
 * 发送飞书消息（模拟）
 * 实际应调用飞书API
 */
async function sendMessage(chatId, message) {
  // 记录消息用于演示
  console.log(`[Feishu] Send to ${chatId}:`, JSON.stringify(message, null, 2));
  return {
    message_id: `msg_${Date.now()}`,
    chat_id: chatId
  };
}

/**
 * 更新飞书消息（模拟）
 */
async function updateMessage(messageId, message) {
  console.log(`[Feishu] Update ${messageId}:`, JSON.stringify(message, null, 2));
  return { success: true };
}

/**
 * 处理按钮回调（模拟）
 * 实际应解析飞书回调事件
 */
function parseCallback(callbackData) {
  try {
    return JSON.parse(callbackData);
  } catch (e) {
    return { action: 'unknown' };
  }
}

module.exports = {
  buildConfirmCard,
  buildProgressMessage,
  buildCompleteMessage,
  buildDailyReport,
  sendMessage,
  updateMessage,
  parseCallback
};
