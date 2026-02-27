"""
股价预测系统 - 超参数调优模块
自动寻找最优模型参数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """超参数调优器"""
    
    def __init__(self, model_type: str = 'xgboost'):
        """
        Args:
            model_type: 模型类型 ('xgboost', 'lstm', 'transformer')
        """
        self.model_type = model_type
        self.best_params = None
        self.best_score = None
    
    def get_param_grid(self) -> Dict[str, List]:
        """获取参数搜索空间"""
        if self.model_type == 'xgboost':
            return {
                'max_depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'n_estimators': [100, 200, 300],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
                'reg_alpha': [0, 0.1, 1],
                'reg_lambda': [1, 2, 5]
            }
        
        elif self.model_type == 'lstm':
            return {
                'sequence_length': [60, 120, 180],
                'lstm_units': [[64, 32], [128, 64], [128, 64, 32]],
                'dropout_rate': [0.1, 0.2, 0.3],
                'learning_rate': [0.001, 0.0001],
                'batch_size': [16, 32, 64]
            }
        
        elif self.model_type == 'transformer':
            return {
                'd_model': [64, 128, 256],
                'n_heads': [4, 8, 16],
                'n_layers': [2, 4, 6],
                'dropout': [0.1, 0.2],
                'learning_rate': [0.0001, 0.00001]
            }
        
        else:
            return {}
    
    def tune_xgboost(self, X_train, y_train, X_val, y_val,
                    method: str = 'random',
                    n_iter: int = 20) -> Dict:
        """
        调优XGBoost参数
        
        Args:
            X_train, y_train: 训练数据
            X_val, y_val: 验证数据
            method: 'grid' 或 'random'
            n_iter: RandomSearch迭代次数
        
        Returns:
            最优参数
        """
        try:
            from xgboost import XGBClassifier
        except ImportError:
            logger.error("XGBoost not available")
            return {}
        
        param_grid = self.get_param_grid()
        
        model = XGBClassifier(
            objective='binary:logistic',
            eval_metric='auc',
            use_label_encoder=False,
            n_jobs=-1,
            random_state=42
        )
        
        if method == 'grid':
            search = GridSearchCV(
                model, param_grid,
                cv=3,
                scoring='roc_auc',
                n_jobs=-1,
                verbose=1
            )
        else:
            search = RandomizedSearchCV(
                model, param_grid,
                n_iter=n_iter,
                cv=3,
                scoring='roc_auc',
                n_jobs=-1,
                random_state=42,
                verbose=1
            )
        
        logger.info(f"Starting {method} search for XGBoost...")
        search.fit(X_train, y_train)
        
        self.best_params = search.best_params_
        self.best_score = search.best_score_
        
        logger.info(f"Best params: {self.best_params}")
        logger.info(f"Best CV score: {self.best_score:.4f}")
        
        # 在验证集上评估
        val_score = search.score(X_val, y_val)
        logger.info(f"Validation score: {val_score:.4f}")
        
        return {
            'best_params': self.best_params,
            'cv_score': self.best_score,
            'val_score': val_score
        }
    
    def tune_threshold(self, y_true, y_prob,
                       metric: str = 'f1') -> Dict:
        """
        调优分类阈值
        
        Args:
            y_true: 真实标签
            y_prob: 预测概率
            metric: 优化指标 ('f1', 'accuracy', 'precision', 'recall')
        
        Returns:
            最优阈值
        """
        from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score
        
        thresholds = np.arange(0.1, 0.9, 0.05)
        scores = []
        
        metric_func = {
            'f1': f1_score,
            'accuracy': accuracy_score,
            'precision': precision_score,
            'recall': recall_score
        }.get(metric, f1_score)
        
        for threshold in thresholds:
            y_pred = (y_prob >= threshold).astype(int)
            
            try:
                if metric == 'f1':
                    score = metric_func(y_true, y_pred)
                else:
                    score = metric_func(y_true, y_pred)
            except:
                score = 0
            
            scores.append(score)
        
        best_idx = np.argmax(scores)
        best_threshold = thresholds[best_idx]
        best_score = scores[best_idx]
        
        logger.info(f"Best threshold: {best_threshold:.2f} ({metric}={best_score:.4f})")
        
        return {
            'best_threshold': best_threshold,
            'best_score': best_score,
            'thresholds': thresholds.tolist(),
            'scores': scores
        }


class BayesianOptimizer:
    """贝叶斯优化器 (简化版)"""
    
    def __init__(self, param_space: Dict[str, Tuple]):
        """
        Args:
            param_space: 参数空间 {param: (min, max, type)}
        """
        self.param_space = param_space
        self.history = []
    
    def suggest(self) -> Dict:
        """建议下一组参数"""
        # 简化实现：随机采样
        params = {}
        for param, (min_val, max_val, ptype) in self.param_space.items():
            if ptype == 'int':
                params[param] = np.random.randint(min_val, max_val + 1)
            elif ptype == 'float':
                params[param] = np.random.uniform(min_val, max_val)
            elif ptype == 'choice':
                params[param] = np.random.choice(min_val)  # min_val是列表
        
        return params
    
    def update(self, params: Dict, score: float):
        """更新历史记录"""
        self.history.append({**params, 'score': score})
    
    def get_best(self) -> Tuple[Dict, float]:
        """获取最优参数"""
        if not self.history:
            return {}, 0
        
        best = max(self.history, key=lambda x: x['score'])
        score = best.pop('score')
        return best, score


class GeneticAlgorithmOptimizer:
    """遗传算法优化器 (简化版)"""
    
    def __init__(self, param_space: Dict[str, List],
                 population_size: int = 20,
                 generations: int = 10):
        self.param_space = param_space
        self.population_size = population_size
        self.generations = generations
        self.population = []
        self.best_individual = None
        self.best_fitness = -np.inf
    
    def initialize_population(self):
        """初始化种群"""
        for _ in range(self.population_size):
            individual = {
                param: np.random.choice(values)
                for param, values in self.param_space.items()
            }
            self.population.append(individual)
    
    def evaluate_fitness(self, individual: Dict, 
                         fitness_func) -> float:
        """评估适应度"""
        return fitness_func(individual)
    
    def select_parents(self, fitness_scores: List[float]) -> List[Dict]:
        """选择父代"""
        # 轮盘赌选择
        fitness_scores = np.array(fitness_scores)
        fitness_scores = fitness_scores - fitness_scores.min() + 1e-10
        probs = fitness_scores / fitness_scores.sum()
        
        selected = np.random.choice(
            len(self.population),
            size=2,
            replace=False,
            p=probs
        )
        
        return [self.population[i] for i in selected]
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """交叉"""
        child = {}
        for param in self.param_space.keys():
            if np.random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
    
    def mutate(self, individual: Dict, mutation_rate: float = 0.1) -> Dict:
        """变异"""
        mutated = individual.copy()
        
        for param, values in self.param_space.items():
            if np.random.random() < mutation_rate:
                mutated[param] = np.random.choice(values)
        
        return mutated
    
    def optimize(self, fitness_func) -> Dict:
        """执行优化"""
        self.initialize_population()
        
        for generation in range(self.generations):
            # 评估适应度
            fitness_scores = [
                self.evaluate_fitness(ind, fitness_func)
                for ind in self.population
            ]
            
            # 更新最优
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = fitness_scores[best_idx]
                self.best_individual = self.population[best_idx].copy()
            
            logger.info(f"Generation {generation+1}: Best fitness = {self.best_fitness:.4f}")
            
            # 生成新一代
            new_population = [self.best_individual]  # 保留最优
            
            while len(new_population) < self.population_size:
                parents = self.select_parents(fitness_scores)
                child = self.crossover(parents[0], parents[1])
                child = self.mutate(child)
                new_population.append(child)
            
            self.population = new_population
        
        return self.best_individual


# 便捷函数
def tune_model_hyperparameters(model_type: str, X_train, y_train,
                               X_val, y_val) -> Dict:
    """便捷函数：调优模型超参数"""
    tuner = HyperparameterTuner(model_type)
    
    if model_type == 'xgboost':
        return tuner.tune_xgboost(X_train, y_train, X_val, y_val)
    
    return {}


if __name__ == '__main__':
    print("Hyperparameter Tuning Module")
    
    # 测试阈值调优
    y_true = np.array([0, 0, 1, 1, 0, 1, 1, 0, 1, 1])
    y_prob = np.array([0.1, 0.3, 0.4, 0.6, 0.2, 0.7, 0.8, 0.3, 0.9, 0.85])
    
    tuner = HyperparameterTuner()
    result = tuner.tune_threshold(y_true, y_prob, metric='f1')
    
    print(f"\nThreshold Tuning Result:")
    print(f"  Best threshold: {result['best_threshold']:.2f}")
    print(f"  Best F1 score: {result['best_score']:.4f}")
