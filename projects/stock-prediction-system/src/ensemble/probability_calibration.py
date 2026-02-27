"""
股价预测系统 - 概率校准模块
将模型输出的原始概率校准为真实概率
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


@dataclass
class CalibrationResult:
    """校准结果"""
    original_prob: float
    calibrated_prob: float
    confidence_interval: Tuple[float, float]  # 95%置信区间
    calibration_method: str


class ProbabilityCalibrator:
    """概率校准器"""
    
    def __init__(self, method: str = 'platt'):
        """
        Args:
            method: 校准方法 ('platt', 'isotonic', 'beta')
        """
        self.method = method
        self.calibrator = None
        self.is_fitted = False
    
    def fit(self, probs: np.ndarray, labels: np.ndarray):
        """
        拟合校准器
        
        Args:
            probs: 原始概率 (0-1)
            labels: 真实标签 (0或1)
        """
        if len(probs) < 100:
            logger.warning(f"Insufficient samples for calibration: {len(probs)}")
            return
        
        if self.method == 'platt':
            # Platt Scaling (逻辑回归)
            self.calibrator = LogisticRegression()
            self.calibrator.fit(probs.reshape(-1, 1), labels)
        
        elif self.method == 'isotonic':
            # Isotonic Regression
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(probs, labels)
        
        elif self.method == 'beta':
            # Beta Calibration (简化版)
            self._fit_beta_calibration(probs, labels)
        
        self.is_fitted = True
        logger.info(f"Calibrator fitted using {self.method} method")
    
    def _fit_beta_calibration(self, probs: np.ndarray, labels: np.ndarray):
        """Beta校准拟合"""
        # 简化的Beta校准
        # 实际应用中需要更复杂的参数估计
        from scipy.optimize import minimize
        
        def beta_loss(params):
            a, b = params
            if a <= 0 or b <= 0:
                return 1e10
            
            # 转换概率
            from scipy.stats import beta as beta_dist
            calibrated = beta_dist.cdf(probs, a, b)
            
            # 对数损失
            epsilon = 1e-15
            log_loss = -np.mean(
                labels * np.log(calibrated + epsilon) +
                (1 - labels) * np.log(1 - calibrated + epsilon)
            )
            return log_loss
        
        result = minimize(beta_loss, [1.0, 1.0], method='L-BFGS-B')
        self.beta_params = result.x if result.success else [1.0, 1.0]
    
    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """
        校准概率
        
        Args:
            probs: 原始概率
        
        Returns:
            校准后的概率
        """
        if not self.is_fitted:
            logger.warning("Calibrator not fitted, returning original probabilities")
            return probs
        
        if self.method in ['platt', 'isotonic']:
            return self.calibrator.predict(probs.reshape(-1, 1))
        
        elif self.method == 'beta':
            from scipy.stats import beta as beta_dist
            return beta_dist.cdf(probs, self.beta_params[0], self.beta_params[1])
        
        return probs
    
    def calibrate_single(self, prob: float) -> CalibrationResult:
        """
        校准单个概率
        
        Returns:
            CalibrationResult
        """
        calibrated = self.calibrate(np.array([prob]))[0]
        
        # 计算置信区间 (简化版)
        # 实际应使用Bootstrap或其他方法
        ci_width = 0.1 * (1 - abs(calibrated - 0.5) * 2)  # 越接近0.5，区间越宽
        ci_lower = max(0, calibrated - ci_width)
        ci_upper = min(1, calibrated + ci_width)
        
        return CalibrationResult(
            original_prob=prob,
            calibrated_prob=calibrated,
            confidence_interval=(ci_lower, ci_upper),
            calibration_method=self.method
        )


class ConfidenceScorer:
    """置信度评分器"""
    
    def __init__(self):
        self.uncertainty_threshold = 0.2
    
    def calculate_confidence(self, 
                            ensemble_prob: float,
                            model_consensus: float,
                            historical_accuracy: float) -> float:
        """
        计算综合置信度
        
        Args:
            ensemble_prob: 集成后的概率
            model_consensus: 模型一致性 (0-1)
            historical_accuracy: 历史准确率
        
        Returns:
            置信度 (0-1)
        """
        # 概率本身的置信度 (越接近0或1，置信度越高)
        prob_confidence = abs(ensemble_prob - 0.5) * 2
        
        # 加权平均
        confidence = (
            prob_confidence * 0.4 +
            model_consensus * 0.3 +
            historical_accuracy * 0.3
        )
        
        return min(confidence, 1.0)
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        获取置信度等级
        """
        if confidence >= 0.8:
            return "高"
        elif confidence >= 0.6:
            return "中"
        elif confidence >= 0.4:
            return "低"
        else:
            return "极低"
    
    def should_trade(self, confidence: float, 
                     min_confidence: float = 0.55) -> bool:
        """
        判断是否应进行交易
        """
        return confidence >= min_confidence


class UncertaintyQuantifier:
    """不确定性量化器"""
    
    def __init__(self):
        pass
    
    def quantify_uncertainty(self, predictions: List[float]) -> Dict:
        """
        量化预测不确定性
        
        Args:
            predictions: 多次预测的结果列表
        
        Returns:
            不确定性指标
        """
        if not predictions:
            return {'mean': 0.5, 'std': 1.0, 'entropy': 1.0}
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        # 计算熵 (不确定性)
        # 将预测分为两类
        p_up = np.mean([1 if p > 0.5 else 0 for p in predictions])
        p_down = 1 - p_up
        
        epsilon = 1e-10
        entropy = -(p_up * np.log2(p_up + epsilon) + p_down * np.log2(p_down + epsilon))
        
        return {
            'mean': mean,
            'std': std,
            'entropy': entropy,
            'variance': std ** 2,
            'uncertainty_level': self._classify_uncertainty(std, entropy)
        }
    
    def _classify_uncertainty(self, std: float, entropy: float) -> str:
        """分类不确定性级别"""
        if std < 0.1 and entropy < 0.3:
            return "低不确定性"
        elif std < 0.2 and entropy < 0.7:
            return "中等不确定性"
        else:
            return "高不确定性"
    
    def monte_carlo_dropout(self, model, X: np.ndarray, 
                           n_samples: int = 100) -> Dict:
        """
        使用Monte Carlo Dropout估计不确定性
        
        注意: 这需要模型支持Dropout在推理时启用
        """
        predictions = []
        
        for _ in range(n_samples):
            # 启用Dropout进行预测
            pred = model.predict(X, training=True)
            predictions.append(pred[0][1] if len(pred[0]) > 1 else pred[0])
        
        return self.quantify_uncertainty(predictions)


# 便捷函数
def calibrate_probability(prob: float, 
                         probs_history: np.ndarray = None,
                         labels_history: np.ndarray = None) -> CalibrationResult:
    """便捷函数：校准概率"""
    calibrator = ProbabilityCalibrator()
    
    if probs_history is not None and labels_history is not None:
        calibrator.fit(probs_history, labels_history)
    
    return calibrator.calibrate_single(prob)


if __name__ == '__main__':
    print("Probability Calibration Module")
    
    # 测试校准
    calibrator = ProbabilityCalibrator(method='platt')
    
    # 模拟数据
    np.random.seed(42)
    probs = np.random.beta(2, 2, 1000)  # 偏向0.5的概率
    labels = (probs > 0.5).astype(int)
    
    # 拟合校准器
    calibrator.fit(probs, labels)
    
    # 测试校准
    test_probs = [0.3, 0.5, 0.7, 0.9]
    print("\nCalibration Examples:")
    for prob in test_probs:
        result = calibrator.calibrate_single(prob)
        print(f"  {prob:.2f} -> {result.calibrated_prob:.2f} "
              f"(CI: {result.confidence_interval[0]:.2f}-{result.confidence_interval[1]:.2f})")
