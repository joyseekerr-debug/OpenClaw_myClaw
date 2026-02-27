"""
股价预测系统 - Transformer低频预测模型
适用于日线和周线时间框架
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
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import (
        Dense, Dropout, LayerNormalization, GlobalAveragePooling1D,
        Input, Embedding
    )
    TF_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not available")
    TF_AVAILABLE = False


class PositionalEncoding:
    """位置编码"""
    
    @staticmethod
    def create(sequence_length: int, d_model: int) -> np.ndarray:
        """
        创建正弦位置编码
        
        Args:
            sequence_length: 序列长度
            d_model: 模型维度
        
        Returns:
            位置编码矩阵
        """
        position = np.arange(sequence_length)[:, np.newaxis]
        div_term = np.exp(
            np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model)
        )
        
        pe = np.zeros((sequence_length, d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe


class TransformerBlock:
    """Transformer编码器块"""
    
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_ff = d_ff
        self.dropout = dropout
    
    def __call__(self, x, training=False):
        if not TF_AVAILABLE:
            return x
        
        import tensorflow as tf
        from tensorflow.keras import layers
        
        # 多头自注意力
        attn_output = layers.MultiHeadAttention(
            num_heads=self.n_heads,
            key_dim=self.d_model // self.n_heads
        )(x, x, training=training)
        
        # 残差连接 + Layer Norm
        x = layers.LayerNormalization()(x + attn_output)
        
        # 前馈网络
        ff_output = layers.Dense(self.d_ff, activation='relu')(x)
        ff_output = layers.Dense(self.d_model)(ff_output)
        ff_output = layers.Dropout(self.dropout)(ff_output, training=training)
        
        # 残差连接 + Layer Norm
        x = layers.LayerNormalization()(x + ff_output)
        
        return x


class TransformerPredictor:
    """Transformer低频预测器"""
    
    def __init__(self,
                 sequence_length: int = 60,
                 d_model: int = 128,
                 n_heads: int = 8,
                 n_layers: int = 4,
                 d_ff: int = 512,
                 dropout: float = 0.1,
                 learning_rate: float = 0.0001):
        """
        Args:
            sequence_length: 序列长度 (60个交易日)
            d_model: 模型维度
            n_heads: 注意力头数
            n_layers: Transformer层数
            d_ff: 前馈网络维度
            dropout: Dropout比率
            learning_rate: 学习率
        """
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.model = None
    
    def build_model(self, n_features: int):
        """构建Transformer模型"""
        if not TF_AVAILABLE:
            logger.error("TensorFlow not available")
            return None
        
        # 输入层
        inputs = Input(shape=(self.sequence_length, n_features))
        
        # 线性投影到d_model维度
        x = Dense(self.d_model)(inputs)
        
        # 添加位置编码
        pos_encoding = PositionalEncoding.create(self.sequence_length, self.d_model)
        pos_encoding = tf.constant(pos_encoding[np.newaxis, ...], dtype=tf.float32)
        x = x + pos_encoding
        
        # Transformer编码器层
        for _ in range(self.n_layers):
            transformer_block = TransformerBlock(
                d_model=self.d_model,
                n_heads=self.n_heads,
                d_ff=self.d_ff,
                dropout=self.dropout
            )
            x = transformer_block(x)
        
        # 全局平均池化
        x = GlobalAveragePooling1D()(x)
        
        # 全连接层
        x = Dense(128, activation='relu')(x)
        x = Dropout(self.dropout)(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(self.dropout)(x)
        
        # 输出层
        outputs = Dense(2, activation='softmax', name='direction')(x)
        
        # 构建模型
        model = Model(inputs=inputs, outputs=outputs)
        
        # 编译
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )
        
        self.model = model
        logger.info(f"Transformer model built with {model.count_params()} parameters")
        
        return model
    
    def prepare_data(self, df: pd.DataFrame,
                     feature_cols: List[str],
                     target_col: str = 'target_direction_1') -> Tuple[np.ndarray, np.ndarray]:
        """准备数据"""
        data = df[feature_cols].values
        targets = df[target_col].values
        
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(targets[i + self.sequence_length])
        
        X = np.array(X)
        y = np.array(y)
        
        # One-hot编码
        if TF_AVAILABLE:
            y = tf.keras.utils.to_categorical(y, num_classes=2)
        
        logger.info(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
        
        return X, y
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100,
              batch_size: int = 32) -> Dict:
        """训练模型"""
        if self.model is None:
            logger.error("Model not built")
            return {}
        
        if not TF_AVAILABLE:
            return {}
        
        # 回调
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]
        
        logger.info("Starting Transformer training...")
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return {
            'loss': history.history['loss'],
            'val_loss': history.history['val_loss'],
            'accuracy': history.history['accuracy'],
            'val_accuracy': history.history['val_accuracy']
        }
    
    def predict(self, X: np.ndarray) -> Dict:
        """预测"""
        if self.model is None:
            return {}
        
        if not TF_AVAILABLE:
            return {
                'up_probability': 0.5,
                'down_probability': 0.5,
                'prediction': 'hold',
                'confidence': 0.5
            }
        
        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])
        
        prob = self.model.predict(X, verbose=0)
        
        up_prob = float(prob[0][1])
        down_prob = float(prob[0][0])
        
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
        """评估"""
        if self.model is None:
            return {}
        
        if not TF_AVAILABLE:
            return {'accuracy': 0.5}
        
        loss, accuracy, auc = self.model.evaluate(X_test, y_test, verbose=0)
        
        return {
            'loss': loss,
            'accuracy': accuracy,
            'auc': auc
        }


# 便捷函数
def train_transformer_model(df: pd.DataFrame, feature_cols: List[str]) -> TransformerPredictor:
    """便捷函数：训练Transformer模型"""
    predictor = TransformerPredictor()
    X, y = predictor.prepare_data(df, feature_cols)
    
    # 划分数据
    n = len(X)
    n_train = int(n * 0.7)
    n_val = int(n * 0.15)
    
    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:n_train+n_val], y[n_train:n_train+n_val]
    X_test, y_test = X[n_train+n_val:], y[n_train+n_val:]
    
    # 构建和训练
    predictor.build_model(n_features=len(feature_cols))
    predictor.train(X_train, y_train, X_val, y_val)
    
    return predictor


if __name__ == '__main__':
    logger.info("Transformer model module loaded")
