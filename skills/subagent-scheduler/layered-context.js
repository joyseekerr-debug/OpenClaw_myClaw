/**
 * 分层上下文管理器
 * 智能压缩和分层存储上下文
 */

const EventEmitter = require('events');

/**
 * 分层上下文管理器
 */
class LayeredContext extends EventEmitter {
  constructor(options = {}) {
    super();
    this.compressionThreshold = options.compressionThreshold || 0.8; // 80%阈值触发压缩
    this.maxContextSize = options.maxContextSize || 100000; // 最大100KB
    this.compressionRatio = options.compressionRatio || 0.5; // 压缩到50%
    
    // 三层存储
    this.layers = {
      global: new Map(),   // 全局层：只读共享
      task: new Map(),     // 任务层：当前任务相关
      temp: new Map()      // 临时层：用完即删
    };
    
    this.metadata = {
      originalSize: 0,
      compressedSize: 0,
      compressionCount: 0,
      lastCompression: null
    };
  }

  /**
   * 设置全局层数据（只读）
   */
  setGlobal(key, value) {
    this.layers.global.set(key, {
      value,
      readonly: true,
      timestamp: Date.now()
    });
    this.checkCompression();
  }

  /**
   * 设置任务层数据
   */
  setTask(key, value, options = {}) {
    this.layers.task.set(key, {
      value,
      priority: options.priority || 'normal', // high/normal/low
      compressible: options.compressible !== false,
      timestamp: Date.now(),
      accessCount: 0
    });
    this.checkCompression();
  }

  /**
   * 设置临时层数据
   */
  setTemp(key, value) {
    this.layers.temp.set(key, {
      value,
      timestamp: Date.now()
    });
    // 临时层不触发压缩检查
  }

  /**
   * 获取数据（按层优先级）
   */
  get(key) {
    // 优先顺序：temp > task > global
    const layers = ['temp', 'task', 'global'];
    
    for (const layerName of layers) {
      const layer = this.layers[layerName];
      if (layer.has(key)) {
        const item = layer.get(key);
        
        // 更新访问计数
        if (layerName === 'task') {
          item.accessCount++;
          item.lastAccess = Date.now();
        }
        
        return item.value;
      }
    }
    
    return undefined;
  }

  /**
   * 检查是否需要压缩
   */
  checkCompression() {
    const currentSize = this.estimateSize();
    const ratio = currentSize / this.maxContextSize;
    
    if (ratio >= this.compressionThreshold) {
      this.emit('compression-needed', {
        currentSize,
        maxSize: this.maxContextSize,
        ratio
      });
      
      this.compress();
    }
  }

  /**
   * 估算当前上下文大小
   */
  estimateSize() {
    let size = 0;
    
    for (const [layerName, layer] of Object.entries(this.layers)) {
      for (const [key, item] of layer) {
        size += this.estimateValueSize(item.value);
        size += key.length * 2; // 字符串开销
      }
    }
    
    this.metadata.originalSize = size;
    return size;
  }

  /**
   * 估算单个值的大小
   */
  estimateValueSize(value) {
    if (value === null || value === undefined) return 0;
    if (typeof value === 'boolean') return 4;
    if (typeof value === 'number') return 8;
    if (typeof value === 'string') return value.length * 2;
    if (Array.isArray(value)) {
      return value.reduce((sum, item) => sum + this.estimateValueSize(item), 0);
    }
    if (typeof value === 'object') {
      return Object.entries(value).reduce((sum, [k, v]) => {
        return sum + k.length * 2 + this.estimateValueSize(v);
      }, 0);
    }
    return 0;
  }

  /**
   * 执行压缩
   */
  compress() {
    this.emit('compressing', { 
      before: this.estimateSize(),
      threshold: this.maxContextSize * this.compressionThreshold
    });

    const beforeSize = this.estimateSize();
    
    // 压缩策略：
    // 1. 清理临时层
    this.layers.temp.clear();
    
    // 2. 压缩任务层低优先级数据
    this.compressTaskLayer();
    
    // 3. 归档旧数据到文件
    this.archiveOldData();

    const afterSize = this.estimateSize();
    this.metadata.compressedSize = afterSize;
    this.metadata.compressionCount++;
    this.metadata.lastCompression = new Date().toISOString();

    this.emit('compressed', {
      before: beforeSize,
      after: afterSize,
      ratio: ((beforeSize - afterSize) / beforeSize * 100).toFixed(1) + '%'
    });
  }

  /**
   * 压缩任务层
   */
  compressTaskLayer() {
    const taskLayer = this.layers.task;
    const now = Date.now();
    
    for (const [key, item] of taskLayer) {
      // 跳过高优先级数据
      if (item.priority === 'high') continue;
      
      // 压缩可压缩数据
      if (item.compressible) {
        // 如果是大型字符串或对象，创建摘要
        if (typeof item.value === 'string' && item.value.length > 500) {
          item.value = this.createSummary(item.value);
          item.compressed = true;
        } else if (typeof item.value === 'object' && this.estimateValueSize(item.value) > 1000) {
          item.value = this.summarizeObject(item.value);
          item.compressed = true;
        }
      }
      
      // 清理长期未访问的低优先级数据
      if (item.priority === 'low' && item.lastAccess && (now - item.lastAccess) > 60000) {
        taskLayer.delete(key);
      }
    }
  }

  /**
   * 创建文本摘要
   */
  createSummary(text, maxLength = 200) {
    if (text.length <= maxLength) return text;
    
    // 提取关键信息
    const lines = text.split('\n').filter(l => l.trim());
    const keyLines = lines.slice(0, 5); // 前5行
    
    return {
      type: 'summary',
      originalLength: text.length,
      summary: keyLines.join('\n').substring(0, maxLength) + '...',
      fullPath: `[archived: ${Date.now()}]`,
      timestamp: Date.now()
    };
  }

  /**
   * 对象摘要
   */
  summarizeObject(obj) {
    const keys = Object.keys(obj);
    
    return {
      type: 'object-summary',
      keys: keys.slice(0, 10), // 只保留前10个键
      keyCount: keys.length,
      sample: keys.slice(0, 3).reduce((acc, key) => {
        const val = obj[key];
        acc[key] = typeof val === 'object' ? '[Object]' : val;
        return acc;
      }, {}),
      fullPath: `[archived: ${Date.now()}]`,
      timestamp: Date.now()
    };
  }

  /**
   * 归档旧数据到文件（模拟）
   */
  archiveOldData() {
    // 实际实现中，这里将数据写入文件
    // 简化版：标记为已归档
    const now = Date.now();
    const archiveThreshold = 30000; // 30秒前的数据
    
    for (const [key, item] of this.layers.task) {
      if (item.priority === 'low' && (now - item.timestamp) > archiveThreshold) {
        item.archived = true;
        item.value = `[archived to file: ${key}]`;
      }
    }
  }

  /**
   * 获取上下文统计
   */
  getStats() {
    const stats = {
      layers: {},
      metadata: { ...this.metadata }
    };
    
    for (const [layerName, layer] of Object.entries(this.layers)) {
      stats.layers[layerName] = {
        itemCount: layer.size,
        estimatedSize: Array.from(layer.values()).reduce(
          (sum, item) => sum + this.estimateValueSize(item.value), 0
        )
      };
    }
    
    return stats;
  }

  /**
   * 导出完整上下文（用于子代理传递）
   */
  export() {
    return {
      global: Object.fromEntries(
        Array.from(this.layers.global).map(([k, v]) => [k, v.value])
      ),
      task: Object.fromEntries(
        Array.from(this.layers.task).map(([k, v]) => [k, v.value])
      ),
      metadata: this.metadata
    };
  }

  /**
   * 导入上下文
   */
  import(data) {
    if (data.global) {
      for (const [key, value] of Object.entries(data.global)) {
        this.setGlobal(key, value);
      }
    }
    
    if (data.task) {
      for (const [key, value] of Object.entries(data.task)) {
        this.setTask(key, value);
      }
    }
  }

  /**
   * 清理所有数据
   */
  clear() {
    this.layers.global.clear();
    this.layers.task.clear();
    this.layers.temp.clear();
    
    this.metadata = {
      originalSize: 0,
      compressedSize: 0,
      compressionCount: 0,
      lastCompression: null
    };
  }
}

module.exports = {
  LayeredContext
};
