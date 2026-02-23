/**
 * SQLite数据库操作封装
 * 使用 better-sqlite3 或类似的同步SQLite库
 * 由于OpenClaw环境限制，这里使用文件模拟
 */

const fs = require('fs');
const path = require('path');
const config = require('./config.json');

const DB_PATH = config.database.path;

/**
 * 初始化数据库（创建表结构）
 */
function initDatabase() {
  const dbDir = path.dirname(DB_PATH);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  
  // 读取并执行schema.sql
  const schemaPath = path.join(__dirname, 'schema.sql');
  const schema = fs.readFileSync(schemaPath, 'utf-8');
  
  // 简化：将SQL语句存储到JSON文件模拟
  // 实际应用中应使用真正的SQLite
  const metaPath = DB_PATH + '.meta.json';
  if (!fs.existsSync(metaPath)) {
    fs.writeFileSync(metaPath, JSON.stringify({
      initialized: true,
      createdAt: new Date().toISOString(),
      tables: ['task_history', 'concurrency_state', 'checkpoints', 'feishu_messages']
    }, null, 2));
  }
  
  return true;
}

/**
 * 模拟数据库查询
 * 实际应用中应使用真正的SQLite
 */
async function query(sql, params = []) {
  // 读取数据文件
  const dataPath = DB_PATH + '.data.json';
  let data = {};
  
  if (fs.existsSync(dataPath)) {
    try {
      data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    } catch (e) {
      data = {};
    }
  }
  
  // 简单模拟：返回task_history中匹配的数据
  if (sql.includes('task_history')) {
    const history = data.task_history || [];
    // 简化的WHERE匹配
    if (params.length > 0 && params[0]) {
      const prefix = params[0].replace('%', '');
      return history.filter(h => h.task_hash && h.task_hash.startsWith(prefix));
    }
    return history.slice(-10); // 返回最近10条
  }
  
  if (sql.includes('concurrency_state')) {
    return data.concurrency_state || { running_standard: 0, running_deep: 0 };
  }
  
  return [];
}

/**
 * 模拟数据库执行
 */
async function run(sql, params = []) {
  const dataPath = DB_PATH + '.data.json';
  let data = {};
  
  if (fs.existsSync(dataPath)) {
    try {
      data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    } catch (e) {
      data = {};
    }
  }
  
  if (sql.includes('INSERT INTO task_history')) {
    if (!data.task_history) data.task_history = [];
    data.task_history.push({
      id: data.task_history.length + 1,
      task_hash: params[0],
      task_preview: params[1],
      branch: params[2],
      duration_ms: params[3],
      estimated_cost: params[4],
      actual_cost: params[5],
      success: params[6],
      retry_count: params[7],
      error_message: params[8],
      created_at: new Date().toISOString()
    });
  }
  
  if (sql.includes('INSERT INTO feishu_messages')) {
    if (!data.feishu_messages) data.feishu_messages = [];
    data.feishu_messages.push({
      id: data.feishu_messages.length + 1,
      task_id: params[0],
      message_id: params[1],
      chat_id: params[2],
      msg_type: params[3],
      content_preview: params[4],
      created_at: new Date().toISOString()
    });
  }
  
  fs.writeFileSync(dataPath, JSON.stringify(data, null, 2));
  return { lastID: 1, changes: 1 };
}

/**
 * 获取历史统计
 */
async function getHistoryStats(branch = null, days = 7) {
  const dataPath = DB_PATH + '.data.json';
  if (!fs.existsSync(dataPath)) return null;
  
  try {
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    const history = data.task_history || [];
    
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    
    const recent = history.filter(h => {
      if (branch && h.branch !== branch) return false;
      return new Date(h.created_at) >= cutoff;
    });
    
    if (recent.length === 0) return null;
    
    const successCount = recent.filter(h => h.success).length;
    const avgDuration = recent.reduce((sum, h) => sum + (h.duration_ms || 0), 0) / recent.length;
    const avgCost = recent.reduce((sum, h) => sum + (h.actual_cost || 0), 0) / recent.length;
    
    return {
      count: recent.length,
      successRate: (successCount / recent.length * 100).toFixed(1),
      avgDuration: Math.round(avgDuration / 1000),
      avgCost: avgCost.toFixed(4)
    };
  } catch (e) {
    return null;
  }
}

module.exports = {
  initDatabase,
  query,
  run,
  getHistoryStats
};
