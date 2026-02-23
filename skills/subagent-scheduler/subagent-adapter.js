/**
 * 子代理执行适配器
 * 绕过技能限制，在主会话中调用sessions_spawn
 * 
 * 使用方法：在主会话中require此模块，传入toolExecutor函数
 */

/**
 * 创建子代理执行器
 * @param {Function} toolExecutor - 主会话传入的tool执行函数
 * @returns {Object} 子代理执行器
 */
function createSubagentExecutor(toolExecutor) {
  return {
    /**
     * 执行子代理任务
     * @param {Object} config - 任务配置
     * @returns {Promise} 执行结果
     */
    async spawn(config) {
      // 通过主会话传入的toolExecutor调用sessions_spawn
      return toolExecutor('sessions_spawn', config);
    },

    /**
     * 获取子代理状态
     * @param {string} runId - 运行ID
     */
    async getStatus(runId) {
      return toolExecutor('subagents', { action: 'list' });
    },

    /**
     * 停止子代理
     * @param {string} runId - 运行ID
     */
    async kill(runId) {
      return toolExecutor('subagents', { action: 'kill', target: runId });
    }
  };
}

/**
 * 主会话使用示例：
 * 
 * ```javascript
 * const { createSubagentExecutor } = require('./subagent-adapter');
 * 
 * // 创建执行器，传入tool调用函数
 * const executor = createSubagentExecutor(async (tool, params) => {
 *   // 这里在主会话中调用OpenClaw工具
 *   return await eval(tool)(params);
 * });
 * 
 * // 使用执行器spawn子代理
 * const result = await executor.spawn({
 *   task: "分析代码",
 *   model: "kimi-coding/k2p5",
 *   reasoning: true
 * });
 * ```
 */

module.exports = {
  createSubagentExecutor
};
