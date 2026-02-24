/**
 * 试探执行引擎
 * 启动后监控前N秒执行状态，动态调整策略
 */

const EventEmitter = require('events');

/**
 * 试探执行管理器
 */
class ProbeExecutor extends EventEmitter {
  constructor(options = {}) {
    super();
    this.probeDuration = options.probeDuration || 15000; // 15秒试探期
    this.checkInterval = options.checkInterval || 3000;  // 每3秒检查
    this.progressThreshold = options.progressThreshold || 0.2; // 20%进度阈值
    this.stallThreshold = options.stallThreshold || 5000; // 5秒无进展视为卡住
  }

  /**
   * 执行带试探的任务
   * @param {Function} taskFn - 实际执行函数
   * @param {Object} options - 配置
   */
  async execute(taskFn, options = {}) {
    const startTime = Date.now();
    const taskId = options.taskId || `probe_${Date.now()}`;
    const initialBranch = options.branch || 'Standard';
    
    // 初始化试探状态
    const probeState = {
      taskId,
      branch: initialBranch,
      startTime,
      checks: [],
      progressHistory: [],
      status: 'probing',
      decision: null
    };

    this.emit('probe-started', { taskId, branch: initialBranch });

    // 启动试探监控
    const probeInterval = setInterval(() => {
      this.checkProgress(probeState);
    }, this.checkInterval);

    // 设置试探结束定时器
    const probeTimer = setTimeout(() => {
      this.finalizeProbe(probeState);
    }, this.probeDuration);

    try {
      // 实际执行任务
      const result = await taskFn({
        ...options,
        probeMode: true,
        onProgress: (progress) => {
          probeState.progressHistory.push({
            timestamp: Date.now(),
            progress,
            elapsed: Date.now() - startTime
          });
          this.emit('progress', { taskId, progress, elapsed: Date.now() - startTime });
        }
      });

      // 任务在试探期内完成
      clearInterval(probeInterval);
      clearTimeout(probeTimer);
      
      probeState.status = 'completed';
      probeState.decision = 'continue';
      
      this.emit('probe-completed', {
        taskId,
        actualDuration: Date.now() - startTime,
        branch: probeState.branch
      });

      return {
        success: true,
        result,
        probe: probeState,
        adjusted: false
      };

    } catch (error) {
      clearInterval(probeInterval);
      clearTimeout(probeTimer);
      
      probeState.status = 'error';
      probeState.error = error;
      
      this.emit('probe-error', { taskId, error });
      
      // 检查是否需要调整策略
      const adjustment = this.analyzeForAdjustment(probeState, error);
      
      if (adjustment.shouldAdjust) {
        this.emit('strategy-adjusted', {
          taskId,
          from: initialBranch,
          to: adjustment.targetBranch,
          reason: adjustment.reason
        });
        
        return {
          success: false,
          error,
          probe: probeState,
          adjusted: true,
          adjustment
        };
      }

      throw error;
    }
  }

  /**
   * 检查进度状态
   */
  checkProgress(state) {
    const elapsed = Date.now() - state.startTime;
    const recentProgress = state.progressHistory.slice(-3);
    
    // 检查是否卡住
    if (recentProgress.length >= 2) {
      const last = recentProgress[recentProgress.length - 1];
      const first = recentProgress[0];
      const timeDiff = last.timestamp - first.timestamp;
      const progressDiff = last.progress - first.progress;
      
      if (timeDiff > this.stallThreshold && progressDiff < 0.05) {
        // 卡住检测
        state.status = 'stalled';
        state.decision = 'upgrade';
        
        this.emit('stall-detected', {
          taskId: state.taskId,
          elapsed,
          progress: last.progress,
          reason: `${timeDiff}ms内进度仅增加${(progressDiff * 100).toFixed(1)}%`
        });
      }
    }

    // 记录检查点
    state.checks.push({
      timestamp: Date.now(),
      elapsed,
      progress: recentProgress.length > 0 ? recentProgress[recentProgress.length - 1].progress : 0,
      status: state.status
    });
  }

  /**
   * 结束试探期，做出决策
   */
  finalizeProbe(state) {
    if (state.status === 'completed' || state.status === 'error') {
      return;
    }

    const elapsed = Date.now() - state.startTime;
    const lastProgress = state.progressHistory.length > 0
      ? state.progressHistory[state.progressHistory.length - 1].progress
      : 0;

    // 基于进度判断是否升级/降级
    const expectedProgress = elapsed / this.probeDuration * 0.5; // 期望完成50%
    
    if (lastProgress < expectedProgress * 0.5) {
      // 进度严重落后，可能需要升级
      state.decision = 'upgrade';
      state.reason = `进度${(lastProgress * 100).toFixed(1)}%远低于预期${(expectedProgress * 100).toFixed(1)}%`;
    } else if (lastProgress > expectedProgress * 1.5) {
      // 进度超前，可以降级节省资源
      state.decision = 'downgrade';
      state.reason = `进度${(lastProgress * 100).toFixed(1)}%远超预期，任务比预计简单`;
    } else {
      state.decision = 'continue';
      state.reason = '进度正常，维持当前策略';
    }

    state.status = 'decided';
    
    this.emit('probe-decided', {
      taskId: state.taskId,
      decision: state.decision,
      reason: state.reason,
      progress: lastProgress,
      elapsed
    });
  }

  /**
   * 分析错误，判断是否需要策略调整
   */
  analyzeForAdjustment(state, error) {
    const errorMessage = error.message || String(error);
    
    // 超时错误 - 升级到更强大的策略
    if (/timeout|timed out|deadline exceeded/i.test(errorMessage)) {
      return {
        shouldAdjust: true,
        targetBranch: this.getUpgradedBranch(state.branch),
        reason: '超时错误，需要更多资源',
        action: 'upgrade'
      };
    }
    
    // 资源不足 - 升级或调整
    if (/memory|out of memory|resource exhausted/i.test(errorMessage)) {
      return {
        shouldAdjust: true,
        targetBranch: this.getUpgradedBranch(state.branch),
        reason: '资源不足，需要更强大的策略',
        action: 'upgrade'
      };
    }
    
    // 执行过快完成 - 降级节省成本
    if (state.progressHistory.length > 0) {
      const actualDuration = Date.now() - state.startTime;
      const firstProgress = state.progressHistory[0];
      
      if (firstProgress.progress > 0.5 && actualDuration < 5000) {
        return {
          shouldAdjust: true,
          targetBranch: this.getDowngradedBranch(state.branch),
          reason: '任务执行过快，可以降级节省成本',
          action: 'downgrade'
        };
      }
    }
    
    return { shouldAdjust: false };
  }

  /**
   * 获取升级后的分支
   */
  getUpgradedBranch(current) {
    const upgradeMap = {
      'Simple': 'Standard',
      'Standard': 'Deep',
      'Batch': 'Orchestrator',
      'Orchestrator': 'Deep',
      'Deep': 'Deep' // 最高级，保持不变
    };
    return upgradeMap[current] || current;
  }

  /**
   * 获取降级后的分支
   */
  getDowngradedBranch(current) {
    const downgradeMap = {
      'Deep': 'Orchestrator',
      'Orchestrator': 'Batch',
      'Batch': 'Standard',
      'Standard': 'Simple',
      'Simple': 'Simple' // 最低级，保持不变
    };
    return downgradeMap[current] || current;
  }

  /**
   * 快速试探模式（简化版）
   * 用于快速判断是否需要调整策略
   */
  async quickProbe(taskFn, options = {}) {
    const probeTime = options.quickProbeTime || 5000; // 5秒快速试探
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        resolve({
          canContinue: true,
          recommendation: 'continue',
          reason: '快速试探通过'
        });
      }, probeTime);

      taskFn(options)
        .then(result => {
          clearTimeout(timeout);
          resolve({
            canContinue: true,
            completed: true,
            result,
            recommendation: 'completed',
            reason: '任务在试探期内完成'
          });
        })
        .catch(error => {
          clearTimeout(timeout);
          
          // 分析错误
          const errorMsg = error.message || String(error);
          if (/timeout|memory|resource/i.test(errorMsg)) {
            resolve({
              canContinue: false,
              recommendation: 'upgrade',
              error,
              reason: '资源或超时错误，建议升级策略'
            });
          } else {
            reject(error);
          }
        });
    });
  }
}

module.exports = {
  ProbeExecutor
};
