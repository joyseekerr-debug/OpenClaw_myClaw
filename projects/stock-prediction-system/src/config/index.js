/**
 * 股价预测系统 - 主入口
 * Multi-Agent Stock Price Prediction System
 * 
 * 系统架构:
 * - 多时间框架预测 (1m/5m/15m/1h/1d/1w)
 * - 多模型集成 (LSTM/XGBoost/Transformer/PriceAction)
 * - 概率输出与校准
 * - 回测与优化
 */

const path = require('path');
const fs = require('fs');

// 系统配置
const SYSTEM_CONFIG = {
  version: '1.0.0',
  name: 'StockPricePredictionSystem',
  timeframes: ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
  models: ['LSTM', 'XGBoost', 'Transformer', 'PriceAction'],
  symbols: ['1810.HK'], // 默认股票
  dataSource: 'itick', // iTick/Yahoo/AkShare
};

// 模型配置
const MODEL_CONFIG = {
  LSTM: {
    timeframe: ['1m', '5m'],
    lookback: 120,
    units: [128, 64, 32],
    dropout: 0.2,
    epochs: 100,
    batchSize: 32
  },
  XGBoost: {
    timeframe: ['15m', '1h'],
    maxDepth: 6,
    learningRate: 0.1,
    nEstimators: 200,
    objective: 'binary:logistic'
  },
  Transformer: {
    timeframe: ['1d', '1w'],
    dModel: 128,
    nHeads: 8,
    nLayers: 4,
    dropout: 0.1
  },
  PriceAction: {
    timeframe: ['1m', '5m', '15m', '1h', '1d', '1w'],
    patterns: ['support_resistance', 'trend_lines', 'chart_patterns', 'candlestick'],
    confidenceThreshold: 0.6
  }
};

// 特征配置
const FEATURE_CONFIG = {
  technical: {
    indicators: ['SMA', 'EMA', 'MACD', 'RSI', 'KDJ', 'BB', 'ATR', 'OBV', 'CCI', 'WR'],
    periods: [5, 10, 20, 60]
  },
  priceAction: {
    supportResistance: { lookback: 100, tolerance: 0.02 },
    trendLines: { minPoints: 3, maxDeviation: 0.01 },
    patterns: ['head_shoulders', 'double_top', 'double_bottom', 'triangle', 'flag', 'wedge']
  },
  alpha: {
    factors: ['momentum', 'volatility', 'liquidity', 'sentiment'],
    lookback: 20
  }
};

// 回测配置
const BACKTEST_CONFIG = {
  initialCapital: 100000,
  commission: 0.001,
  slippage: 0.001,
  positionSize: 0.1, // 10% per trade
  stopLoss: 0.02, // 2%
  takeProfit: 0.05 // 5%
};

module.exports = {
  SYSTEM_CONFIG,
  MODEL_CONFIG,
  FEATURE_CONFIG,
  BACKTEST_CONFIG
};
