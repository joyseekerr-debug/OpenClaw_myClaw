/**
 * 自适应学习引擎
 * 每日分析历史数据，自动优化系统参数
 */

const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');

/**
 * 学习引擎
 */
class LearningEngine extends EventEmitter {
  constructor(db, options = {}) {
    super();
    this.db = db;
    this.outputDir = options.outputDir || './learning-reports';
    this.minSamples = options.minSamples || 5; // 最小样本数才进行优化
    this.adjustmentThreshold = options.adjustmentThreshold || 0.1; // 10%差异才调整
    
    // 当前优化建议
    this.recommendations = [];
    this.adjustments = [];
    
    // 确保输出目录存在
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * 执行每日学习（仅分析，不发送报告）
   */
  async dailyLearning() {
    const date = new Date().toISOString().split('T')[0];
    console.log(`[LearningEngine] 开始每日学习: ${date}`);
    
    this.emit('learning-started', { date });
    
    // 1. 分析分类准确率
    const classificationAnalysis = await this.analyzeClassificationAccuracy();
    
    // 2. 分析耗时分布
    const durationAnalysis = await this.analyzeDurationDistribution();
    
    // 3. 分析成本预估准确性
    const costAnalysis = await this.analyzeCostAccuracy();
    
    // 4. 分析分支成功率
    const branchAnalysis = await this.analyzeBranchSuccessRate();
    
    // 5. 生成优化建议
    this.generateRecommendations({
      classification: classificationAnalysis,
      duration: durationAnalysis,
      cost: costAnalysis,
      branch: branchAnalysis
    });
    
    // 6. 生成报告
    const report = this.generateReport(date, {
      classification: classificationAnalysis,
      duration: durationAnalysis,
      cost: costAnalysis,
      branch: branchAnalysis
    });
    
    // 7. 保存报告
    this.saveReport(date, report);
    
    // 8. 应用自动调整
    const adjustments = this.applyAutoAdjustments();
    
    this.emit('learning-completed', {
      date,
      report,
      adjustments
    });
    
    return report;
  }

  /**
   * 发送报告（单独调用，用于定时推送）
   * @param {string} date - 报告日期，默认为最新
   * @param {Function} feishuSender - 飞书发送函数
   */
  async sendReport(date = null, feishuSender) {
    let report;
    
    if (date) {
      // 加载指定日期的报告
      const filepath = path.join(this.outputDir, `learning-report-${date}.json`);
      if (fs.existsSync(filepath)) {
        report = JSON.parse(fs.readFileSync(filepath, 'utf-8'));
      } else {
        throw new Error(`未找到 ${date} 的报告`);
      }
    } else {
      // 获取最新报告
      report = this.getLatestReport();
    }
    
    if (!report) {
      throw new Error('没有可用的报告');
    }
    
    if (!feishuSender) {
      throw new Error('需要提供飞书发送函数');
    }
    
    const card = this.buildFeishuCard(report);
    await feishuSender(card);
    
    this.emit('report-sent', { date: report.date });
    
    return { sent: true, date: report.date };
  }

  /**
   * 分析分类准确率
   */
  async analyzeClassificationAccuracy() {
    // 查询最近7天的数据
    const rows = await this.db.query(`
      SELECT 
        branch,
        COUNT(*) as count,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
        AVG(duration_ms) as avg_duration,
        AVG(ABS(actual_cost - estimated_cost)) as cost_diff
      FROM task_history
      WHERE created_at > datetime('now', '-7 days')
      GROUP BY branch
    `);
    
    const analysis = {};
    
    for (const row of rows || []) {
      const successRate = row.count > 0 ? (row.success_count / row.count * 100).toFixed(1) : 0;
      
      analysis[row.branch] = {
        count: row.count,
        successRate: parseFloat(successRate),
        avgDuration: Math.round(row.avg_duration || 0),
        costAccuracy: row.cost_diff || 0
      };
    }
    
    // 检测分类问题
    const issues = [];
    
    // 如果Standard分支成功率很低，可能是被误判的任务
    if (analysis.Standard && analysis.Standard.successRate < 70) {
      issues.push({
        type: 'misclassification',
        branch: 'Standard',
        message: `Standard分支成功率仅${analysis.Standard.successRate}%，可能有任务被误判为Standard`,
        suggestion: '降低Simple分支的置信度阈值，让更多任务使用更高层级策略'
      });
    }
    
    // 如果Deep分支成功率很高但数量少，说明识别准确
    if (analysis.Deep && analysis.Deep.successRate > 90 && analysis.Deep.count < 5) {
      issues.push({
        type: 'underutilization',
        branch: 'Deep',
        message: 'Deep分支成功率很高但使用率低',
        suggestion: '考虑降低Deep分支触发条件，让更多复杂任务使用'
      });
    }
    
    return {
      branches: analysis,
      issues,
      overall: {
        totalTasks: Object.values(analysis).reduce((sum, b) => sum + b.count, 0),
        avgSuccessRate: Object.values(analysis).reduce((sum, b) => sum + b.successRate * b.count, 0) / 
                       Object.values(analysis).reduce((sum, b) => sum + b.count, 0) || 0
      }
    };
  }

  /**
   * 分析耗时分布
   */
  async analyzeDurationDistribution() {
    const rows = await this.db.query(`
      SELECT 
        branch,
        duration_ms
      FROM task_history
      WHERE created_at > datetime('now', '-7 days')
        AND success = 1
      ORDER BY branch, duration_ms
    `);
    
    const distributions = {};
    
    // 按分支分组
    for (const row of rows || []) {
      if (!distributions[row.branch]) {
        distributions[row.branch] = [];
      }
      distributions[row.branch].push(row.duration_ms);
    }
    
    const analysis = {};
    
    for (const [branch, durations] of Object.entries(distributions)) {
      if (durations.length < this.minSamples) continue;
      
      durations.sort((a, b) => a - b);
      const median = durations[Math.floor(durations.length / 2)];
      const p90 = durations[Math.floor(durations.length * 0.9)];
      const p95 = durations[Math.floor(durations.length * 0.95)];
      const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
      
      // 获取默认预期值
      const expectedDuration = this.getExpectedDuration(branch);
      const bias = avg - expectedDuration;
      
      analysis[branch] = {
        count: durations.length,
        median: median,
        p90: p90,
        p95: p95,
        avgActual: Math.round(avg),
        avgEstimated: expectedDuration,
        bias: Math.round(bias),
        biasPercent: expectedDuration > 0 ? Math.round(bias / expectedDuration * 100) : 0
      };
    }
    
    return analysis;
  }

  /**
   * 获取预期耗时
   */
  getExpectedDuration(branch) {
    const durations = {
      'Simple': 5000,
      'Standard': 45000,
      'Batch': 80000,
      'Orchestrator': 120000,
      'Deep': 300000
    };
    return durations[branch] || 60000;
  }

  /**
   * 分析成本预估准确性
   */
  async analyzeCostAccuracy() {
    const rows = await this.db.query(`
      SELECT 
        branch,
        estimated_cost,
        actual_cost
      FROM task_history
      WHERE created_at > datetime('now', '-7 days')
        AND success = 1
        AND actual_cost IS NOT NULL
    `);
    
    const accuracyByBranch = {};
    
    for (const row of rows || []) {
      if (!accuracyByBranch[row.branch]) {
        accuracyByBranch[row.branch] = { errors: [], count: 0 };
      }
      
      const error = Math.abs(row.actual_cost - row.estimated_cost);
      const errorPercent = row.estimated_cost > 0 ? error / row.estimated_cost : 0;
      
      accuracyByBranch[row.branch].errors.push(errorPercent);
      accuracyByBranch[row.branch].count++;
    }
    
    const analysis = {};
    
    for (const [branch, data] of Object.entries(accuracyByBranch)) {
      if (data.count < this.minSamples) continue;
      
      const avgError = data.errors.reduce((a, b) => a + b, 0) / data.errors.length;
      
      analysis[branch] = {
        count: data.count,
        avgErrorPercent: (avgError * 100).toFixed(1),
        mape: (avgError * 100).toFixed(1) // Mean Absolute Percentage Error
      };
    }
    
    return analysis;
  }

  /**
   * 分析分支成功率
   */
  async analyzeBranchSuccessRate() {
    const rows = await this.db.query(`
      SELECT 
        branch,
        COUNT(*) as total,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
        AVG(retry_count) as avg_retries
      FROM task_history
      WHERE created_at > datetime('now', '-7 days')
      GROUP BY branch
    `);
    
    const analysis = {};
    
    for (const row of rows || []) {
      const rate = row.total > 0 ? (row.success / row.total * 100).toFixed(1) : 0;
      
      analysis[row.branch] = {
        total: row.total,
        success: row.success,
        failed: row.total - row.success,
        successRate: parseFloat(rate),
        avgRetries: (row.avg_retries || 0).toFixed(2)
      };
    }
    
    return analysis;
  }

  /**
   * 生成优化建议
   */
  generateRecommendations(analyses) {
    this.recommendations = [];
    
    const { classification, duration, cost, branch } = analyses;
    
    // 1. 分类建议
    for (const issue of classification.issues || []) {
      this.recommendations.push({
        type: 'classification',
        priority: issue.type === 'misclassification' ? 'high' : 'medium',
        message: issue.message,
        suggestion: issue.suggestion,
        autoApplicable: false // 需要人工确认
      });
    }
    
    // 2. 超时建议
    for (const [branchName, data] of Object.entries(duration)) {
      if (data.biasPercent > 20) {
        // 实际耗时远超预估
        this.recommendations.push({
          type: 'timeout',
          branch: branchName,
          priority: 'high',
          message: `${branchName}分支实际耗时比预估高${data.biasPercent}%`,
          suggestion: `建议将${branchName}的超时时间从${data.avgEstimated}ms调整为${Math.round(data.avgActual * 1.2)}ms`,
          currentValue: data.avgEstimated,
          suggestedValue: Math.round(data.avgActual * 1.2),
          autoApplicable: true
        });
      }
    }
    
    // 3. 成本预估建议
    for (const [branchName, data] of Object.entries(cost)) {
      if (parseFloat(data.mape) > 30) {
        this.recommendations.push({
          type: 'cost',
          branch: branchName,
          priority: 'medium',
          message: `${branchName}分支成本预估误差${data.mape}%过高`,
          suggestion: '需要校准成本预估模型参数',
          autoApplicable: false
        });
      }
    }
    
    // 4. 成功率建议
    for (const [branchName, data] of Object.entries(branch)) {
      if (data.successRate < 80) {
        this.recommendations.push({
          type: 'success_rate',
          branch: branchName,
          priority: 'high',
          message: `${branchName}分支成功率仅${data.successRate}%`,
          suggestion: '建议增加重试次数或降级到更稳定的策略',
          autoApplicable: true
        });
      }
    }
    
    // 按优先级排序
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    this.recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
  }

  /**
   * 应用自动调整
   */
  applyAutoAdjustments() {
    this.adjustments = [];
    
    for (const rec of this.recommendations) {
      if (!rec.autoApplicable) continue;
      
      switch (rec.type) {
        case 'timeout':
          // 调整超时时间（实际应更新配置文件）
          this.adjustments.push({
            type: 'timeout',
            branch: rec.branch,
            from: rec.currentValue,
            to: rec.suggestedValue,
            applied: true
          });
          break;
          
        case 'success_rate':
          // 增加重试次数建议
          this.adjustments.push({
            type: 'retry',
            branch: rec.branch,
            suggestion: 'increase',
            applied: false // 需要下次重启生效
          });
          break;
      }
    }
    
    return this.adjustments;
  }

  /**
   * 生成报告
   */
  generateReport(date, analyses) {
    const { classification, duration, cost, branch } = analyses;
    
    return {
      date,
      summary: {
        totalTasks: classification.overall.totalTasks,
        avgSuccessRate: classification.overall.avgSuccessRate.toFixed(1),
        recommendationCount: this.recommendations.length,
        autoAdjustments: this.adjustments.filter(a => a.applied).length
      },
      classification: classification.branches,
      duration,
      cost,
      branchSuccess: branch,
      recommendations: this.recommendations,
      adjustments: this.adjustments
    };
  }

  /**
   * 保存报告
   */
  saveReport(date, report) {
    const filename = `learning-report-${date}.json`;
    const filepath = path.join(this.outputDir, filename);
    
    fs.writeFileSync(filepath, JSON.stringify(report, null, 2));
    
    return filepath;
  }

  /**
   * 获取最新报告
   */
  getLatestReport() {
    const files = fs.readdirSync(this.outputDir)
      .filter(f => f.startsWith('learning-report-'))
      .sort()
      .reverse();
    
    if (files.length === 0) return null;
    
    const latest = files[0];
    const content = fs.readFileSync(path.join(this.outputDir, latest), 'utf-8');
    return JSON.parse(content);
  }

  /**
   * 构建飞书报告卡片
   */
  buildFeishuCard(report) {
    const elements = [
      {
        tag: 'div',
        text: {
          tag: 'lark_md',
          content: `**📊 每日学习报告 (${report.date})**\n\n` +
                   `总任务数: **${report.summary.totalTasks}**\n` +
                   `平均成功率: **${report.summary.avgSuccessRate}%**\n` +
                   `优化建议: **${report.summary.recommendationCount}**条\n` +
                   `自动调整: **${report.summary.autoAdjustments}**项`
        }
      }
    ];
    
    // 添加建议详情
    if (report.recommendations.length > 0) {
      elements.push({
        tag: 'div',
        text: {
          tag: 'lark_md',
          content: `\n**🎯 优化建议:**`
        }
      });
      
      for (const rec of report.recommendations.slice(0, 5)) {
        const emoji = rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢';
        elements.push({
          tag: 'div',
          text: {
            tag: 'lark_md',
            content: `${emoji} **${rec.type}**: ${rec.message}\n   💡 ${rec.suggestion}`
          }
        });
      }
    }
    
    return {
      msg_type: 'interactive',
      card: {
        config: { wide_screen_mode: true },
        header: {
          title: { tag: 'plain_text', content: '🤖 子代理调度器 - 每日学习报告' },
          template: 'blue'
        },
        elements
      }
    };
  }
}

module.exports = {
  LearningEngine
};
