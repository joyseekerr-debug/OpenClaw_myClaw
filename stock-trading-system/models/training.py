"""
模型训练与评估模块
包含数据准备、模型训练、交叉验证、性能评估
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import logging
import pickle
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, model, model_name: str):
        """
        初始化训练器
        
        Args:
            model: 模型实例 (LSTMModel/XGBoostModel/TransformerModel)
            model_name: 模型名称
        """
        self.model = model
        self.model_name = model_name
        self.training_history = {}
        self.metrics = {}
        
    def prepare_data(self, df: pd.DataFrame, feature_cols: List[str],
                    target_col: str = 'close', 
                    sequence_length: int = 60,
                    train_ratio: float = 0.8,
                    val_ratio: float = 0.1) -> Dict[str, Any]:
        """
        准备训练数据
        
        Args:
            df: 特征数据
            feature_cols: 特征列名
            target_col: 目标列名
            sequence_length: 序列长度（用于LSTM/Transformer）
            train_ratio: 训练集比例
            val_ratio: 验证集比例
        
        Returns:
            划分好的数据字典
        """
        # 计算未来收益率作为目标
        df = df.copy()
        df['target'] = df[target_col].shift(-1) / df[target_col] - 1
        df = df.dropna()
        
        # 准备特征
        X = df[feature_cols].values
        y = df['target'].values
        
        # 时间序列划分（避免数据泄露）
        n = len(X)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        X_train = X[:train_size]
        y_train = y[:train_size]
        
        X_val = X[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]
        
        X_test = X[train_size + val_size:]
        y_test = y[train_size + val_size:]
        
        # 如果是序列模型，需要reshape
        if hasattr(self.model, 'sequence_length'):
            X_train = self._create_sequences(X_train, self.model.sequence_length)
            y_train = y_train[self.model.sequence_length:]
            
            X_val = self._create_sequences(X_val, self.model.sequence_length)
            y_val = y_val[self.model.sequence_length:]
            
            X_test = self._create_sequences(X_test, self.model.sequence_length)
            y_test = y_test[self.model.sequence_length:]
        
        logger.info(f"📊 数据划分完成:")
        logger.info(f"   训练集: {len(X_train)} 样本")
        logger.info(f"   验证集: {len(X_val)} 样本")
        logger.info(f"   测试集: {len(X_test)} 样本")
        
        return {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test,
            'feature_cols': feature_cols
        }
    
    def _create_sequences(self, X: np.ndarray, seq_length: int) -> np.ndarray:
        """创建序列数据"""
        sequences = []
        for i in range(len(X) - seq_length + 1):
            sequences.append(X[i:i + seq_length])
        return np.array(sequences)
    
    def train(self, data: Dict[str, Any], 
             save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            data: 准备好的数据字典
            save_path: 模型保存路径
        
        Returns:
            训练结果
        """
        logger.info(f"🚀 开始训练 {self.model_name} 模型...")
        
        # 训练模型
        history = self.model.train(
            data['X_train'], data['y_train'],
            data['X_val'], data['y_val']
        )
        
        self.training_history = history
        
        # 在测试集上评估
        test_metrics = self.evaluate(
            data['X_test'], data['y_test']
        )
        
        self.metrics = {
            'test': test_metrics,
            'train_size': len(data['X_train']),
            'val_size': len(data['X_val']),
            'test_size': len(data['X_test'])
        }
        
        # 保存模型
        if save_path:
            self.save_model(save_path)
        
        logger.info(f"✅ 模型训练完成!")
        logger.info(f"   测试集 MSE: {test_metrics['mse']:.6f}")
        logger.info(f"   测试集 MAE: {test_metrics['mae']:.6f}")
        logger.info(f"   测试集 R²: {test_metrics['r2']:.4f}")
        
        return {
            'history': history,
            'metrics': self.metrics
        }
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        评估模型性能
        
        Args:
            X_test: 测试特征
            y_test: 测试目标
        
        Returns:
            评估指标
        """
        # 预测
        y_pred = self.model.predict(X_test)
        
        # 计算指标
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # 方向准确率（预测涨跌方向）
        direction_true = np.sign(y_test[1:] - y_test[:-1])
        direction_pred = np.sign(y_pred[1:] - y_pred[:-1])
        direction_accuracy = np.mean(direction_true == direction_pred)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'direction_accuracy': direction_accuracy
        }
        
        return metrics
    
    def cross_validate(self, df: pd.DataFrame, feature_cols: List[str],
                      target_col: str = 'close',
                      n_splits: int = 5,
                      sequence_length: int = 60) -> Dict[str, List[float]]:
        """
        时间序列交叉验证
        
        Args:
            df: 特征数据
            feature_cols: 特征列名
            target_col: 目标列名
            n_splits: 交叉验证折数
            sequence_length: 序列长度
        
        Returns:
            各折的评估指标
        """
        logger.info(f"🔄 开始 {n_splits} 折时间序列交叉验证...")
        
        # 准备数据
        df = df.copy()
        df['target'] = df[target_col].shift(-1) / df[target_col] - 1
        df = df.dropna()
        
        X = df[feature_cols].values
        y = df['target'].values
        
        # 时间序列分割
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        cv_results = {
            'mse': [], 'rmse': [], 'mae': [], 'r2': [],
            'direction_accuracy': []
        }
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            logger.info(f"   第 {fold}/{n_splits} 折...")
            
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # 序列模型特殊处理
            if hasattr(self.model, 'sequence_length'):
                X_train_seq = self._create_sequences(X_train, sequence_length)
                y_train_seq = y_train[sequence_length:]
                X_val_seq = self._create_sequences(X_val, sequence_length)
                y_val_seq = y_val[sequence_length:]
                
                # 临时创建新模型实例
                from copy import deepcopy
                fold_model = deepcopy(self.model)
                fold_model.is_trained = False
                fold_model.model = None
                
                # 训练
                fold_model.train(X_train_seq, y_train_seq)
                
                # 评估
                metrics = self._evaluate_fold(fold_model, X_val_seq, y_val_seq)
            else:
                # 非序列模型
                fold_model = deepcopy(self.model)
                fold_model.is_trained = False
                fold_model.model = None
                if hasattr(fold_model, 'build_model'):
                    fold_model.build_model()
                
                fold_model.train(X_train, y_train)
                metrics = self._evaluate_fold(fold_model, X_val, y_val)
            
            for key in cv_results:
                cv_results[key].append(metrics[key])
        
        # 计算平均值
        cv_summary = {
            key: {'mean': np.mean(values), 'std': np.std(values)}
            for key, values in cv_results.items()
        }
        
        logger.info(f"✅ 交叉验证完成!")
        for metric, stats in cv_summary.items():
            logger.info(f"   {metric}: {stats['mean']:.4f} (±{stats['std']:.4f})")
        
        return cv_summary
    
    def _evaluate_fold(self, model, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
        """评估单折"""
        y_pred = model.predict(X_val)
        
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        direction_true = np.sign(y_val[1:] - y_val[:-1])
        direction_pred = np.sign(y_pred[1:] - y_pred[:-1])
        direction_accuracy = np.mean(direction_true == direction_pred)
        
        return {
            'mse': mse, 'rmse': rmse, 'mae': mae, 'r2': r2,
            'direction_accuracy': direction_accuracy
        }
    
    def save_model(self, path: str):
        """保存模型"""
        self.model.save(path)
        
        # 保存训练信息
        info = {
            'model_name': self.model_name,
            'training_history': self.training_history,
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        info_path = path.replace('.pkl', '_info.json').replace('.pt', '_info.json')
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2, default=str)
        
        logger.info(f"💾 模型已保存: {path}")
    
    def get_feature_importance(self, feature_names: List[str]) -> Optional[pd.DataFrame]:
        """获取特征重要性"""
        importance = self.model.get_feature_importance()
        
        if not importance:
            return None
        
        # 映射到特征名
        df_importance = pd.DataFrame([
            {'feature': feature_names[int(k.split('_')[1])], 'importance': v}
            for k, v in importance.items() if k.startswith('feature_')
        ])
        
        df_importance = df_importance.sort_values('importance', ascending=False)
        
        return df_importance


class ModelComparison:
    """模型对比评估"""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, model_name: str, metrics: Dict[str, float],
                  training_time: float = None):
        """添加模型结果"""
        self.results[model_name] = {
            'metrics': metrics,
            'training_time': training_time
        }
    
    def compare(self) -> pd.DataFrame:
        """对比所有模型"""
        comparison_data = []
        
        for model_name, result in self.results.items():
            row = {'model': model_name}
            row.update(result['metrics'])
            if result['training_time']:
                row['training_time'] = result['training_time']
            comparison_data.append(row)
        
        df = pd.DataFrame(comparison_data)
        
        # 排序（按R2降序）
        if 'r2' in df.columns:
            df = df.sort_values('r2', ascending=False)
        
        return df
    
    def get_best_model(self, metric: str = 'r2') -> str:
        """获取最佳模型"""
        comparison = self.compare()
        
        if metric in comparison.columns:
            # 对于误差指标，越小越好；对于R2等，越大越好
            if metric in ['mse', 'rmse', 'mae']:
                best_idx = comparison[metric].idxmin()
            else:
                best_idx = comparison[metric].idxmax()
            
            return comparison.loc[best_idx, 'model']
        
        return None
    
    def plot_comparison(self, save_path: Optional[str] = None):
        """可视化对比结果"""
        try:
            import matplotlib.pyplot as plt
            
            df = self.compare()
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            metrics = ['mse', 'mae', 'r2', 'direction_accuracy']
            titles = ['MSE (越低越好)', 'MAE (越低越好)', 
                     'R² (越高越好)', 'Direction Accuracy (越高越好)']
            
            for idx, (metric, title) in enumerate(zip(metrics, titles)):
                if metric in df.columns:
                    ax = axes[idx // 2, idx % 2]
                    bars = ax.bar(df['model'], df[metric])
                    ax.set_title(title)
                    ax.set_ylabel(metric.upper())
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                    
                    # 添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.4f}',
                               ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"📊 对比图已保存: {save_path}")
            
            plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib未安装，无法绘图")


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("模型训练与评估模块")
    print("="*70)
    
    # 示例：创建模拟数据
    np.random.seed(42)
    n_samples = 1000
    n_features = 30
    
    df = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    df['close'] = np.random.randn(n_samples).cumsum() + 100
    
    feature_cols = [f'feature_{i}' for i in range(n_features)]
    
    print(f"\n📊 模拟数据: {n_samples} 样本, {n_features} 特征")
    
    # 示例：创建模型和训练器
    from models.predictors import XGBoostModel
    
    model = XGBoostModel({
        'n_estimators': 100,
        'max_depth': 4,
        'learning_rate': 0.1
    })
    
    trainer = ModelTrainer(model, "XGBoost_Example")
    
    # 准备数据
    data = trainer.prepare_data(df, feature_cols, train_ratio=0.7, val_ratio=0.15)
    
    print(f"\n✅ Phase 3 模型训练模块就绪")
    print("="*70)
