"""
股价预测系统 - LSTM高频预测模型
适用于1分钟和5分钟时间框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        LSTM, Dense, Dropout, Bidirectional, 
        Attention, Input, Concatenate, LayerNormalization
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.utils import to_categorical
    TF_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not available. LSTM model will use mock implementation.")
    TF_AVAILABLE = False


class LSTMPredictor:
    """LSTM高频预测器"""
    
    def __init__(self, 
                 sequence_length: int = 120,
                 n_features: int = 20,
                 lstm_units: List[int] = [128, 64, 32],
                 dropout_rate: float = 0.2,
                 learning_rate: float = 0.001):
        """
        Args:
            sequence_length: 序列长度 (120 = 2小时1分钟数据)
            n_features: 特征数量
            lstm_units: LSTM层单元数
            dropout_rate: Dropout比率
            learning_rate: 学习率
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.history = None
        
    def build_model(self):
        """构建LSTM模型"""
        if not TF_AVAILABLE:
            logger.error("TensorFlow not available. Cannot build LSTM model.")
            return None
        
        # 输入层
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # 第一层双向LSTM
        x = Bidirectional(
            LSTM(self.lstm_units[0], return_sequences=True)
        )(inputs)
        x = LayerNormalization()(x)
        x = Dropout(self.dropout_rate)(x)
        
        # 第二层LSTM
        x = LSTM(self.lstm_units[1], return_sequences=True)(x)
        x = LayerNormalization()(x)
        x = Dropout(self.dropout_rate)(x)
        
        # 第三层LSTM
        x = LSTM(self.lstm_units[2], return_sequences=False)(x)
        x = LayerNormalization()(x)
        x = Dropout(self.dropout_rate)(x)
        
        # 全连接层
        x = Dense(64, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        x = Dense(32, activation='relu')(x)
        
        # 输出层 (涨跌概率)
        outputs = Dense(2, activation='softmax', name='direction')(x)
        
        # 构建模型
        model = Model(inputs=inputs, outputs=outputs)
        
        # 编译模型
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )
        
        self.model = model
        logger.info(f"LSTM model built with {model.count_params()} parameters")
        
        return model
    
    def prepare_data(self, df: pd.DataFrame, 
                     feature_cols: List[str],
                     target_col: str = 'target_direction_1') -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            df: 特征DataFrame
            feature_cols: 特征列名
            target_col: 目标列名
        
        Returns:
            X, y arrays
        """
        data = df[feature_cols].values
        targets = df[target_col].values
        
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(targets[i + self.sequence_length])
        
        X = np.array(X)
        y = np.array(y)
        
        # 转换为one-hot编码
        y = to_categorical(y, num_classes=2)
        
        logger.info(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
        
        return X, y
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100,
              batch_size: int = 32) -> Dict:
        """
        训练模型
        
        Returns:
            训练历史
        """
        if self.model is None:
            self.build_model()
        
        if not TF_AVAILABLE:
            logger.error("Cannot train without TensorFlow")
            return {}
        
        # 回调函数
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        # 训练
        logger.info("Starting LSTM training...")
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # 返回训练历史
        history_dict = {
            'loss': self.history.history['loss'],
            'val_loss': self.history.history['val_loss'],
            'accuracy': self.history.history['accuracy'],
            'val_accuracy': self.history.history['val_accuracy'],
            'auc': self.history.history['auc'],
            'val_auc': self.history.history['val_auc']
        }
        
        logger.info("Training completed")
        
        return history_dict
    
    def predict(self, X: np.ndarray) -> Dict:
        """
        预测
        
        Args:
            X: 输入序列 (1, sequence_length, n_features)
        
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
        
        if not TF_AVAILABLE:
            # Mock prediction
            return {
                'up_probability': 0.5,
                'down_probability': 0.5,
                'prediction': 'hold',
                'confidence': 0.5
            }
        
        # 确保输入维度正确
        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])
        
        # 预测
        pred = self.model.predict(X, verbose=0)
        
        up_prob = float(pred[0][1])
        down_prob = float(pred[0][0])
        
        # 确定预测方向
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
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        评估模型
        
        Returns:
            评估指标
        """
        if self.model is None:
            logger.error("Model not trained")
            return {}
        
        if not TF_AVAILABLE:
            return {'accuracy': 0.5}
        
        # 评估
        loss, accuracy, auc = self.model.evaluate(X_test, y_test, verbose=0)
        
        # 预测
        y_pred = self.model.predict(X_test, verbose=0)
        y_pred_classes = np.argmax(y_pred, axis=1)
        y_true_classes = np.argmax(y_test, axis=1)
        
        # 计算更多指标
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        precision = precision_score(y_true_classes, y_pred_classes, average='weighted')
        recall = recall_score(y_true_classes, y_pred_classes, average='weighted')
        f1 = f1_score(y_true_classes, y_pred_classes, average='weighted')
        
        return {
            'loss': loss,
            'accuracy': accuracy,
            'auc': auc,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.model is not None and TF_AVAILABLE:
            self.model.save(filepath)
            logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        if TF_AVAILABLE:
            self.model = tf.keras.models.load_model(filepath)
            logger.info(f"Model loaded from {filepath}")


class LSTMModelTrainer:
    """LSTM模型训练器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.predictor = LSTMPredictor(**self.config)
    
    def train_model(self, df: pd.DataFrame, 
                    feature_cols: List[str],
                    test_size: float = 0.2,
                    val_size: float = 0.1) -> Dict:
        """
        完整训练流程
        
        Returns:
            训练结果
        """
        # 准备数据
        X, y = self.predictor.prepare_data(df, feature_cols)
        
        # 划分数据集
        n_samples = len(X)
        n_test = int(n_samples * test_size)
        n_val = int(n_samples * val_size)
        n_train = n_samples - n_test - n_val
        
        X_train = X[:n_train]
        y_train = y[:n_train]
        X_val = X[n_train:n_train+n_val]
        y_val = y[n_train:n_train+n_val]
        X_test = X[n_train+n_val:]
        y_test = y[n_train+n_val:]
        
        logger.info(f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        
        # 构建模型
        self.predictor.build_model()
        
        # 训练
        history = self.predictor.train(X_train, y_train, X_val, y_val)
        
        # 评估
        evaluation = self.predictor.evaluate(X_test, y_test)
        
        return {
            'history': history,
            'evaluation': evaluation,
            'model': self.predictor.model
        }


# 便捷函数
def train_lstm_model(df: pd.DataFrame, feature_cols: List[str]) -> LSTMPredictor:
    """便捷函数：训练LSTM模型"""
    trainer = LSTMModelTrainer()
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
        
        # 训练LSTM
        logger.info("Training LSTM model...")
        predictor = train_lstm_model(df_features, feature_cols[:20])  # 使用前20个特征
        
        # 预测测试
        if predictor.model is not None:
            X, _ = predictor.prepare_data(df_features, feature_cols[:20])
            prediction = predictor.predict(X[-1:])
            print(f"\nPrediction: {prediction}")
