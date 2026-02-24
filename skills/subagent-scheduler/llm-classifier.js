/**
 * LLM智能分类层
 * 当规则分类置信度不足时，使用轻量LLM模型辅助分类
 */

const config = require('./config.json');

/**
 * LLM分类器类
 */
class LLMClassifier {
  constructor(options = {}) {
    this.model = options.model || config.llmClassifier?.model || 'openai/gpt-4.1-mini';
    this.confidenceThreshold = options.confidenceThreshold || 0.75;
    this.maxTokens = options.maxTokens || 150;
    this.temperature = options.temperature || 0.1;
  }

  /**
   * 构建分类Prompt
   */
  buildPrompt(task) {
    return `分析以下任务，选择最合适的执行策略：

任务描述："""${task.substring(0, 500)}"""

可选策略：
1. Simple - 简单快速任务（<10秒，1-2个工具，如：快速查询、简单计算）
2. Standard - 标准任务（10-120秒，独立执行，如：文件分析、生成报告）
3. Batch - 批量处理（3-20个同类子任务，如：批量处理文件列表）
4. Orchestrator - 编排任务（多阶段有依赖，如：先获取再分析最后汇总）
5. Deep - 深度任务（>2分钟，多轮交互，如：深度研究、复杂分析）

请返回JSON格式：
{
  "branch": "策略名称",
  "confidence": 0-1之间的置信度,
  "reason": "选择理由（简短）",
  "estimatedDuration": 预估秒数,
  "estimatedCost": 预估美元成本
}

只返回JSON，不要其他内容。`;
  }

  /**
   * 解析LLM响应
   */
  parseResponse(response) {
    try {
      // 尝试直接解析
      let result = JSON.parse(response);
      return this.validateResult(result);
    } catch (e) {
      // 尝试从文本中提取JSON
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          let result = JSON.parse(jsonMatch[0]);
          return this.validateResult(result);
        } catch (e2) {
          console.error('[LLMClassifier] JSON解析失败:', e2.message);
        }
      }
    }
    return null;
  }

  /**
   * 验证结果格式
   */
  validateResult(result) {
    const validBranches = ['Simple', 'Standard', 'Batch', 'Orchestrator', 'Deep'];
    
    if (!result.branch || !validBranches.includes(result.branch)) {
      console.warn('[LLMClassifier] 无效的分支:', result.branch);
      return null;
    }
    
    return {
      branch: result.branch,
      confidence: Math.max(0, Math.min(1, result.confidence || 0.5)),
      reason: result.reason || 'LLM分类',
      estimatedDuration: result.estimatedDuration || this.getDefaultDuration(result.branch),
      estimatedCost: result.estimatedCost || this.getDefaultCost(result.branch),
      source: 'llm'
    };
  }

  /**
   * 获取默认耗时
   */
  getDefaultDuration(branch) {
    const durations = { Simple: 5, Standard: 45, Batch: 80, Orchestrator: 120, Deep: 300 };
    return durations[branch] || 60;
  }

  /**
   * 获取默认成本
   */
  getDefaultCost(branch) {
    const costs = { Simple: 0.001, Standard: 0.005, Batch: 0.01, Orchestrator: 0.02, Deep: 0.05 };
    return costs[branch] || 0.01;
  }

  /**
   * 调用LLM进行分类
   * 注意：这里需要外部传入callLLM函数或配置
   */
  async classify(task, callLLM = null) {
    const prompt = this.buildPrompt(task);
    
    try {
      let response;
      
      if (callLLM) {
        // 使用外部传入的LLM调用函数
        response = await callLLM({
          model: this.model,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: this.maxTokens,
          temperature: this.temperature
        });
      } else {
        // 模拟LLM调用（实际应替换为真实调用）
        response = this.mockLLMCall(task);
      }
      
      const result = this.parseResponse(response);
      
      if (result && result.confidence >= this.confidenceThreshold) {
        return result;
      }
      
      // 置信度不足，返回null让上层降级处理
      return null;
      
    } catch (error) {
      console.error('[LLMClassifier] 分类失败:', error.message);
      return null;
    }
  }

  /**
   * 模拟LLM调用（用于测试）
   */
  mockLLMCall(task) {
    const lower = task.toLowerCase();
    
    // 简单的规则模拟
    if (lower.includes('批量') || lower.includes('所有文件') || /\d+个/.test(task)) {
      return JSON.stringify({
        branch: 'Batch',
        confidence: 0.85,
        reason: '任务涉及批量处理多个项目',
        estimatedDuration: 90,
        estimatedCost: 0.015
      });
    }
    
    if (lower.includes('深度') || lower.includes('详细分析') || task.length > 300) {
      return JSON.stringify({
        branch: 'Deep',
        confidence: 0.8,
        reason: '任务需要深度分析和多轮处理',
        estimatedDuration: 400,
        estimatedCost: 0.08
      });
    }
    
    if (lower.includes('先') && (lower.includes('然后') || lower.includes('再'))) {
      return JSON.stringify({
        branch: 'Orchestrator',
        confidence: 0.82,
        reason: '任务有明显的多阶段依赖关系',
        estimatedDuration: 150,
        estimatedCost: 0.025
      });
    }
    
    if (task.length < 50) {
      return JSON.stringify({
        branch: 'Simple',
        confidence: 0.9,
        reason: '简短简单的查询任务',
        estimatedDuration: 3,
        estimatedCost: 0.001
      });
    }
    
    return JSON.stringify({
      branch: 'Standard',
      confidence: 0.75,
      reason: '一般的分析任务',
      estimatedDuration: 60,
      estimatedCost: 0.01
    });
  }

  /**
   * 批量分类多个任务
   */
  async classifyBatch(tasks, callLLM = null) {
    const results = [];
    
    for (const task of tasks) {
      const result = await this.classify(task, callLLM);
      results.push({
        task: task.substring(0, 50),
        result: result || { branch: 'Standard', confidence: 0.5, reason: 'LLM分类失败，使用默认' }
      });
    }
    
    return results;
  }
}

module.exports = {
  LLMClassifier
};
