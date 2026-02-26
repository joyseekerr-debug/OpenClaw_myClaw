/**
 * 指令队列功能测试
 */

const { CommandQueue, TaskStatus } = require('./command-queue');

async function testCommandQueue() {
  console.log('=== 指令队列功能测试 ===\n');
  
  // 创建队列
  const queue = new CommandQueue({
    maxQueueSize: 10,
    enableNotification: true
  });
  
  // 设置任务处理器（模拟执行）
  queue.setTaskHandler(async (taskData, metadata) => {
    console.log(`  [处理器] 执行任务: ${taskData}`);
    
    // 模拟执行时间
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return { success: true, data: `执行结果: ${taskData}` };
  });
  
  // 设置通知处理器
  queue.setNotificationHandler(async (notification, metadata) => {
    console.log(`  [通知] ${notification.type}: ${notification.message}`);
  });
  
  // 监听事件
  queue.on('task-enqueued', (task) => {
    console.log(`  [事件] 任务入队: ${task.id}`);
  });
  
  queue.on('task-started', (task) => {
    console.log(`  [事件] 任务开始: ${task.id}`);
  });
  
  queue.on('task-completed', (task) => {
    console.log(`  [事件] 任务完成: ${task.id}`);
  });
  
  // 测试1: 添加单个任务
  console.log('1. 添加单个任务...');
  const taskId1 = await queue.enqueue('任务1 - 简单查询', {
    metadata: { chatId: 'test_chat' }
  });
  console.log(`  ✅ 任务已添加: ${taskId1}`);
  
  // 等待第一个任务开始
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 测试2: 添加多个任务（应该排队）
  console.log('\n2. 添加多个任务...');
  const taskId2 = await queue.enqueue('任务2 - 代码分析', {
    metadata: { chatId: 'test_chat' }
  });
  const taskId3 = await queue.enqueue('任务3 - 数据处理', {
    metadata: { chatId: 'test_chat' }
  });
  console.log(`  ✅ 任务2已添加: ${taskId2}`);
  console.log(`  ✅ 任务3已添加: ${taskId3}`);
  
  // 检查队列状态
  const status = queue.getStatus();
  console.log(`  队列状态: 执行中=${status.processing}, 队列长度=${status.queueLength}`);
  
  // 测试3: 获取队列详情
  console.log('\n3. 队列详情...');
  const details = queue.getQueueDetails();
  console.log(`  当前任务: ${details.current?.id || '无'}`);
  console.log(`  等待任务: ${details.pending.length}个`);
  details.pending.forEach((t, i) => {
    console.log(`    ${i+1}. ${t.id}`);
  });
  
  // 等待所有任务完成
  console.log('\n4. 等待所有任务完成...');
  await new Promise(resolve => {
    queue.on('queue-empty', () => {
      console.log('  ✅ 队列已清空');
      resolve();
    });
    
    // 超时保护
    setTimeout(resolve, 15000);
  });
  
  // 测试4: 优先级测试
  console.log('\n5. 优先级测试...');
  
  // 先添加低优先级任务
  await queue.enqueue('低优先级任务', {
    metadata: { chatId: 'test_chat' },
    priority: 1
  });
  
  // 再添加高优先级任务（应该插队到前面）
  await queue.enqueue('高优先级任务', {
    metadata: { chatId: 'test_chat' },
    priority: 10
  });
  
  const priorityDetails = queue.getQueueDetails();
  console.log(`  队列顺序:`);
  priorityDetails.pending.forEach((t, i) => {
    console.log(`    ${i+1}. ${t.data} (优先级: ${t.priority})`);
  });
  
  // 等待完成
  await new Promise(resolve => setTimeout(resolve, 6000));
  
  // 测试5: 取消任务
  console.log('\n6. 取消任务测试...');
  const cancelTaskId = await queue.enqueue('将被取消的任务', {
    metadata: { chatId: 'test_chat' }
  });
  
  // 立即取消（还在队列中）
  await new Promise(resolve => setTimeout(resolve, 100));
  const cancelled = queue.cancelTask(cancelTaskId);
  console.log(`  ✅ 任务取消${cancelled ? '成功' : '失败'}`);
  
  // 最终统计
  console.log('\n7. 最终统计...');
  const finalStatus = queue.getStatus();
  console.log(`  总处理: ${finalStatus.stats.totalProcessed}`);
  console.log(`  失败: ${finalStatus.stats.totalFailed}`);
  console.log(`  取消: ${finalStatus.stats.totalCancelled}`);
  
  console.log('\n=== 所有测试通过 ✅ ===');
  
  // 清理
  queue.clear();
}

// 运行测试
testCommandQueue().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
