/**
 * SQLite数据库操作封装
 * 使用 better-sqlite3 真实SQLite数据库
 */

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_DIR = path.join(__dirname, 'data');
const DB_PATH = path.join(DB_DIR, 'subagent.db');

let db = null;

/**
 * 初始化数据库
 */
function initDatabase() {
  // 创建数据目录
  if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
  }
  
  // 打开或创建数据库
  db = new Database(DB_PATH);
  
  // 读取并执行schema
  const schemaPath = path.join(__dirname, 'schema.sql');
  const schema = fs.readFileSync(schemaPath, 'utf-8');
  
  // 分割SQL语句并执行
  const statements = schema.split(';').filter(s => s.trim());
  for (const stmt of statements) {
    try {
      db.exec(stmt);
    } catch (e) {
      // 表已存在等错误可以忽略
      if (!e.message.includes('already exists')) {
        console.error('Schema error:', e.message);
      }
    }
  }
  
  console.log('[SQLite] 数据库初始化完成:', DB_PATH);
  return true;
}

/**
 * 查询数据
 */
async function query(sql, params = []) {
  if (!db) initDatabase();
  
  try {
    const stmt = db.prepare(sql);
    
    // 判断是查询还是执行
    if (sql.trim().toLowerCase().startsWith('select')) {
      return stmt.all(...params) || [];
    } else {
      return stmt.run(...params);
    }
  } catch (e) {
    console.error('[SQLite] Query error:', e.message);
    throw e;
  }
}

/**
 * 执行SQL
 */
async function run(sql, params = []) {
  return query(sql, params);
}

/**
 * 获取历史统计
 */
async function getHistoryStats(branch = null, days = 7) {
  if (!db) initDatabase();
  
  try {
    let sql = `
      SELECT 
        COUNT(*) as count,
        AVG(CASE WHEN success = 1 THEN duration_ms END) as avg_duration,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
        AVG(actual_cost) as avg_cost
      FROM task_history
      WHERE created_at > datetime('now', '-${days} days')
    `;
    
    if (branch) {
      sql += ` AND branch = '${branch}'`;
    }
    
    const result = db.prepare(sql).get();
    
    if (!result || result.count === 0) {
      return null;
    }
    
    return {
      count: result.count,
      successRate: result.success_rate?.toFixed(1) || '0',
      avgDuration: Math.round((result.avg_duration || 0) / 1000),
      avgCost: (result.avg_cost || 0).toFixed(4)
    };
  } catch (e) {
    console.error('[SQLite] Stats error:', e.message);
    return null;
  }
}

/**
 * 插入任务历史
 */
async function insertTaskHistory(data) {
  if (!db) initDatabase();
  
  const stmt = db.prepare(`
    INSERT INTO task_history 
    (task_hash, task_preview, branch, duration_ms, estimated_cost, actual_cost, success, retry_count, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  return stmt.run(
    data.task_hash,
    data.task_preview,
    data.branch,
    data.duration_ms,
    data.estimated_cost,
    data.actual_cost,
    data.success ? 1 : 0,
    data.retry_count || 0,
    data.error_message
  );
}

/**
 * 获取相似任务历史
 */
async function getSimilarTasks(taskHashPrefix, limit = 10) {
  if (!db) initDatabase();
  
  const stmt = db.prepare(`
    SELECT branch, duration_ms, success, actual_cost
    FROM task_history
    WHERE task_hash LIKE ?
    ORDER BY created_at DESC
    LIMIT ?
  `);
  
  return stmt.all(`${taskHashPrefix}%`, limit);
}

/**
 * 关闭数据库
 */
function closeDatabase() {
  if (db) {
    db.close();
    db = null;
  }
}

module.exports = {
  initDatabase,
  query,
  run,
  getHistoryStats,
  insertTaskHistory,
  getSimilarTasks,
  closeDatabase
};
