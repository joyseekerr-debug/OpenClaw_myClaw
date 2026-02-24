const fs = require('fs');
const path = require('path');

console.log('=== Phase 1 全面验证报告 ===\n');

// 1. 文件完整性检查
console.log('【1. 文件完整性检查】');
const checks = [
  { name: '核心调度器', file: 'scheduler.js', required: true },
  { name: '数据库模块', file: 'database.js', required: true },
  { name: '飞书交互', file: 'feishu.js', required: true },
  { name: '主入口', file: 'index.js', required: true },
  { name: '重试执行器', file: 'retry-executor.js', required: true },
  { name: 'Cron管理器', file: 'cron-manager.js', required: true },
  { name: '成本监控', file: 'cost-monitor.js', required: true },
  { name: '配置文件', file: 'config.json', required: true },
  { name: '数据库Schema', file: 'schema.sql', required: true },
  { name: '飞书回调', file: 'feishu-callback.js', required: false },
  { name: '并发控制', file: 'redis-concurrency.js', required: false },
  { name: '适配器', file: 'subagent-adapter.js', required: false }
];

let passed = 0;
let failed = 0;

for (const check of checks) {
  const exists = fs.existsSync(check.file);
  const status = exists ? '✅' : (check.required ? '❌' : '⚠️');
  const level = exists ? 'OK' : (check.required ? '缺失' : '可选缺失');
  console.log(`${status} ${check.name}: ${check.file} [${level}]`);
  
  if (exists) passed++;
  else if (check.required) failed++;
}

console.log(`\n文件检查: ${passed}/${checks.length} 通过`);

// 2. 模块加载测试
console.log('\n【2. 模块加载测试】');
const modules = [
  'scheduler', 'database', 'feishu', 'index', 'retry-executor', 
  'cron-manager', 'cost-monitor'
];

for (const mod of modules) {
  try {
    require(`./${mod}`);
    console.log(`✅ ${mod}: 加载成功`);
  } catch (e) {
    console.log(`❌ ${mod}: ${e.message}`);
  }
}

// 3. 配置文件验证
console.log('\n【3. 配置文件验证】');
try {
  const config = require('./config.json');
  const requiredKeys = ['branches', 'costLimits', 'confirmation', 'model'];
  for (const key of requiredKeys) {
    if (config[key]) {
      console.log(`✅ ${key}: 已配置`);
    } else {
      console.log(`❌ ${key}: 缺失`);
    }
  }
  
  // 检查分支配置
  const branches = ['Simple', 'Standard', 'Batch', 'Orchestrator', 'Deep'];
  console.log('\n分支配置:');
  for (const b of branches) {
    if (config.branches[b]) {
      console.log(`  ✅ ${b}`);
    } else {
      console.log(`  ❌ ${b}: 缺失`);
    }
  }
} catch (e) {
  console.log(`❌ 配置文件错误: ${e.message}`);
}

console.log('\n【4. 功能测试】');
console.log('运行 test.js 进行功能测试...');
