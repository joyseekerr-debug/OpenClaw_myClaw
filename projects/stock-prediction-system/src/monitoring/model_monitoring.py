"""
股价预测系统 - 监控模块
模型性能监控和告警
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelMonitor:
    """模型监控器"""
    
    def __init__(self, 
                 accuracy_threshold: float = 0.5,
                 drift_threshold: float = 0.2,
                 check_interval: int = 24):
        """
        Args:
            accuracy_threshold: 准确率告警阈值
            drift_threshold: 数据漂移阈值
            check_interval: 检查间隔(小时)
        """
        self.accuracy_threshold = accuracy_threshold
        self.drift_threshold = drift_threshold
        self.check_interval = check_interval
        
        self.prediction_history = []
        self.performance_history = []
        self.alerts = []
    
    def log_prediction(self, 
                      symbol: str,
                      prediction: str,
                      confidence: float,
                      actual: str = None):
        """
        记录预测日志
        
        Args:
            symbol: 股票代码
            prediction: 预测方向
            confidence: 置信度
            actual: 实际结果(可选)
        """
        log_entry = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'prediction': prediction,
            'confidence': confidence,
            'actual': actual
        }
        
        self.prediction_history.append(log_entry)
        
        # 只保留最近1000条
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
    
    def calculate_accuracy(self, window: int = 100) -> Dict:
        """
        计算最近准确率
        
        Args:
            window: 窗口大小
        
        Returns:
            准确率统计
        """
        # 过滤有实际结果的记录
        validated = [p for p in self.prediction_history 
                    if p['actual'] is not None]
        
        if len(validated) < window:
            window = len(validated)
        
        if window == 0:
            return {'accuracy': 0, 'sample_size': 0}
        
        recent = validated[-window:]
        
        correct = sum(1 for p in recent if p['prediction'] == p['actual'])
        accuracy = correct / window
        
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': window,
            'sample_size': window
        }
    
    def check_model_health(self) -> Dict:
        """
        检查模型健康状态
        
        Returns:
            健康状态报告
        """
        accuracy_stats = self.calculate_accuracy(window=100)
        
        issues = []
        
        # 检查准确率
        if accuracy_stats['accuracy'] < self.accuracy_threshold:
            issues.append({
                'type': 'low_accuracy',
                'severity': 'warning',
                'message': f"Accuracy dropped to {accuracy_stats['accuracy']:.2%}"
            })
        
        # 检查预测分布
        if len(self.prediction_history) >= 50:
            recent = self.prediction_history[-50:]
            up_ratio = sum(1 for p in recent if p['prediction'] == 'up') / len(recent)
            
            if up_ratio < 0.2 or up_ratio > 0.8:
                issues.append({
                    'type': 'prediction_bias',
                    'severity': 'info',
                    'message': f"Prediction bias detected: up_ratio={up_ratio:.2%}"
                })
        
        status = 'healthy' if not issues else 'degraded'
        
        return {
            'status': status,
            'accuracy': accuracy_stats,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_drift(self, 
                    reference_data: pd.DataFrame,
                    current_data: pd.DataFrame) -> Dict:
        """
        检测数据漂移
        
        Args:
            reference_data: 参考数据(训练时)
            current_data: 当前数据
        
        Returns:
            漂移检测结果
        """
        drift_detected = False
        drifted_features = []
        
        numeric_cols = reference_data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in current_data.columns:
                continue
            
            ref_mean = reference_data[col].mean()
            ref_std = reference_data[col].std()
            
            current_mean = current_data[col].mean()
            
            # 计算标准化差异
            if ref_std > 0:
                z_score = abs(current_mean - ref_mean) / ref_std
                
                if z_score > self.drift_threshold:
                    drift_detected = True
                    drifted_features.append({
                        'feature': col,
                        'z_score': z_score,
                        'ref_mean': ref_mean,
                        'current_mean': current_mean
                    })
        
        return {
            'drift_detected': drift_detected,
            'drifted_features': drifted_features,
            'timestamp': datetime.now().isoformat()
        }
    
    def should_retrain(self) -> bool:
        """
        判断是否需要重新训练
        
        Returns:
            是否需要重训练
        """
        accuracy_stats = self.calculate_accuracy(window=30)
        
        # 连续7天准确率低于阈值
        if accuracy_stats['accuracy'] < self.accuracy_threshold and accuracy_stats['sample_size'] >= 7:
            return True
        
        return False


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_history = []
        self.alert_cooldown = {}  # 告警冷却
    
    def send_alert(self, alert_type: str, message: str, 
                  severity: str = 'info') -> bool:
        """
        发送告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            severity: 严重程度 (info/warning/critical)
        
        Returns:
            是否发送成功
        """
        # 检查冷却期
        if self._is_in_cooldown(alert_type):
            return False
        
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'severity': severity,
            'message': message
        }
        
        self.alert_history.append(alert)
        
        # 设置冷却期 (5分钟)
        self.alert_cooldown[alert_type] = datetime.now()
        
        # 记录告警
        logger.warning(f"ALERT [{severity}]: {message}")
        
        # 这里可以集成飞书/邮件通知
        self._send_notification(alert)
        
        return True
    
    def _is_in_cooldown(self, alert_type: str) -> bool:
        """检查是否在冷却期"""
        if alert_type not in self.alert_cooldown:
            return False
        
        last_alert = self.alert_cooldown[alert_type]
        cooldown_period = timedelta(minutes=5)
        
        return datetime.now() - last_alert < cooldown_period
    
    def _send_notification(self, alert: Dict):
        """发送通知"""
        # 简化实现，实际应调用飞书API
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }
        
        emoji = severity_emoji.get(alert['severity'], 'ℹ️')
        
        print(f"\n{emoji} 系统告警")
        print(f"类型: {alert['type']}")
        print(f"级别: {alert['severity']}")
        print(f"时间: {alert['timestamp']}")
        print(f"消息: {alert['message']}")
        print("-" * 40)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """获取最近告警"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alert_history
            if alert['timestamp'] > cutoff
        ]


class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self):
        self.metrics = {
            'predictions_made': 0,
            'predictions_correct': 0,
            'avg_latency_ms': 0,
            'errors': 0
        }
        self.latency_history = []
    
    def record_prediction(self, latency_ms: float, correct: bool = None):
        """记录预测性能"""
        self.metrics['predictions_made'] += 1
        
        if correct is not None:
            if correct:
                self.metrics['predictions_correct'] += 1
        
        # 更新平均延迟
        self.latency_history.append(latency_ms)
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)
        
        self.metrics['avg_latency_ms'] = np.mean(self.latency_history)
    
    def record_error(self):
        """记录错误"""
        self.metrics['errors'] += 1
    
    def get_report(self) -> Dict:
        """获取性能报告"""
        accuracy = 0
        if self.metrics['predictions_made'] > 0:
            accuracy = self.metrics['predictions_correct'] / self.metrics['predictions_made']
        
        return {
            **self.metrics,
            'accuracy': accuracy,
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
def monitor_model_performance(predictions: List[Dict], 
                             actuals: List[str]) -> Dict:
    """便捷函数：监控模型性能"""
    monitor = ModelMonitor()
    
    for pred, actual in zip(predictions, actuals):
        monitor.log_prediction(
            symbol=pred.get('symbol', 'unknown'),
            prediction=pred.get('prediction', 'hold'),
            confidence=pred.get('confidence', 0.5),
            actual=actual
        )
    
    return monitor.check_model_health()


if __name__ == '__main__':
    print("Monitoring Module")
    
    # 测试
    monitor = ModelMonitor()
    
    # 模拟预测历史
    for i in range(100):
        monitor.log_prediction(
            symbol='1810.HK',
            prediction='up' if i % 2 == 0 else 'down',
            confidence=0.6,
            actual='up' if i % 3 == 0 else 'down'
        )
    
    # 检查健康状态
    health = monitor.check_model_health()
    print(f"\nHealth Check: {health}")
    
    # 告警测试
    alert_mgr = AlertManager()
    alert_mgr.send_alert('test', '这是一个测试告警', 'warning')
