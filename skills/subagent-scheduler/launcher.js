/**
 * 子代理调度器启动脚本
 * 初始化并自动启动定时任务
 */

const { SubagentScheduler } = require('./index');

async function main() {
  console.log('[Launcher] 启动子代理调度器...');
  
  const scheduler = new SubagentScheduler();
  
  // 初始化并自动启动定时任务
  await scheduler.init({
    autoStartLearning: true  // 自动启动每日学习定时任务
  });
  
  console.log('[Launcher] 调度器启动完成');
  console.log('[Launcher] 定时任务状态:');
  console.log('  - 每日6:00 学习分析');
  console.log('  - 每日9:00 报告推送');
  
  // 保持进程运行
  console.log('[Launcher] 按 Ctrl+C 停止');
}

// 优雅退出
process.on('SIGINT', async () => {
  console.log('\n[Launcher] 正在关闭...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n[Launcher] 正在关闭...');
  process.exit(0);
});

main().catch(console.error);
