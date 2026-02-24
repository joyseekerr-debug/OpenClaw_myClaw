"""
Phase 2: 多时间尺度预测模型
包含LSTM、XGBoost、Transformer三种模型
支持1分钟/5分钟/15分钟/日线/周线多时间尺度
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """预测模型基类"""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.model = None
        self.is_trained = False
        self.feature_names = []
    
    @abstractmethod
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: Optional[np.ndarray] = None, 
              y_val: Optional[np.ndarray] = None) -> dict:
        """训练模型"""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        pass
    
    @abstractmethod
    def save(self, path: str):
        """保存模型"""
        pass
    
    @abstractmethod
    def load(self, path: str):
        """加载模型"""
        pass
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性（可选实现）"""
        return {}


class LSTMModel(BaseModel):
    """
    LSTM深度学习模型
    适用于: 捕捉时间序列长期依赖关系
    时间尺度: 1分钟/5分钟/15分钟高频数据
    """
    
    def __init__(self, config: dict = None):
        default_config = {
            'sequence_length': 60,
            'hidden_units': 128,
            'num_layers': 2,
            'dropout': 0.2,
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 100,
            'early_stopping_patience': 10
        }
        default_config.update(config or {})
        super().__init__('LSTM', default_config)
        
        self.sequence_length = self.config['sequence_length']
        self.hidden_units = self.config['hidden_units']
        self.scaler = None
    
    def build_model(self, input_shape: Tuple[int, int]):
        """构建LSTM模型"""
        try:
            import torch
            import torch.nn as nn
            
            class LSTMNetwork(nn.Module):
                def __init__(self, input_size, hidden_size, num_layers, dropout, output_size=1):
                    super().__init__()
                    self.hidden_size = hidden_size
                    self.num_layers = num_layers
                    
                    self.lstm = nn.LSTM(
                        input_size=input_size,
                        hidden_size=hidden_size,
                        num_layers=num_layers,
                        dropout=dropout if num_layers > 1 else 0,
                        batch_first=True
                    )
                    
                    self.dropout = nn.Dropout(dropout)
                    self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
                    self.fc2 = nn.Linear(hidden_size // 2, output_size)
                    self.relu = nn.ReLU()
                
                def forward(self, x):
                    lstm_out, _ = self.lstm(x)
                    out = self.dropout(lstm_out[:, -1, :])  # 取最后一个时间步
                    out = self.fc1(out)
                    out = self.relu(out)
                    out = self.fc2(out)
                    return out
            
            self.model = LSTMNetwork(
                input_size=input_shape[1],
                hidden_size=self.hidden_units,
                num_layers=self.config['num_layers'],
                dropout=self.config['dropout']
            )
            
            self.criterion = nn.MSELoss()
            self.optimizer = torch.optim.Adam(
                self.model.parameters(), 
                lr=self.config['learning_rate']
            )
            
            logger.info(f"✅ LSTM模型构建完成: {input_shape} -> hidden={self.hidden_units}")
            
        except ImportError:
            logger.error("❌ PyTorch未安装，无法使用LSTM模型")
            raise
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> dict:
        """训练LSTM模型"""
        import torch
        from sklearn.preprocessing import StandardScaler
        
        # 数据归一化
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val.reshape(-1, X_val.shape[-1])).reshape(X_val.shape)
        
        # 构建模型
        if self.model is None:
            self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # 转换为Tensor
        X_train_tensor = torch.FloatTensor(X_train_scaled)
        y_train_tensor = torch.FloatTensor(y_train).view(-1, 1)
        
        train_dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = torch.utils.data.DataLoader(
            train_dataset, 
            batch_size=self.config['batch_size'], 
            shuffle=True
        )
        
        # 训练循环
        best_val_loss = float('inf')
        patience_counter = 0
        history = {'train_loss': [], 'val_loss': []}
        
        for epoch in range(self.config['epochs']):
            self.model.train()
            train_loss = 0
            
            for batch_X, batch_y in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            history['train_loss'].append(avg_train_loss)
            
            # 验证
            if X_val is not None:
                self.model.eval()
                with torch.no_grad():
                    X_val_tensor = torch.FloatTensor(X_val_scaled)
                    y_val_tensor = torch.FloatTensor(y_val).view(-1, 1)
                    val_outputs = self.model(X_val_tensor)
                    val_loss = self.criterion(val_outputs, y_val_tensor).item()
                    history['val_loss'].append(val_loss)
                    
                    # Early stopping
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        patience_counter = 0
                    else:
                        patience_counter += 1
                        
                    if patience_counter >= self.config['early_stopping_patience']:
                        logger.info(f"⏹️ Early stopping at epoch {epoch}")
                        break
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{self.config['epochs']}, "
                          f"Train Loss: {avg_train_loss:.6f}")
        
        self.is_trained = True
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        import torch
        
        self.model.eval()
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled)
        
        with torch.no_grad():
            predictions = self.model(X_tensor).numpy()
        
        return predictions.flatten()
    
    def save(self, path: str):
        """保存模型"""
        import torch
        import pickle
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'scaler': self.scaler
        }, path)
        logger.info(f"💾 LSTM模型已保存: {path}")
    
    def load(self, path: str):
        """加载模型"""
        import torch
        
        checkpoint = torch.load(path)
        self.config = checkpoint['config']
        self.scaler = checkpoint['scaler']
        
        # 重建模型
        self.build_model((self.sequence_length, self.config.get('input_size', 30)))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        self.is_trained = True
        logger.info(f"📂 LSTM模型已加载: {path}")


class XGBoostModel(BaseModel):
    """
    XGBoost机器学习模型
    适用于: 中频数据，特征重要性分析
    时间尺度: 15分钟/60分钟/日线
    """
    
    def __init__(self, config: dict = None):
        default_config = {
            'n_estimators': 1000,
            'max_depth': 8,
            'learning_rate': 0.01,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'early_stopping_rounds': 50,
            'eval_metric': 'rmse'
        }
        default_config.update(config or {})
        super().__init__('XGBoost', default_config)
    
    def build_model(self):
        """构建XGBoost模型"""
        try:
            import xgboost as xgb
            
            self.model = xgb.XGBRegressor(
                n_estimators=self.config['n_estimators'],
                max_depth=self.config['max_depth'],
                learning_rate=self.config['learning_rate'],
                subsample=self.config['subsample'],
                colsample_bytree=self.config['colsample_bytree'],
                eval_metric=self.config['eval_metric'],
                random_state=42,
                n_jobs=-1
            )
            
            logger.info(f"✅ XGBoost模型构建完成: {self.config['n_estimators']} estimators")
            
        except ImportError:
            logger.error("❌ XGBoost未安装")
            raise
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> dict:
        """训练XGBoost模型"""
        if self.model is None:
            self.build_model()
        
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            early_stopping_rounds=self.config['early_stopping_rounds'],
            verbose=False
        )
        
        self.is_trained = True
        
        # 获取训练历史
        results = self.model.evals_result()
        
        logger.info(f"✅ XGBoost训练完成: best_iteration={self.model.best_iteration}")
        
        return results
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.is_trained:
            return {}
        
        importance = self.model.feature_importances_
        return {f"feature_{i}": imp for i, imp in enumerate(importance)}
    
    def save(self, path: str):
        """保存模型"""
        self.model.save_model(path)
        logger.info(f"💾 XGBoost模型已保存: {path}")
    
    def load(self, path: str):
        """加载模型"""
        import xgboost as xgb
        self.model = xgb.XGBRegressor()
        self.model.load_model(path)
        self.is_trained = True
        logger.info(f"📂 XGBoost模型已加载: {path}")


class TransformerModel(BaseModel):
    """
    Transformer模型
    适用于: 长序列依赖捕捉
    时间尺度: 日线/周线长周期数据
    """
    
    def __init__(self, config: dict = None):
        default_config = {
            'd_model': 64,
            'nhead': 4,
            'num_layers': 3,
            'dim_feedforward': 256,
            'dropout': 0.1,
            'learning_rate': 0.0001,
            'batch_size': 32,
            'epochs': 100
        }
        default_config.update(config or {})
        super().__init__('Transformer', default_config)
    
    def build_model(self, input_size: int):
        """构建Transformer模型"""
        try:
            import torch
            import torch.nn as nn
            
            class TransformerNetwork(nn.Module):
                def __init__(self, input_size, d_model, nhead, num_layers, 
                            dim_feedforward, dropout, output_size=1):
                    super().__init__()
                    
                    self.input_projection = nn.Linear(input_size, d_model)
                    
                    encoder_layer = nn.TransformerEncoderLayer(
                        d_model=d_model,
                        nhead=nhead,
                        dim_feedforward=dim_feedforward,
                        dropout=dropout,
                        batch_first=True
                    )
                    self.transformer_encoder = nn.TransformerEncoder(
                        encoder_layer, 
                        num_layers=num_layers
                    )
                    
                    self.decoder = nn.Sequential(
                        nn.Linear(d_model, d_model // 2),
                        nn.ReLU(),
                        nn.Dropout(dropout),
                        nn.Linear(d_model // 2, output_size)
                    )
                
                def forward(self, x):
                    # x: (batch, seq_len, features)
                    x = self.input_projection(x)
                    x = self.transformer_encoder(x)
                    x = x[:, -1, :]  # 取最后一个时间步
                    x = self.decoder(x)
                    return x
            
            self.model = TransformerNetwork(
                input_size=input_size,
                d_model=self.config['d_model'],
                nhead=self.config['nhead'],
                num_layers=self.config['num_layers'],
                dim_feedforward=self.config['dim_feedforward'],
                dropout=self.config['dropout']
            )
            
            self.criterion = nn.MSELoss()
            self.optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=self.config['learning_rate']
            )
            
            logger.info(f"✅ Transformer模型构建完成: d_model={self.config['d_model']}")
            
        except ImportError:
            logger.error("❌ PyTorch未安装")
            raise
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> dict:
        """训练Transformer模型"""
        import torch
        
        if self.model is None:
            self.build_model(X_train.shape[-1])
        
        # 转换为Tensor
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train).view(-1, 1)
        
        train_dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=self.config['batch_size'],
            shuffle=True
        )
        
        history = {'train_loss': []}
        
        for epoch in range(self.config['epochs']):
            self.model.train()
            train_loss = 0
            
            for batch_X, batch_y in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item()
            
            avg_loss = train_loss / len(train_loader)
            history['train_loss'].append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{self.config['epochs']}, Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        import torch
        
        self.model.eval()
        X_tensor = torch.FloatTensor(X)
        
        with torch.no_grad():
            predictions = self.model(X_tensor).numpy()
        
        return predictions.flatten()
    
    def save(self, path: str):
        """保存模型"""
        import torch
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"💾 Transformer模型已保存: {path}")
    
    def load(self, path: str):
        """加载模型"""
        import torch
        checkpoint = torch.load(path)
        self.config = checkpoint['config']
        # 重建并加载
        self.build_model(self.config.get('input_size', 30))
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        logger.info(f"📂 Transformer模型已加载: {path}")


class MultiTimeframeEnsemble:
    """
    多时间尺度集成模型
    整合不同时间尺度的预测结果
    """
    
    def __init__(self):
        self.models = {}  # 存储不同时间尺度的模型
        self.weights = {}  # 各模型权重
        self.timeframes = ['1min', '5min', '15min', '1h', '1d', '1w']
    
    def add_model(self, timeframe: str, model: BaseModel, weight: float = 1.0):
        """添加时间尺度模型"""
        self.models[timeframe] = model
        self.weights[timeframe] = weight
        logger.info(f"✅ 添加模型: {timeframe} ({model.name}), weight={weight}")
    
    def predict(self, timeframe_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        多时间尺度预测
        
        Args:
            timeframe_data: 各时间尺度的特征数据 {timeframe: X}
        
        Returns:
            各时间尺度的预测结果
        """
        predictions = {}
        
        for timeframe, X in timeframe_data.items():
            if timeframe in self.models:
                model = self.models[timeframe]
                pred = model.predict(X)
                predictions[timeframe] = pred
        
        return predictions
    
    def ensemble_predict(self, timeframe_data: Dict[str, np.ndarray],
                        method: str = 'weighted_average') -> np.ndarray:
        """
        集成预测
        
        Args:
            timeframe_data: 各时间尺度的特征数据
            method: 'weighted_average', 'voting', 'stacking'
        
        Returns:
            集成后的预测结果
        """
        predictions = self.predict(timeframe_data)
        
        if not predictions:
            raise ValueError("没有可用的预测结果")
        
        if method == 'weighted_average':
            # 加权平均
            weighted_sum = None
            total_weight = 0
            
            for timeframe, pred in predictions.items():
                weight = self.weights.get(timeframe, 1.0)
                if weighted_sum is None:
                    weighted_sum = pred * weight
                else:
                    weighted_sum += pred * weight
                total_weight += weight
            
            return weighted_sum / total_weight
        
        elif method == 'voting':
            # 投票法（分类问题）
            # 这里简化为平均
            return np.mean(list(predictions.values()), axis=0)
        
        else:
            raise ValueError(f"未知的集成方法: {method}")
    
    def optimize_weights(self, timeframe_data: Dict[str, np.ndarray],
                        y_true: np.ndarray,
                        metric: str = 'mse'):
        """优化各时间尺度模型的权重"""
        from scipy.optimize import minimize
        
        predictions = self.predict(timeframe_data)
        timeframes = list(predictions.keys())
        
        def objective(weights):
            # 加权预测
            weighted_pred = np.zeros_like(y_true, dtype=float)
            for i, tf in enumerate(timeframes):
                weighted_pred += weights[i] * predictions[tf]
            
            # 计算损失
            if metric == 'mse':
                return np.mean((y_true - weighted_pred) ** 2)
            elif metric == 'mae':
                return np.mean(np.abs(y_true - weighted_pred))
            else:
                return np.mean((y_true - weighted_pred) ** 2)
        
        # 约束：权重和为1，非负
        n = len(timeframes)
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(n)]
        initial_weights = [1/n] * n
        
        result = minimize(objective, initial_weights, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        # 更新权重
        for i, tf in enumerate(timeframes):
            self.weights[tf] = result.x[i]
        
        logger.info(f"✅ 权重优化完成: {self.weights}")
        return self.weights


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("多时间尺度预测模型 - Phase 2 模块")
    print("="*70)
    
    # 示例：创建各时间尺度的模型
    models = {
        '1min': LSTMModel({'sequence_length': 60, 'hidden_units': 64}),
        '5min': LSTMModel({'sequence_length': 48, 'hidden_units': 128}),
        '15min': XGBoostModel({'n_estimators': 500, 'max_depth': 6}),
        '1h': XGBoostModel({'n_estimators': 800, 'max_depth': 8}),
        '1d': TransformerModel({'d_model': 64, 'nhead': 4, 'num_layers': 3}),
        '1w': TransformerModel({'d_model': 32, 'nhead': 2, 'num_layers': 2})
    }
    
    print("\n📊 模型配置:")
    for timeframe, model in models.items():
        print(f"   {timeframe}: {model.name}")
    
    # 创建集成模型
    ensemble = MultiTimeframeEnsemble()
    for timeframe, model in models.items():
        ensemble.add_model(timeframe, model, weight=1.0)
    
    print("\n✅ Phase 2 模型模块初始化完成")
    print("="*70)
