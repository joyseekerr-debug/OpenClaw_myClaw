"""
股价预测系统 - 多模型集成模块
加权融合多个模型的预测结果
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelPrediction:
    """单个模型的预测结果"""
    model_name: str
    timeframe: str
    up_probability: float
    down_probability: float
    prediction: str  # 'up', 'down', 'hold'
    confidence: float
    weight: float = 1.0  # 模型权重


@dataclass
class EnsemblePrediction:
    """集成预测结果"""
    up_probability: float
    down_probability: float
    prediction: str
    confidence: float
    model_contributions: Dict[str, float]
    consensus_level: float  # 一致性程度 0-1


class ModelEnsemble:
    """多模型集成器"""
    
    def __init__(self, 
                 model_weights: Dict[str, float] = None,
                 use_dynamic_weights: bool = True):
        """
        Args:
            model_weights: 模型权重配置 {model_name: weight}
            use_dynamic_weights: 是否使用动态权重调整
        """
        # 默认权重配置
        self.default_weights = model_weights or {
            'LSTM': 0.25,
            'XGBoost': 0.25,
            'Transformer': 0.25,
            'PriceAction': 0.25
        }
        
        self.weights = self.default_weights.copy()
        self.use_dynamic_weights = use_dynamic_weights
        
        # 历史性能记录 (用于动态权重)
        self.performance_history = {
            model: {'accuracy': [], 'recent_accuracy': 0.5}
            for model in self.weights.keys()
        }
    
    def predict(self, predictions: List[ModelPrediction]) -> EnsemblePrediction:
        """
        集成多个模型的预测
        
        Args:
            predictions: 各模型的预测结果列表
        
        Returns:
            集成预测结果
        """
        if not predictions:
            logger.warning("No predictions to ensemble")
            return EnsemblePrediction(
                up_probability=0.5,
                down_probability=0.5,
                prediction='hold',
                confidence=0.5,
                model_contributions={},
                consensus_level=0
            )
        
        # 更新动态权重
        if self.use_dynamic_weights:
            self._update_weights(predictions)
        
        # 计算加权概率
        weighted_up = 0
        weighted_down = 0
        total_weight = 0
        
        model_contributions = {}
        
        for pred in predictions:
            model_name = pred.model_name
            weight = self.weights.get(model_name, 0.25)
            
            # 应用权重
            weighted_up += pred.up_probability * weight * pred.confidence
            weighted_down += pred.down_probability * weight * pred.confidence
            total_weight += weight * pred.confidence
            
            # 记录贡献
            model_contributions[model_name] = pred.up_probability if pred.prediction == 'up' else pred.down_probability
        
        # 归一化
        if total_weight > 0:
            up_prob = weighted_up / total_weight
            down_prob = weighted_down / total_weight
        else:
            up_prob = down_prob = 0.5
        
        # 确保概率和为1
        total = up_prob + down_prob
        if total > 0:
            up_prob /= total
            down_prob /= total
        
        # 确定预测方向
        if up_prob > down_prob:
            prediction = 'up'
            confidence = up_prob
        elif down_prob > up_prob:
            prediction = 'down'
            confidence = down_prob
        else:
            prediction = 'hold'
            confidence = 0.5
        
        # 计算一致性
        consensus = self._calculate_consensus(predictions)
        
        return EnsemblePrediction(
            up_probability=up_prob,
            down_probability=down_prob,
            prediction=prediction,
            confidence=confidence,
            model_contributions=model_contributions,
            consensus_level=consensus
        )
    
    def _update_weights(self, predictions: List[ModelPrediction]):
        """基于最新表现更新权重"""
        # 这里简化处理，实际应根据历史回测结果
        # 目前保持默认权重
        pass
    
    def update_performance(self, model_name: str, was_correct: bool):
        """
        更新模型性能记录
        
        Args:
            model_name: 模型名称
            was_correct: 预测是否正确
        """
        if model_name not in self.performance_history:
            return
        
        self.performance_history[model_name]['accuracy'].append(1 if was_correct else 0)
        
        # 只保留最近30次
        if len(self.performance_history[model_name]['accuracy']) > 30:
            self.performance_history[model_name]['accuracy'].pop(0)
        
        # 计算最近准确率
        recent = self.performance_history[model_name]['accuracy']
        if recent:
            self.performance_history[model_name]['recent_accuracy'] = np.mean(recent)
    
    def recalculate_weights(self):
        """根据历史表现重新计算权重"""
        if not self.use_dynamic_weights:
            return
        
        # 基于最近准确率调整权重
        accuracies = {
            model: data['recent_accuracy']
            for model, data in self.performance_history.items()
        }
        
        total_accuracy = sum(accuracies.values())
        
        if total_accuracy > 0:
            for model in self.weights:
                # 准确率高的模型获得更高权重
                base_weight = accuracies.get(model, 0.25)
                self.weights[model] = base_weight / total_accuracy
        
        logger.info(f"Weights updated: {self.weights}")
    
    def _calculate_consensus(self, predictions: List[ModelPrediction]) -> float:
        """
        计算模型间的一致性
        
        Returns:
            0-1之间，1表示完全一致
        """
        if len(predictions) < 2:
            return 1.0
        
        # 统计预测方向
        up_count = sum(1 for p in predictions if p.prediction == 'up')
        down_count = sum(1 for p in predictions if p.prediction == 'down')
        hold_count = sum(1 for p in predictions if p.prediction == 'hold')
        
        # 计算最大一致比例
        max_agreement = max(up_count, down_count, hold_count)
        
        return max_agreement / len(predictions)
    
    def get_recommendation(self, ensemble: EnsemblePrediction) -> str:
        """
        生成交易建议
        """
        if ensemble.consensus_level < 0.5:
            return "观望 - 模型分歧较大，等待更明确信号"
        
        if ensemble.prediction == 'up':
            if ensemble.confidence > 0.7:
                return f"强烈看涨 - 置信度{ensemble.confidence:.1%}，建议积极做多"
            elif ensemble.confidence > 0.6:
                return f"谨慎看涨 - 置信度{ensemble.confidence:.1%}，建议轻仓试多"
            else:
                return f"轻微看涨 - 置信度{ensemble.confidence:.1%}，建议观望"
        
        elif ensemble.prediction == 'down':
            if ensemble.confidence > 0.7:
                return f"强烈看跌 - 置信度{ensemble.confidence:.1%}，建议积极做空"
            elif ensemble.confidence > 0.6:
                return f"谨慎看跌 - 置信度{ensemble.confidence:.1%}，建议轻仓试空"
            else:
                return f"轻微看跌 - 置信度{ensemble.confidence:.1%}，建议观望"
        
        else:
            return "观望 - 多空平衡，等待突破"


class VotingEnsemble(ModelEnsemble):
    """投票集成 (简单多数投票)"""
    
    def predict(self, predictions: List[ModelPrediction]) -> EnsemblePrediction:
        """投票决策"""
        if not predictions:
            return super().predict(predictions)
        
        # 统计投票
        up_votes = sum(1 for p in predictions if p.prediction == 'up')
        down_votes = sum(1 for p in predictions if p.prediction == 'down')
        hold_votes = sum(1 for p in predictions if p.prediction == 'hold')
        
        total = len(predictions)
        
        up_prob = up_votes / total
        down_prob = down_votes / total
        
        # 确定胜者
        if up_votes > down_votes and up_votes > hold_votes:
            prediction = 'up'
            confidence = up_prob
        elif down_votes > up_votes and down_votes > hold_votes:
            prediction = 'down'
            confidence = down_prob
        else:
            prediction = 'hold'
            confidence = max(up_prob, down_prob, hold_votes/total)
        
        # 计算平均概率
        avg_up = np.mean([p.up_probability for p in predictions])
        avg_down = np.mean([p.down_probability for p in predictions])
        
        # 归一化
        total_prob = avg_up + avg_down
        if total_prob > 0:
            avg_up /= total_prob
            avg_down /= total_prob
        
        return EnsemblePrediction(
            up_probability=avg_up,
            down_probability=avg_down,
            prediction=prediction,
            confidence=confidence,
            model_contributions={p.model_name: p.confidence for p in predictions},
            consensus_level=self._calculate_consensus(predictions)
        )


# 便捷函数
def ensemble_predictions(predictions: List[ModelPrediction],
                        method: str = 'weighted') -> EnsemblePrediction:
    """便捷函数：集成预测"""
    if method == 'weighted':
        ensemble = ModelEnsemble()
    else:
        ensemble = VotingEnsemble()
    
    return ensemble.predict(predictions)


if __name__ == '__main__':
    # 测试代码
    print("Model Ensemble Module")
    
    # 模拟预测结果
    predictions = [
        ModelPrediction('LSTM', '1d', 0.7, 0.3, 'up', 0.7),
        ModelPrediction('XGBoost', '1d', 0.6, 0.4, 'up', 0.6),
        ModelPrediction('Transformer', '1d', 0.8, 0.2, 'up', 0.8),
        ModelPrediction('PriceAction', '1d', 0.4, 0.6, 'down', 0.6)
    ]
    
    # 加权集成
    ensemble = ModelEnsemble()
    result = ensemble.predict(predictions)
    
    print(f"\nEnsemble Result:")
    print(f"  Prediction: {result.prediction}")
    print(f"  Up Probability: {result.up_probability:.2f}")
    print(f"  Down Probability: {result.down_probability:.2f}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Consensus: {result.consensus_level:.2f}")
    print(f"  Recommendation: {ensemble.get_recommendation(result)}")
