"""
股价预测系统 - XGBoost中频预测模型
适用于15分钟和1小时时间框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入XGBoost
try:
    import xgboost as xgb
    from xgboost import XGBClassifier, plot_importance
    XGB_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not available. Will use mock implementation.")
    XGB_AVAILABLE = False

# 尝试导入SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class XGBoostPredictor:
    """XGBoost中频预测器"""
    
    def __init__(self,
                 max_depth: int = 6,
                 learning_rate: float = 0.1,
                 n_estimators: int = 200,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 reg_alpha: float = 0.1,
                 reg_lambda: float = 1.0,
                 min_child_weight: int = 3):
        """
        Args:
            max_depth: 树的最大深度
            learning_rate: 学习率
            n_estimators: 树的数量
            subsample: 样本采样比例
            colsample_bytree: 特征采样比例
            reg_alpha: L1正则化
            reg_lambda: L2正则化
            min_child_weight: 最小叶子节点样本权重和
        """
        self.params = {
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'n_estimators': n_estimators,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda,
            'min_child_weight': min_child_weight,
            'objective': 'binary:logistic',
            'eval_metric': ['auc', 'logloss'],
            'n_jobs': -1,
            'random_state': 42
        }
        
        self.model = None
        self.feature_names = None
        self.feature_importance = None
    
    def build_model(self):
        """构建XGBoost模型"""
        if not XGB_AVAILABLE:
            logger.error("XGBoost not available")
            return None
        
        self.model = XGBClassifier(**self.params)
        logger.info("XGBoost model built")
        
        return self.model
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None,
              early_stopping_rounds: int = 20) -> Dict:
        """
        训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练标签 (0或1)
            X_val: 验证特征
            y_val: 验证标签
            early_stopping_rounds: 早停轮数
        
        Returns:
            训练结果
        """
        if self.model is None:
            self.build_model()
        
        if not XGB_AVAILABLE:
            logger.error("Cannot train without XGBoost")
            return {}
        
        # 保存特征名
        self.feature_names = X_train.columns.tolist()
        
        # 准备验证集
        eval_set = []
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
        
        logger.info("Starting XGBoost training...")
        
        # 训练 (简化版本，避免API兼容问题)
        try:
            if eval_set:
                # 尝试使用新API
                from xgboost.callback import EarlyStopping
                self.model.fit(
                    X_train, y_train,
                    eval_set=eval_set,
                    callbacks=[EarlyStopping(rounds=early_stopping_rounds)],
                    verbose=False
                )
            else:
                self.model.fit(X_train, y_train, verbose=False)
        except Exception as e:
            # 回退到基础训练
            logger.warning(f"Advanced training failed: {e}, using basic fit")
            self.model.fit(X_train, y_train, verbose=False)
        
        # 获取最佳迭代次数 (仅early stopping时有)
        best_iteration = getattr(self.model, 'best_iteration', self.params.get('n_estimators', 100))
        
        # 获取特征重要性
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Training completed. Best iteration: {best_iteration}")
        
        return {
            'best_iteration': best_iteration,
            'feature_importance': self.feature_importance.head(10).to_dict()
        }
    
    def predict(self, X: pd.DataFrame) -> Dict:
        """
        预测
        
        Args:
            X: 特征DataFrame
        
        Returns:
            {
                'up_probability': float,
                'down_probability': float,
                'prediction': str,
                'confidence': float
            }
        """
        if self.model is None:
            logger.error("Model not trained")
            return {}
        
        if not XGB_AVAILABLE:
            return {
                'up_probability': 0.5,
                'down_probability': 0.5,
                'prediction': 'hold',
                'confidence': 0.5
            }
        
        # 预测概率
        prob = self.model.predict_proba(X)
        
        up_prob = float(prob[0][1])
        down_prob = float(prob[0][0])
        
        # 确定方向
        if up_prob > down_prob:
            prediction = 'up'
            confidence = up_prob
        else:
            prediction = 'down'
            confidence = down_prob
        
        return {
            'up_probability': up_prob,
            'down_probability': down_prob,
            'prediction': prediction,
            'confidence': confidence
        }
    
    def predict_batch(self, X: pd.DataFrame) -> pd.DataFrame:
        """批量预测"""
        if self.model is None:
            logger.error("Model not trained")
            return pd.DataFrame()
        
        if not XGB_AVAILABLE:
            return pd.DataFrame({
                'up_probability': [0.5] * len(X),
                'down_probability': [0.5] * len(X)
            })
        
        prob = self.model.predict_proba(X)
        
        return pd.DataFrame({
            'up_probability': prob[:, 1],
            'down_probability': prob[:, 0],
            'prediction': np.where(prob[:, 1] > prob[:, 0], 'up', 'down'),
            'confidence': np.maximum(prob[:, 0], prob[:, 1])
        })
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        评估模型
        
        Returns:
            评估指标
        """
        if self.model is None:
            logger.error("Model not trained")
            return {}
        
        if not XGB_AVAILABLE:
            return {'accuracy': 0.5}
        
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, 
            f1_score, roc_auc_score, classification_report
        )
        
        # 预测
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]
        
        # 计算指标
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        auc = roc_auc_score(y_test, y_prob)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc': auc
        }
    
    def get_shap_values(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        获取SHAP值（特征贡献度）
        
        Returns:
            SHAP值数组
        """
        if not SHAP_AVAILABLE or self.model is None:
            logger.warning("SHAP not available")
            return None
        
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)
        
        return shap_values
    
    def explain_prediction(self, X_sample: pd.DataFrame) -> Dict:
        """
        解释单个预测
        
        Returns:
            特征贡献度
        """
        if self.feature_importance is None:
            return {}
        
        # 获取最重要的5个特征
        top_features = self.feature_importance.head(5)['feature'].tolist()
        
        # 获取样本值
        sample_values = X_sample[top_features].iloc[0].to_dict()
        
        return {
            'top_features': top_features,
            'feature_values': sample_values,
            'importance_scores': self.feature_importance.head(5).to_dict()
        }
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.model is not None and XGB_AVAILABLE:
            self.model.save_model(filepath)
            logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        if XGB_AVAILABLE:
            if self.model is None:
                self.build_model()
            self.model.load_model(filepath)
            logger.info(f"Model loaded from {filepath}")


class XGBoostTrainer:
    """XGBoost训练器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.predictor = XGBoostPredictor(**self.config)
    
    def train_model(self, df: pd.DataFrame,
                    feature_cols: List[str],
                    target_col: str = 'target_direction_1',
                    test_size: float = 0.2,
                    val_size: float = 0.1) -> Dict:
        """
        完整训练流程
        
        Returns:
            训练结果
        """
        # 准备数据
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        
        # 只保留0和1的样本
        mask = y.isin([0, 1])
        X = X[mask]
        y = y[mask]
        
        # 划分数据集
        n_samples = len(X)
        n_test = int(n_samples * test_size)
        n_val = int(n_samples * val_size)
        n_train = n_samples - n_test - n_val
        
        X_train = X.iloc[:n_train]
        y_train = y.iloc[:n_train]
        X_val = X.iloc[n_train:n_train+n_val]
        y_val = y.iloc[n_train:n_train+n_val]
        X_test = X.iloc[n_train+n_val:]
        y_test = y.iloc[n_train+n_val:]
        
        logger.info(f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        
        # 训练
        train_result = self.predictor.train(X_train, y_train, X_val, y_val)
        
        # 评估
        evaluation = self.predictor.evaluate(X_test, y_test)
        
        return {
            'train_result': train_result,
            'evaluation': evaluation,
            'model': self.predictor.model
        }


# 便捷函数
def train_xgboost_model(df: pd.DataFrame, feature_cols: List[str]) -> XGBoostPredictor:
    """便捷函数：训练XGBoost模型"""
    trainer = XGBoostTrainer()
    result = trainer.train_model(df, feature_cols)
    return trainer.predictor


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    from features.feature_engineering import engineer_features
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=500)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 特征工程
        df_features = engineer_features(df)
        
        # 获取特征列
        feature_cols = [col for col in df_features.columns 
                       if col not in ['symbol', 'timeframe', 'source', 'target_direction_1']]
        
        # 训练XGBoost
        logger.info("Training XGBoost model...")
        predictor = train_xgboost_model(df_features, feature_cols[:30])
        
        # 预测测试
        if predictor.model is not None:
            X_test = df_features[feature_cols[:30]].dropna().iloc[-1:]
            prediction = predictor.predict(X_test)
            print(f"\nPrediction: {prediction}")
            
            # 特征重要性
            if predictor.feature_importance is not None:
                print("\nTop 5 important features:")
                print(predictor.feature_importance.head())
