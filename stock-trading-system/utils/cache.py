"""
Redis缓存管理模块
用于缓存热点数据、特征、模型预测结果
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = None
        self.is_connected = False
        
        self._connect()
    
    def _connect(self):
        """连接Redis"""
        try:
            import redis
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # 保持二进制
                socket_connect_timeout=5
            )
            self.client.ping()
            self.is_connected = True
            logger.info(f"✅ Redis连接成功 {self.host}:{self.port}")
        except ImportError:
            logger.warning("⚠️ redis库未安装，使用本地内存缓存")
            self._init_local_cache()
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}，使用本地内存缓存")
            self._init_local_cache()
    
    def _init_local_cache(self):
        """初始化本地内存缓存（降级方案）"""
        self.is_connected = False
        self.local_cache = {}
        logger.info("使用本地内存缓存")
    
    def _make_key(self, key: str) -> str:
        """生成缓存key"""
        return f"stock_trading:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        full_key = self._make_key(key)
        
        try:
            if self.is_connected:
                data = self.client.get(full_key)
                if data:
                    return pickle.loads(data)
            else:
                # 本地缓存
                if full_key in self.local_cache:
                    item = self.local_cache[full_key]
                    if item['expire'] > datetime.now():
                        return item['value']
                    else:
                        del self.local_cache[full_key]
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any, expire: int = 3600):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)，默认1小时
        """
        full_key = self._make_key(key)
        
        try:
            if self.is_connected:
                serialized = pickle.dumps(value)
                self.client.setex(full_key, expire, serialized)
            else:
                # 本地缓存
                self.local_cache[full_key] = {
                    'value': value,
                    'expire': datetime.now() + timedelta(seconds=expire)
                }
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        full_key = self._make_key(key)
        
        try:
            if self.is_connected:
                self.client.delete(full_key)
            else:
                if full_key in self.local_cache:
                    del self.local_cache[full_key]
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        full_key = self._make_key(key)
        
        try:
            if self.is_connected:
                return self.client.exists(full_key) > 0
            else:
                if full_key in self.local_cache:
                    item = self.local_cache[full_key]
                    if item['expire'] > datetime.now():
                        return True
                    del self.local_cache[full_key]
                return False
        except Exception as e:
            logger.error(f"缓存检查失败: {e}")
            return False
    
    def clear_pattern(self, pattern: str):
        """清除符合pattern的所有key"""
        try:
            if self.is_connected:
                full_pattern = self._make_key(pattern)
                keys = self.client.keys(full_pattern + "*")
                if keys:
                    self.client.delete(*keys)
            else:
                # 本地缓存清除
                keys_to_delete = [k for k in self.local_cache.keys() if k.startswith(self._make_key(pattern))]
                for k in keys_to_delete:
                    del self.local_cache[k]
        except Exception as e:
            logger.error(f"缓存清除失败: {e}")
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        try:
            if self.is_connected:
                info = self.client.info()
                return {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_keys': self.client.dbsize(),
                    'type': 'redis'
                }
            else:
                return {
                    'total_keys': len(self.local_cache),
                    'type': 'local'
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}


class FeatureCache:
    """特征缓存专用类"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def _feature_key(self, symbol: str, timestamp: str, feature_name: str) -> str:
        """生成特征缓存key"""
        return f"feature:{symbol}:{timestamp}:{feature_name}"
    
    def get_feature(self, symbol: str, timestamp: str, feature_name: str) -> Optional[float]:
        """获取特征值"""
        key = self._feature_key(symbol, timestamp, feature_name)
        return self.cache.get(key)
    
    def set_feature(self, symbol: str, timestamp: str, feature_name: str, value: float):
        """设置特征值"""
        key = self._feature_key(symbol, timestamp, feature_name)
        # 特征缓存24小时
        self.cache.set(key, value, expire=86400)
    
    def get_features_batch(self, symbol: str, timestamps: list, feature_names: list) -> dict:
        """批量获取特征"""
        result = {}
        for ts in timestamps:
            result[ts] = {}
            for feat in feature_names:
                value = self.get_feature(symbol, ts, feat)
                if value is not None:
                    result[ts][feat] = value
        return result
    
    def set_features_batch(self, symbol: str, timestamp: str, features: dict):
        """批量设置特征"""
        for feat_name, value in features.items():
            self.set_feature(symbol, timestamp, feat_name, value)


class PredictionCache:
    """预测结果缓存"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def _prediction_key(self, symbol: str, model_name: str, timestamp: str) -> str:
        """生成预测缓存key"""
        return f"pred:{symbol}:{model_name}:{timestamp}"
    
    def get_prediction(self, symbol: str, model_name: str, timestamp: str) -> Optional[dict]:
        """获取预测结果"""
        key = self._prediction_key(symbol, model_name, timestamp)
        return self.cache.get(key)
    
    def set_prediction(self, symbol: str, model_name: str, timestamp: str, 
                      prediction: dict, expire: int = 300):
        """
        设置预测结果
        
        Args:
            expire: 预测结果缓存5分钟（股价变化快）
        """
        key = self._prediction_key(symbol, model_name, timestamp)
        self.cache.set(key, prediction, expire=expire)
    
    def get_latest_predictions(self, symbol: str, model_names: list, 
                               last_n: int = 10) -> dict:
        """获取最近N次预测结果"""
        # 这里简化实现，实际应该使用Redis列表或有序集合
        pass


# 全局缓存实例
cache_instance = None

def get_cache() -> RedisCache:
    """获取全局缓存实例"""
    global cache_instance
    if cache_instance is None:
        cache_instance = RedisCache()
    return cache_instance


if __name__ == "__main__":
    # 测试
    cache = RedisCache()
    
    # 测试基本操作
    cache.set("test_key", {"data": [1, 2, 3]}, expire=60)
    value = cache.get("test_key")
    print(f"获取值: {value}")
    
    # 测试特征缓存
    feature_cache = FeatureCache(cache)
    feature_cache.set_feature("1810.HK", "2024-02-24", "ma5", 15.5)
    ma5 = feature_cache.get_feature("1810.HK", "2024-02-24", "ma5")
    print(f"MA5特征: {ma5}")
    
    # 统计
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
