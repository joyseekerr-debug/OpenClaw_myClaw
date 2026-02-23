/**
 * SQLite数据库测试
 */

const db = require('./database');

async function testSQLite() {
  console.log('=== SQLite数据库测试 ===\n');
  
  try {
    // 1. 初始化
    console.log('1. 初始化数据库...');
    db.initDatabase();
    console.log('✓ 初始化成功\n');
    
    // 2. 插入测试数据
    console.log('2. 插入测试数据...');
    for (let i = 0; i < 5; i++) {
      await db.insertTaskHistory({
        task_hash: `test_hash_${i}`,
        task_preview: `测试任务 ${i}`,
        branch: ['Simple', 'Standard', 'Batch'][i % 3],
        duration_ms: 30000 + i * 10000,
        estimated_cost: 0.05,
        actual_cost: 0.048,
        success: i % 2 === 0,
        retry_count: 0,
        error_message: null
      });
    }
    console.log('✓ 插入5条测试数据\n');
    
    // 3. 查询所有数据
    console.log('3. 查询所有数据...');
    const all = await db.query('SELECT * FROM task_history ORDER BY id DESC LIMIT 5');
    console.log(`✓ 查询到 ${all.length} 条记录`);
    all.forEach(row => {
      console.log(`  - ${row.branch}: ${row.task_preview} (${row.success ? '成功' : '失败'})`);
    });
    console.log('');
    
    // 4. 统计查询
    console.log('4. 统计查询...');
    const stats = await db.getHistoryStats(null, 7);
    console.log('✓ 历史统计:', stats);
    
    const standardStats = await db.getHistoryStats('Standard', 7);
    console.log('✓ Standard分支统计:', standardStats);
    console.log('');
    
    // 5. 相似任务查询
    console.log('5. 相似任务查询...');
    const similar = await db.getSimilarTasks('test_hash', 3);
    console.log(`✓ 找到 ${similar.length} 条相似任务`);
    console.log('');
    
    console.log('=== 所有SQLite测试通过 ===');
    
  } catch (e) {
    console.error('❌ 测试失败:', e.message);
    console.error(e.stack);
  } finally {
    db.closeDatabase();
  }
}

testSQLite();
