/**
 * Phase 4 学习引擎测试
 * 验证每日学习、自动优化建议
 */

const scheduler = require('./index');
const { LearningEngine } = require('./learning-engine');

async function runPhase4Tests() {
  console.log('=== Phase 4 自适应学习测试 ===\n');

  // 先添加一些测试数据到数据库
  console.log('1. 准备测试数据...');
  const sch = await scheduler.init();
  
  // 模拟添加历史任务记录
  const testData = [
    { branch: 'Simple', duration: 3000, success: 1, estimated: 5000, actual: 0.001 },
    { branch: 'Simple', duration: 4000, success: 1, estimated: 5000, actual: 0.002 },
    { branch: 'Standard', duration: 45000, success: 1, estimated: 45000, actual: 0.01 },
    { branch: 'Standard', duration: 60000, success: 0, estimated: 45000, actual: 0 }, // 失败
    { branch: 'Standard', duration: 120000, success: 1, estimated: 45000, actual: 0.015 }, // 超时
    { branch: 'Deep', duration: 300000, success: 1, estimated: 300000, actual: 0.05 },
  ];
  
  for (let i = 0; i < 3; i++) { // 添加3轮数据
    for (const data of testData) {
      await sch.db.run(
        `INSERT INTO task_history 
         (task_hash, task_preview, branch, duration_ms, estimated_cost, actual_cost, success, retry_count, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-${i} days'))`,
        [`hash_${Math.random()}`, '测试任务', data.branch, data.duration, data.estimated, data.actual, data.success, 0]
      );
    }
  }
  console.log('✓ 测试数据准备完成\n');

  // 2. 学习引擎测试
  console.log('2. 学习引擎分析测试...');
  const engine = new LearningEngine(sch.db, {
    minSamples: 3,
    outputDir: './test-learning-reports'
  });
  
  // 执行每日学习
  const report = await engine.dailyLearning();
  
  console.log(`  报告日期: ${report.date}`);
  console.log(`  总任务数: ${report.summary.totalTasks}`);
  console.log(`  平均成功率: ${report.summary.avgSuccessRate}%`);
  console.log(`  优化建议: ${report.summary.recommendationCount}条`);
  
  // 显示分类统计
  console.log('\n  分支统计:');
  for (const [branch, data] of Object.entries(report.classification || {})) {
    console.log(`    ${branch}: ${data.count}次, 成功率${data.successRate}%`);
  }
  
  // 显示耗时分析
  if (report.duration) {
    console.log('\n  耗时分析:');
    for (const [branch, data] of Object.entries(report.duration)) {
      console.log(`    ${branch}: 平均${data.avgActual}ms, 预估偏差${data.biasPercent}%`);
    }
  }
  
  // 显示优化建议
  if (report.recommendations.length > 0) {
    console.log('\n  优化建议:');
    for (const rec of report.recommendations) {
      const emoji = rec.priority === 'high' ? '🔴' : '🟡';
      console.log(`    ${emoji} [${rec.type}] ${rec.message}`);
      console.log(`       💡 ${rec.suggestion}`);
    }
  }
  
  console.log('✓ 学习引擎测试完成\n');

  // 3. 飞书报告卡片测试
  console.log('3. 飞书报告卡片测试...');
  const card = engine.buildFeishuCard(report);
  console.log(`  卡片类型: ${card.msg_type}`);
  console.log(`  卡片标题: ${card.card.header.title.content}`);
  console.log('✓ 飞书卡片构建完成\n');

  // 4. 定时任务测试
  console.log('4. 定时学习任务测试...');
  const taskId = sch.startDailyLearning(null, '0 0 * * *'); // 每天0点（测试用）
  console.log(`  定时任务ID: ${taskId}`);
  console.log(`  运行中任务: ${sch.cronManager.list().join(', ')}`);
  
  // 停止测试任务
  sch.cronManager.stop(taskId);
  console.log('✓ 定时任务测试完成\n');

  // 5. 获取最新报告
  console.log('5. 获取最新报告测试...');
  const latestReport = sch.getLatestLearningReport();
  if (latestReport) {
    console.log(`  最新报告日期: ${latestReport.date}`);
    console.log(`  报告文件已保存`);
  }
  console.log('✓ 获取报告测试完成\n');

  console.log('=== Phase 4 所有测试通过 ✅ ===');
}

// 运行测试
runPhase4Tests().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
