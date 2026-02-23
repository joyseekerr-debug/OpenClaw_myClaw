/**
 * 成本监控器
 * 结合预估和实际查询进行成本监控
 */

const EventEmitter = require('events');

class CostMonitor extends EventEmitter {
  constructor(db, options = {}) {
    super();
    this.db = db;
    this.budget = options.budget || {
      perTask: 1.0,
      perSession: 10.0,
      perDay: 50.0
    };
    this.alertThreshold = options.alertThreshold || 0.8;
    this.currentSessionCost = 0;
  }

  /**
   * 预估任务成本
   */
  estimateCost(branch, taskLength) {
    const baseRates = {
      'Simple': { input: 0.001, output: 0.003, time: 5 },
      'Standard': { input: 0.001, output: 0.003, time: 45 },
      'Batch': { input: 0.001, output: 0.003, time: 80 },
      'Orchestrator': { input: 0.002, output: 0.006, time: 120 },
      'Deep': { input: 0.002, output: 0.006, time: 300 }
    };
    
    const rate = baseRates[branch] || baseRates['Standard'];
    const estimatedInput = Math.min(taskLength * 2, 8000);
    const estimatedOutput = estimatedInput * (branch === 'Deep' ? 1.5 : 0.8);
    
    // 基于历史数据调整预估
    const historicalAdjustment = this.getHistoricalAdjustment(branch);
    
    return {
      input: estimatedInput,
      output: estimatedOutput,
      total: (estimatedInput * rate.input + estimatedOutput * rate.output) / 1000 * historicalAdjustment,
      estimatedTime: rate.time,
      confidence: historicalAdjustment > 1.0 ? 'high' : 'medium'
    };
  }

  /**
   * 基于历史数据调整预估
   */
  getHistoricalAdjustment(branch) {
    if (!this.db) return 1.0;
    
    try {
      const history = this.db.query(
        `SELECT AVG(actual_cost / estimated_cost) as ratio
         FROM task_history
         WHERE branch = ? AND success = 1
         AND created_at > datetime('now', '-7 days')`,
        [branch]
      );
      
      if (history && history[0] && history[0].ratio) {
        return Math.max(0.8, Math.min(1.5, history[0].ratio));
      }
    } catch (e) {
      console.error('[CostMonitor] 历史查询失败:', e.message);
    }
    
    return 1.1; // 默认10%缓冲
  }

  /**
   * 检查预算
   */
  async checkBudget(estimatedCost) {
    const checks = {
      perTask: estimatedCost <= this.budget.perTask,
      perSession: (this.currentSessionCost + estimatedCost) <= this.budget.perSession,
      perDay: await this.checkDailyBudget(estimatedCost)
    };
    
    const passed = checks.perTask && checks.perSession && checks.perDay;
    
    if (!passed) {
      const reasons = [];
      if (!checks.perTask) reasons.push(`单次任务预算超限($${this.budget.perTask})`);
      if (!checks.perSession) reasons.push(`会话预算超限($${this.budget.perSession})`);
      if (!checks.perDay) reasons.push(`日预算超限($${this.budget.perDay})`);
      
      return { allowed: false, reasons };
    }
    
    // 检查是否接近阈值
    const warnings = [];
    if (estimatedCost > this.budget.perTask * this.alertThreshold) {
      warnings.push(`预估成本接近单次预算阈值(${(this.alertThreshold * 100).toFixed(0)}%)`);
    }
    
    return { allowed: true, warnings };
  }

  /**
   * 检查日预算
   */
  async checkDailyBudget(estimatedCost) {
    if (!this.db) return true;
    
    try {
      const result = this.db.query(
        `SELECT SUM(actual_cost) as total
         FROM task_history
         WHERE created_at > datetime('now', '-1 day')`
      );
      
      const todayCost = result[0]?.total || 0;
      return (todayCost + estimatedCost) <= this.budget.perDay;
    } catch (e) {
      return true;
    }
  }

  /**
   * 记录实际成本
   */
  recordActualCost(cost) {
    this.currentSessionCost += cost;
    
    // 检查是否需要告警
    if (this.currentSessionCost > this.budget.perSession * this.alertThreshold) {
      this.emit('warning', {
        type: 'session_budget',
        message: `会话成本已达 $${this.currentSessionCost.toFixed(4)}, 接近预算上限`,
        current: this.currentSessionCost,
        limit: this.budget.perSession
      });
    }
  }

  /**
   * 实时监控（模拟）
   * 实际应从子代理获取token使用量
   */
  startRealtimeMonitor(taskId, checkInterval = 10) {
    let estimatedTotal = 0;
    
    const interval = setInterval(async () => {
      // 模拟获取实时数据
      // 实际应调用API获取子代理当前token使用量
      const progress = await this.getTaskProgress(taskId);
      
      if (progress.completed) {
        clearInterval(interval);
        this.recordActualCost(progress.actualCost);
        this.emit('completed', { taskId, cost: progress.actualCost });
        return;
      }
      
      // 基于进度估算当前成本
      const currentEstimated = progress.estimatedTotal * (progress.percent / 100);
      
      if (currentEstimated > this.budget.perTask * this.alertThreshold) {
        this.emit('alert', {
          taskId,
          message: `任务成本预估已达 $${currentEstimated.toFixed(4)}, 接近预算`,
          percent: progress.percent
        });
      }
    }, checkInterval * 1000);
    
    return interval;
  }

  /**
   * 获取任务进度（模拟）
   */
  async getTaskProgress(taskId) {
    // 实际应从子代理获取
    return {
      percent: 50,
      estimatedTotal: 0.1,
      actualCost: 0.05,
      completed: false
    };
  }

  /**
   * 生成成本报告
   */
  async generateReport() {
    if (!this.db) return null;
    
    return this.db.query(`
      SELECT 
        DATE(created_at) as date,
        branch,
        COUNT(*) as count,
        SUM(actual_cost) as total_cost,
        AVG(actual_cost) as avg_cost
      FROM task_history
      WHERE created_at > datetime('now', '-7 days')
      GROUP BY DATE(created_at), branch
      ORDER BY date DESC
    `);
  }
}

module.exports = {
  CostMonitor
};
