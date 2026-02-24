const scheduler = require('./scheduler');

// 测试更长的深度任务
const tasks = [
  {
    name: '深度长文本',
    task: '深度分析整个代码库并给出架构建议。这是一段很长的任务描述，包含很多字，超过200个字符的限制，这样才能触发Deep分支。让我们添加更多内容来确保长度足够，达到阈值要求。这是一些额外的填充内容，继续添加更多文字使其超过200字符的限制。'
  },
  {
    name: '标准分析',
    task: '分析这个日志文件找出错误模式并生成详细报告'
  },
  {
    name: '批量任务',
    task: '批量处理所有配置文件'
  },
  {
    name: '流程任务',
    task: '先获取数据然后分析最后生成报告'
  }
];

async function runTest() {
  console.log('=== 任务分类边界测试 ===\n');

  for (const t of tasks) {
    const result = await scheduler.classifyTask(t.task);
    console.log(`${t.name}:`);
    console.log(`  长度: ${t.task.length}`);
    console.log(`  分支: ${result.branch}`);
    console.log(`  置信度: ${result.confidence}`);
    console.log(`  原因: ${result.reason}`);
    console.log('');
  }
}

runTest();
