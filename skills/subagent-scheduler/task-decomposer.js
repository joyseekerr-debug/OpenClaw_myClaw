/**
 * Task Decomposer
 * 任务分解器 - 将复杂任务拆解为可并行执行的子任务 DAG
 */

const EventEmitter = require('events');

/**
 * 任务分解器类
 */
class TaskDecomposer extends EventEmitter {
  constructor(options = {}) {
    super();
    this.maxSubtasks = options.maxSubtasks || 20;
    this.minSubtaskDuration = options.minSubtaskDuration || 5000; // 5秒
  }

  /**
   * 分析任务复杂度，判断是否需要分解
   * @param {string} task 
   * @returns {Object} 复杂度分析
   */
  analyzeComplexity(task) {
    const indicators = {
      length: task.length,
      wordCount: task.split(/\s+/).length,
      hasMultipleSteps: /步骤|阶段|先.*然后|接着|最后/.test(task),
      hasMultipleTargets: /批量|所有|多个|列表/.test(task),
      hasDeepAnalysis: /深度|详细|全面|彻底/.test(task),
      hasDependencies: /依赖|基于|根据.*结果/.test(task),
      estimatedSubtasks: 1
    };
    
    // 估算子任务数量
    let estimatedSubtasks = 1;
    
    if (indicators.hasMultipleSteps) estimatedSubtasks += 2;
    if (indicators.hasMultipleTargets) {
      const match = task.match(/(\d+)/);
      if (match) {
        estimatedSubtasks += Math.min(parseInt(match[1]), 10);
      } else {
        estimatedSubtasks += 3;
      }
    }
    if (indicators.hasDeepAnalysis) estimatedSubtasks += 2;
    if (indicators.hasDependencies) estimatedSubtasks += 1;
    
    indicators.estimatedSubtasks = Math.min(estimatedSubtasks, this.maxSubtasks);
    
    // 复杂度评分
    let score = 0;
    if (indicators.length > 200) score += 2;
    if (indicators.length > 500) score += 3;
    if (indicators.hasMultipleSteps) score += 2;
    if (indicators.hasMultipleTargets) score += 2;
    if (indicators.hasDeepAnalysis) score += 2;
    if (indicators.hasDependencies) score += 1;
    
    indicators.complexityScore = score;
    indicators.shouldDecompose = score >= 3 || estimatedSubtasks > 2;
    
    return indicators;
  }

  /**
   * 分解任务为子任务 DAG
   * @param {string} task 
   * @param {Object} options 
   * @returns {Object} DAG
   */
  async decompose(task, options = {}) {
    const analysis = this.analyzeComplexity(task);
    
    if (!analysis.shouldDecompose) {
      // 不需要分解，返回单节点 DAG
      return {
        taskId: `task_${Date.now()}`,
        originalTask: task,
        complexity: analysis,
        subtasks: [{
          id: 'subtask_1',
          task: task,
          dependsOn: [],
          estimatedDuration: 60000,
          requiredCapabilities: ['read', 'write']
        }],
        parallelGroups: [['subtask_1']],
        totalSubtasks: 1
      };
    }
    
    this.emit('decomposing', { task, complexity: analysis });
    
    // 根据任务类型选择分解策略
    let subtasks;
    
    if (analysis.hasMultipleTargets && task.includes('文件')) {
      subtasks = this.decomposeFileBatchTask(task, analysis);
    } else if (analysis.hasMultipleSteps) {
      subtasks = this.decomposeStepByStepTask(task, analysis);
    } else if (analysis.hasDeepAnalysis) {
      subtasks = this.decomposeAnalysisTask(task, analysis);
    } else {
      subtasks = this.decomposeGenericTask(task, analysis);
    }
    
    // 构建 DAG
    const dag = this.buildDAG(subtasks);
    
    dag.taskId = `task_${Date.now()}`;
    dag.originalTask = task;
    dag.complexity = analysis;
    dag.totalSubtasks = subtasks.length;
    
    this.emit('decomposed', { 
      taskId: dag.taskId, 
      subtaskCount: subtasks.length 
    });
    
    return dag;
  }

  /**
   * 分解批量文件任务
   */
  decomposeFileBatchTask(task, analysis) {
    // 提取文件数量
    const match = task.match(/(\d+)个?.*文件/);
    const fileCount = match ? parseInt(match[1]) : 5;
    
    const subtasks = [];
    
    // 1. 扫描文件
    subtasks.push({
      id: 'scan_files',
      task: '扫描并列出所有目标文件',
      dependsOn: [],
      estimatedDuration: 10000,
      requiredCapabilities: ['read', 'list_files'],
      type: 'scan'
    });
    
    // 2. 并行处理每个文件
    const batchSize = Math.ceil(fileCount / Math.min(fileCount, 5)); // 最多5个并行
    
    for (let i = 0; i < Math.min(fileCount, 10); i++) {
      subtasks.push({
        id: `process_file_${i}`,
        task: `处理第${i + 1}批文件`,
        dependsOn: ['scan_files'],
        estimatedDuration: 30000,
        requiredCapabilities: ['read', 'write', 'analyze'],
        type: 'process',
        batchIndex: i
      });
    }
    
    // 3. 汇总结果
    const processIds = subtasks
      .filter(s => s.type === 'process')
      .map(s => s.id);
    
    subtasks.push({
      id: 'aggregate_results',
      task: '汇总所有文件处理结果',
      dependsOn: processIds,
      estimatedDuration: 15000,
      requiredCapabilities: ['read', 'write', 'aggregate'],
      type: 'aggregate'
    });
    
    return subtasks;
  }

  /**
   * 分解分步骤任务
   */
  decomposeStepByStepTask(task, analysis) {
    const subtasks = [];
    
    // 解析步骤（简化实现）
    const steps = [
      { name: '数据收集', caps: ['read', 'fetch'] },
      { name: '数据清洗', caps: ['read', 'write', 'transform'] },
      { name: '数据分析', caps: ['read', 'analyze'] },
      { name: '结果生成', caps: ['read', 'write', 'generate'] }
    ];
    
    let prevId = null;
    
    steps.forEach((step, index) => {
      const id = `step_${index + 1}`;
      
      subtasks.push({
        id,
        task: `${step.name}: ${task.substring(0, 50)}...`,
        dependsOn: prevId ? [prevId] : [],
        estimatedDuration: 30000,
        requiredCapabilities: step.caps,
        type: 'step',
        stepIndex: index
      });
      
      prevId = id;
    });
    
    return subtasks;
  }

  /**
   * 分解深度分析任务
   */
  decomposeAnalysisTask(task, analysis) {
    const subtasks = [
      {
        id: 'collect_info',
        task: '收集相关信息和背景资料',
        dependsOn: [],
        estimatedDuration: 20000,
        requiredCapabilities: ['read', 'search', 'fetch'],
        type: 'collect'
      },
      {
        id: 'analyze_structure',
        task: '分析结构和组成部分',
        dependsOn: ['collect_info'],
        estimatedDuration: 30000,
        requiredCapabilities: ['read', 'analyze'],
        type: 'analyze'
      },
      {
        id: 'deep_analysis',
        task: '深度分析和挖掘',
        dependsOn: ['analyze_structure'],
        estimatedDuration: 60000,
        requiredCapabilities: ['read', 'analyze', 'reasoning'],
        type: 'deep'
      },
      {
        id: 'synthesize_report',
        task: '综合分析并生成报告',
        dependsOn: ['deep_analysis'],
        estimatedDuration: 30000,
        requiredCapabilities: ['read', 'write', 'synthesize'],
        type: 'synthesize'
      }
    ];
    
    return subtasks;
  }

  /**
   * 通用任务分解
   */
  decomposeGenericTask(task, analysis) {
    // 默认分解为：准备 → 执行 → 验证
    return [
      {
        id: 'prepare',
        task: '准备和规划',
        dependsOn: [],
        estimatedDuration: 10000,
        requiredCapabilities: ['read', 'plan'],
        type: 'prepare'
      },
      {
        id: 'execute',
        task: `执行: ${task.substring(0, 100)}`,
        dependsOn: ['prepare'],
        estimatedDuration: 60000,
        requiredCapabilities: ['read', 'write', 'execute'],
        type: 'execute'
      },
      {
        id: 'verify',
        task: '验证和整理结果',
        dependsOn: ['execute'],
        estimatedDuration: 15000,
        requiredCapabilities: ['read', 'verify'],
        type: 'verify'
      }
    ];
  }

  /**
   * 构建 DAG
   * @param {Array} subtasks 
   * @returns {Object} DAG
   */
  buildDAG(subtasks) {
    // 构建邻接表
    const graph = {};
    const inDegree = {};
    
    subtasks.forEach(st => {
      graph[st.id] = [];
      inDegree[st.id] = 0;
    });
    
    subtasks.forEach(st => {
      st.dependsOn.forEach(depId => {
        if (graph[depId]) {
          graph[depId].push(st.id);
          inDegree[st.id]++;
        }
      });
    });
    
    // 拓扑排序，找出并行组
    const parallelGroups = [];
    const queue = [];
    
    // 找到入度为0的节点
    Object.keys(inDegree).forEach(id => {
      if (inDegree[id] === 0) queue.push(id);
    });
    
    while (queue.length > 0) {
      const currentGroup = [...queue];
      parallelGroups.push(currentGroup);
      
      queue.length = 0;
      
      currentGroup.forEach(id => {
        graph[id].forEach(nextId => {
          inDegree[nextId]--;
          if (inDegree[nextId] === 0) {
            queue.push(nextId);
          }
        });
      });
    }
    
    return {
      subtasks,
      graph,
      parallelGroups,
      isValid: parallelGroups.length > 0
    };
  }

  /**
   * 获取可执行的子任务
   * @param {Object} dag 
   * @param {Set} completed - 已完成的子任务
   * @returns {Array} 可执行的子任务
   */
  getExecutableSubtasks(dag, completed = new Set()) {
    return dag.subtasks.filter(st => {
      // 未完成
      if (completed.has(st.id)) return false;
      
      // 依赖已满足
      return st.dependsOn.every(depId => completed.has(depId));
    });
  }

  /**
   * 估算总耗时
   * @param {Object} dag 
   * @returns {number} 毫秒
   */
  estimateTotalDuration(dag) {
    let total = 0;
    
    // 按并行组累加最长时间
    dag.parallelGroups.forEach(group => {
      const maxDuration = Math.max(...group.map(id => {
        const st = dag.subtasks.find(s => s.id === id);
        return st ? st.estimatedDuration : 0;
      }));
      total += maxDuration;
    });
    
    return total;
  }
}

module.exports = {
  TaskDecomposer
};
