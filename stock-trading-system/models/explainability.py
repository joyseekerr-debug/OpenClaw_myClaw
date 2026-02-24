"""
SHAP模型解释性分析
解释模型预测结果和特征贡献
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP解释器"""
    
    def __init__(self, model, model_type: str = 'tree'):
        """
        初始化SHAP解释器
        
        Args:
            model: 训练好的模型
            model_type: 'tree' (XGBoost/LightGBM) 或 'deep' (LSTM/Transformer)
        """
        self.model = model
        self.model_type = model_type
        self.explainer = None
        self.shap_values = None
        
    def build_explainer(self, X_background: Optional[np.ndarray] = None):
        """
        构建SHAP解释器
        
        Args:
            X_background: 背景数据（用于解释）
        """
        try:
            import shap
            
            if self.model_type == 'tree':
                # 树模型使用TreeExplainer
                self.explainer = shap.TreeExplainer(self.model.model)
                logger.info("✅ TreeExplainer构建完成")
                
            elif self.model_type == 'deep':
                # 深度学习模型使用DeepExplainer
                if X_background is None:
                    raise ValueError("深度学习模型需要提供背景数据")
                
                import torch
                self.explainer = shap.DeepExplainer(self.model.model, 
                                                   torch.FloatTensor(X_background))
                logger.info("✅ DeepExplainer构建完成")
                
            else:
                # 其他模型使用KernelExplainer
                if X_background is None:
                    raise ValueError("KernelExplainer需要提供背景数据")
                
                self.explainer = shap.KernelExplainer(self.model.predict, X_background)
                logger.info("✅ KernelExplainer构建完成")
                
        except ImportError:
            logger.error("❌ SHAP库未安装，无法使用解释功能")
            raise
    
    def explain(self, X: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """
        解释预测结果
        
        Args:
            X: 待解释的特征数据
            feature_names: 特征名称
        
        Returns:
            SHAP解释结果
        """
        if self.explainer is None:
            logger.warning("⚠️ 解释器未构建，尝试自动构建...")
            self.build_explainer()
        
        try:
            import shap
            
            # 计算SHAP值
            self.shap_values = self.explainer.shap_values(X)
            
            # 处理多输出情况（取第一个输出）
            if isinstance(self.shap_values, list):
                self.shap_values = self.shap_values[0]
            
            # 构建解释结果
            results = {
                'shap_values': self.shap_values,
                'base_value': self.explainer.expected_value,
                'feature_names': feature_names,
                'feature_importance': self._calculate_feature_importance(feature_names)
            }
            
            logger.info(f"✅ SHAP解释完成: {len(feature_names)} 个特征")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ SHAP解释失败: {e}")
            raise
    
    def _calculate_feature_importance(self, feature_names: List[str]) -> pd.DataFrame:
        """计算特征重要性（基于SHAP值绝对值的平均）"""
        if self.shap_values is None:
            return pd.DataFrame()
        
        # 计算平均绝对SHAP值
        mean_shap = np.abs(self.shap_values).mean(axis=0)
        
        # 如果是序列数据，需要展平
        if len(mean_shap.shape) > 1:
            mean_shap = mean_shap.flatten()
        
        # 构建DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names[:len(mean_shap)],
            'shap_importance': mean_shap[:len(feature_names)]
        })
        
        importance_df = importance_df.sort_values('shap_importance', ascending=False)
        
        return importance_df
    
    def explain_single_prediction(self, X: np.ndarray, feature_names: List[str],
                                 idx: int = 0) -> Dict[str, Any]:
        """
        解释单个预测结果
        
        Args:
            X: 特征数据
            feature_names: 特征名称
            idx: 样本索引
        
        Returns:
            单样本解释结果
        """
        if self.shap_values is None:
            self.explain(X, feature_names)
        
        # 获取指定样本的SHAP值
        sample_shap = self.shap_values[idx]
        
        # 如果是序列数据，取最后一个时间步
        if len(sample_shap.shape) > 1:
            sample_shap = sample_shap[-1]
        
        # 特征贡献
        contributions = []
        for i, (name, shap_val) in enumerate(zip(feature_names, sample_shap)):
            contributions.append({
                'feature': name,
                'shap_value': shap_val,
                'impact': '正向' if shap_val > 0 else '负向',
                'magnitude': abs(shap_val)
            })
        
        # 按贡献绝对值排序
        contributions.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return {
            'base_value': self.explainer.expected_value,
            'prediction': self.explainer.expected_value + np.sum(sample_shap),
            'top_features': contributions[:10],
            'all_contributions': contributions
        }
    
    def plot_summary(self, X: np.ndarray, feature_names: List[str],
                    save_path: Optional[str] = None):
        """
        绘制SHAP摘要图
        
        Args:
            X: 特征数据
            feature_names: 特征名称
            save_path: 保存路径
        """
        try:
            import shap
            import matplotlib.pyplot as plt
            
            if self.shap_values is None:
                self.explain(X, feature_names)
            
            plt.figure(figsize=(10, 8))
            shap.summary_plot(self.shap_values, X, feature_names=feature_names,
                            show=False)
            plt.title("SHAP Feature Importance")
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"📊 SHAP摘要图已保存: {save_path}")
            
            plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib或shap未安装，无法绘图")
    
    def plot_waterfall(self, X: np.ndarray, feature_names: List[str],
                      idx: int = 0, save_path: Optional[str] = None):
        """
        绘制瀑布图（单样本解释）
        
        Args:
            X: 特征数据
            feature_names: 特征名称
            idx: 样本索引
            save_path: 保存路径
        """
        try:
            import shap
            import matplotlib.pyplot as plt
            
            if self.shap_values is None:
                self.explain(X, feature_names)
            
            plt.figure(figsize=(10, 6))
            
            # 创建Explanation对象
            explanation = shap.Explanation(
                values=self.shap_values[idx],
                base_values=self.explainer.expected_value,
                data=X[idx],
                feature_names=feature_names
            )
            
            shap.waterfall_plot(explanation, show=False)
            plt.title(f"SHAP Waterfall Plot (Sample {idx})")
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"📊 SHAP瀑布图已保存: {save_path}")
            
            plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib或shap未安装，无法绘图")
    
    def get_feature_interactions(self, X: np.ndarray, feature_names: List[str],
                                top_n: int = 10) -> pd.DataFrame:
        """
        分析特征交互作用
        
        Args:
            X: 特征数据
            feature_names: 特征名称
            top_n: 返回前N个交互
        
        Returns:
            特征交互DataFrame
        """
        try:
            import shap
            
            if self.shap_values is None:
                self.explain(X, feature_names)
            
            # 计算特征交互SHAP值
            interaction_values = self.explainer.shap_interaction_values(X)
            
            # 如果是列表，取第一个输出
            if isinstance(interaction_values, list):
                interaction_values = interaction_values[0]
            
            # 计算平均交互强度
            mean_interaction = np.abs(interaction_values).mean(axis=0)
            
            # 提取非对角线元素（特征间交互）
            interactions = []
            n = len(feature_names)
            for i in range(n):
                for j in range(i+1, n):
                    interactions.append({
                        'feature_1': feature_names[i],
                        'feature_2': feature_names[j],
                        'interaction_strength': mean_interaction[i, j]
                    })
            
            # 排序
            interactions_df = pd.DataFrame(interactions)
            interactions_df = interactions_df.sort_values('interaction_strength', 
                                                          ascending=False)
            
            return interactions_df.head(top_n)
            
        except Exception as e:
            logger.error(f"❌ 特征交互分析失败: {e}")
            return pd.DataFrame()
    
    def generate_report(self, X: np.ndarray, feature_names: List[str],
                       n_samples: int = 5) -> str:
        """
        生成解释报告
        
        Args:
            X: 特征数据
            feature_names: 特征名称
            n_samples: 解释的样本数
        
        Returns:
            报告文本
        """
        if self.shap_values is None:
            self.explain(X, feature_names)
        
        report = []
        report.append("="*70)
        report.append("SHAP模型解释报告")
        report.append("="*70)
        
        # 1. 全局特征重要性
        report.append("\n【全局特征重要性】")
        importance_df = self._calculate_feature_importance(feature_names)
        report.append(importance_df.head(10).to_string(index=False))
        
        # 2. 单样本解释
        report.append(f"\n【单样本解释 (前{n_samples}个样本)】")
        for i in range(min(n_samples, len(X))):
            explanation = self.explain_single_prediction(X, feature_names, idx=i)
            report.append(f"\n样本 {i}:")
            report.append(f"  基准值: {explanation['base_value']:.6f}")
            report.append(f"  预测值: {explanation['prediction']:.6f}")
            report.append(f"  主要影响因素:")
            for feat in explanation['top_features'][:5]:
                report.append(f"    - {feat['feature']}: {feat['shap_value']:.6f} ({feat['impact']})")
        
        report.append("\n" + "="*70)
        
        return "\n".join(report)


class PredictionExplainer:
    """预测结果解释器（简化版，不依赖SHAP）"""
    
    def __init__(self, model):
        self.model = model
    
    def explain_with_feature_importance(self, X: np.ndarray, 
                                       feature_names: List[str]) -> pd.DataFrame:
        """
        使用模型内置的特征重要性进行解释
        
        Args:
            X: 特征数据
            feature_names: 特征名称
        
        Returns:
            特征重要性DataFrame
        """
        importance = self.model.get_feature_importance()
        
        if not importance:
            logger.warning("⚠️ 模型没有提供特征重要性")
            return pd.DataFrame()
        
        # 映射到特征名
        df = pd.DataFrame([
            {'feature': feature_names[i], 'importance': imp}
            for i, imp in enumerate(importance.values())
            if i < len(feature_names)
        ])
        
        df = df.sort_values('importance', ascending=False)
        
        return df
    
    def explain_prediction_change(self, X_base: np.ndarray, 
                                  X_changed: np.ndarray,
                                  feature_names: List[str],
                                  changed_features: List[str]) -> Dict[str, Any]:
        """
        解释特征变化对预测的影响
        
        Args:
            X_base: 基准特征
            X_changed: 改变后的特征
            feature_names: 所有特征名
            changed_features: 改变的特征名
        
        Returns:
            变化解释
        """
        # 基准预测
        pred_base = self.model.predict(X_base.reshape(1, -1))[0]
        
        # 改变后预测
        pred_changed = self.model.predict(X_changed.reshape(1, -1))[0]
        
        # 变化量
        change = pred_changed - pred_base
        
        # 改变的特征值
        feature_changes = []
        for feat in changed_features:
            idx = feature_names.index(feat)
            old_val = X_base[idx]
            new_val = X_changed[idx]
            feature_changes.append({
                'feature': feat,
                'old_value': old_val,
                'new_value': new_val,
                'change': new_val - old_val,
                'change_pct': (new_val - old_val) / old_val * 100 if old_val != 0 else 0
            })
        
        return {
            'prediction_base': pred_base,
            'prediction_changed': pred_changed,
            'prediction_change': change,
            'prediction_change_pct': change / pred_base * 100 if pred_base != 0 else 0,
            'feature_changes': feature_changes,
            'direction': '上涨' if change > 0 else '下跌' if change < 0 else '持平'
        }


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("SHAP模型解释性模块")
    print("="*70)
    
    print("\n✅ SHAP解释器模块就绪")
    print("   • 支持树模型解释 (XGBoost/LightGBM)")
    print("   • 支持深度学习模型解释 (LSTM/Transformer)")
    print("   • 提供摘要图、瀑布图、交互分析")
    print("="*70)
