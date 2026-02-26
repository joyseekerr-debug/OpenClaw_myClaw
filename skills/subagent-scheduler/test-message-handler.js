/**
 * 飞书消息处理器测试
 */

const { getMessageHandler, resetMessageHandler } = require('./feishu-message-handler');

async function testMessageHandler() {
  console.log('=== 飞书消息处理器测试 ===\n');
  
  // 获取处理器（自动启用队列）
  const handler = getMessageHandler();
  
  console.log('1. 处理器已启动，测试消息入队...\n');
  
  // 模拟用户消息
  const testMessages = [
    { text: '查询今天的天气', chatId: 'test_chat' },
    { text: '分析一下小米股票', chatId: 'test_chat' },
    { text: '紧急：帮我看看这个错误', chatId: 'test_chat', priority: 10 }
  ];
  
  for (const msg of testMessages) {
    console.log(`发送: "${msg.text}"`);
    
    const result = await handler.handleMessage(msg.text, msg.chatId, {
      userId: 'test_user',
      userName: '测试用户'
    });
    
    console.log(`  任务ID: ${result.taskId}`);
    console.log(`  优先级: ${result.priority}`);
    console.log(`  队列长度: ${result.status.queueLength}`);
    console.log('');
  }
  
  // 检查队列状态
  console.log('2. 队列状态...');
  const status = handler.getStatus();
  console.log(`  正在执行: ${status.processing ? '是' : '否'}`);
  console.log(`  队列长度: ${status.queueLength}`);
  console.log(`  已处理: ${status.stats.totalProcessed}`);
  
  // 检查队列详情
  console.log('\n3. 队列详情...');
  const details = handler.getQueueDetails();
  console.log(`  当前任务: ${details.current?.data || '无'}`);
  console.log(`  等待任务:`);
  details.pending.forEach((task, i) => {
    console.log(`    ${i+1}. ${task.data} (优先级: ${task.priority})`);
  });
  
  console.log('\n=== 测试完成 ✅ ===');
  console.log('\n飞书消息队列已启用，所有消息将自动排队执行。');
  
  // 清理
  await handler.close();
  resetMessageHandler();
}

// 运行测试
testMessageHandler().catch(console.error);
