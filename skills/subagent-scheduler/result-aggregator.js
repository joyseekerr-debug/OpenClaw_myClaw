/**
 * Result Aggregator
 * 结果聚合器 - 收集子任务结果并生成最终输出
 */

const EventEmitter = require('events');

/**
 * 聚合策略枚举
 */
const AggregationStrategy = {
  CONCAT: 'concat',           // 简单拼接
  SMART_MERGE: 'smart_merge', // 智能合并
  VOTE: 'vote',              // 投票机制
  PRIORITY: 'priority',       // 优先级
  SUMMARIZE: 'summarize'      // 摘要生成
};

/**
 * 结果聚合器类
 */
class ResultAggregator extends EventEmitter {
  constructor(options = {}) {
    super();
    this.strategy = options.strategy || AggregationStrategy.SMART_MERGE;
    this.conflictThreshold = options.conflictThreshold || 0.8;
  }

  /**
   * 收集子任务结果
   * @param {string} subtaskId 
   * @param {*} result 
   * @param {Object} metadata 
   */
  collect(subtaskId, result, metadata = {}) {
    this.emit('result-collected', { subtaskId, result, metadata });
    return { subtaskId, result, metadata, timestamp: Date.now() };
  }

  /**
   * 聚合多个结果
   * @param {Array} results - 结果数组
   * @param {Object} options 
   * @returns {Object} 聚合结果
   */
  async aggregate(results, options = {}) {
    const { 
      strategy = this.strategy,
      originalTask = ''
    } = options;
    
    if (!results || results.length === 0) {
      return { success: false, error: '没有结果可聚合' };
    }
    
    if (results.length === 1) {
      return {
        success: true,
        result: results[0].result,
        source: 'single',
        metadata: results[0].metadata
      };
    }
    
    this.emit('aggregating', { count: results.length, strategy });
    
    switch (strategy) {
      case AggregationStrategy.CONCAT:
        return this.aggregateByConcat(results);
        
      case AggregationStrategy.SMART_MERGE:
        return this.aggregateBySmartMerge(results);
        
      case AggregationStrategy.VOTE:
        return this.aggregateByVote(results);
        
      case AggregationStrategy.PRIORITY:
        return this.aggregateByPriority(results, options.priorities);
        
      case AggregationStrategy.SUMMARIZE:
        return await this.aggregateBySummarize(results, originalTask);
        
      default:
        return this.aggregateByConcat(results);
    }
  }

  /**
   * 简单拼接聚合
   */
  aggregateByConcat(results) {
    const texts = results.map(r => {
      if (typeof r.result === 'string') return r.result;
      if (typeof r.result === 'object') return JSON.stringify(r.result);
      return String(r.result);
    });
    
    return {
      success: true,
      result: texts.join('\n\n---\n\n'),
      source: 'concat',
      count: results.length
    };
  }

  /**
   * 智能合并聚合
   */
  aggregateBySmartMerge(results) {
    // 1. 去重
    const uniqueResults = this.deduplicate(results);
    
    // 2. 检测冲突
    const conflicts = this.detectConflicts(uniqueResults);
    
    // 3. 解决冲突
    const resolved = this.resolveConflicts(uniqueResults, conflicts);
    
    // 4. 合并文本
    const merged = this.mergeTexts(resolved);
    
    return {
      success: true,
      result: merged,
      source: 'smart_merge',
      count: results.length,
      uniqueCount: uniqueResults.length,
      conflictCount: conflicts.length
    };
  }

  /**
   * 投票聚合
   */
  aggregateByVote(results) {
    // 按结果内容分组
    const votes = new Map();
    
    results.forEach(r => {
      const key = typeof r.result === 'string' 
        ? r.result 
        : JSON.stringify(r.result);
      
      if (!votes.has(key)) {
        votes.set(key, { count: 0, results: [] });
      }
      
      const vote = votes.get(key);
      vote.count++;
      vote.results.push(r);
    });
    
    // 找出票数最高的
    let winner = null;
    let maxVotes = 0;
    
    for (const [key, vote] of votes) {
      if (vote.count > maxVotes) {
        maxVotes = vote.count;
        winner = vote.results[0];
      }
    }
    
    return {
      success: true,
      result: winner.result,
      source: 'vote',
      confidence: maxVotes / results.length,
      voteDistribution: Array.from(votes.entries()).map(([k, v]) => ({
        result: k.substring(0, 100),
        votes: v.count
      }))
    };
  }

  /**
   * 优先级聚合
   */
  aggregateByPriority(results, priorities = {}) {
    // 按优先级排序
    const sorted = results.sort((a, b) => {
      const priorityA = priorities[a.subtaskId] || 0;
      const priorityB = priorities[b.subtaskId] || 0;
      return priorityB - priorityA;
    });
    
    // 返回最高优先级的结果
    return {
      success: true,
      result: sorted[0].result,
      source: 'priority',
      selectedFrom: sorted[0].subtaskId
    };
  }

  /**
   * 摘要聚合（简化版）
   */
  async aggregateBySummarize(results, originalTask) {
    // 合并所有文本
    const fullText = results.map(r => {
      if (typeof r.result === 'string') return r.result;
      return JSON.stringify(r.result);
    }).join('\n\n');
    
    // 简化摘要：提取关键句
    const summary = this.extractKeyPoints(fullText);
    
    return {
      success: true,
      result: {
        summary,
        fullText: fullText.substring(0, 5000) + '...',
        originalTask
      },
      source: 'summarize',
      count: results.length
    };
  }

  /**
   * 去重
   */
  deduplicate(results) {
    const seen = new Set();
    return results.filter(r => {
      const key = typeof r.result === 'string' 
        ? r.result 
        : JSON.stringify(r.result);
      
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  /**
   * 检测冲突
   */
  detectConflicts(results) {
    const conflicts = [];
    
    for (let i = 0; i < results.length; i++) {
      for (let j = i + 1; j < results.length; j++) {
        const similarity = this.calculateSimilarity(
          results[i].result,
          results[j].result
        );
        
        // 相似度在阈值附近视为潜在冲突
        if (similarity > 0.3 && similarity < this.conflictThreshold) {
          conflicts.push({
            pair: [results[i].subtaskId, results[j].subtaskId],
            similarity,
            type: 'potential_conflict'
          });
        }
      }
    }
    
    return conflicts;
  }

  /**
   * 解决冲突
   */
  resolveConflicts(results, conflicts) {
    // 简化：保留置信度高的结果
    return results.sort((a, b) => {
      const confidenceA = a.metadata?.confidence || 0.5;
      const confidenceB = b.metadata?.confidence || 0.5;
      return confidenceB - confidenceA;
    });
  }

  /**
   * 合并文本
   */
  mergeTexts(results) {
    const sections = results.map((r, index) => {
      const header = `[${r.metadata?.agentName || 'Agent'} ${index + 1}]`;
      const content = typeof r.result === 'string' 
        ? r.result 
        : JSON.stringify(r.result, null, 2);
      return `${header}\n${content}`;
    });
    
    return sections.join('\n\n---\n\n');
  }

  /**
   * 计算相似度（简化版）
   */
  calculateSimilarity(a, b) {
    const strA = typeof a === 'string' ? a : JSON.stringify(a);
    const strB = typeof b === 'string' ? b : JSON.stringify(b);
    
    // 使用简单的词频相似度
    const wordsA = new Set(strA.toLowerCase().split(/\s+/));
    const wordsB = new Set(strB.toLowerCase().split(/\s+/));
    
    const intersection = new Set([...wordsA].filter(x => wordsB.has(x)));
    const union = new Set([...wordsA, ...wordsB]);
    
    return intersection.size / union.size;
  }

  /**
   * 提取关键点（简化版）
   */
  extractKeyPoints(text) {
    const sentences = text.split(/[。！？.!?]/).filter(s => s.trim().length > 10);
    
    // 简单的关键词提取
    const keywords = ['重要', '关键', '核心', '主要', '总结', '结论'];
    const keySentences = sentences.filter(s => 
      keywords.some(k => s.includes(k))
    );
    
    return {
      keyPoints: keySentences.slice(0, 5),
      totalSentences: sentences.length,
      charCount: text.length
    };
  }

  /**
   * 按 DAG 结构聚合
   * @param {Object} dag 
   * @param {Map} results - subtaskId -> result
   */
  async aggregateByDAG(dag, results) {
    // 按并行组顺序聚合
    const aggregatedResults = [];
    
    for (const group of dag.parallelGroups) {
      const groupResults = group
        .map(id => results.get(id))
        .filter(r => r !== undefined);
      
      if (groupResults.length > 0) {
        const aggregated = await this.aggregate(groupResults, {
          strategy: AggregationStrategy.SMART_MERGE
        });
        
        aggregatedResults.push({
          group,
          ...aggregated
        });
      }
    }
    
    // 最终聚合
    return await this.aggregate(
      aggregatedResults.map(r => ({ result: r.result })),
      { strategy: AggregationStrategy.CONCAT }
    );
  }
}

module.exports = {
  ResultAggregator,
  AggregationStrategy
};
