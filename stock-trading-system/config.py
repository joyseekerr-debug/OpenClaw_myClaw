"""
股票交易系统配置
"""

import os
from dotenv import load_dotenv

load_dotenv()

# 系统配置
SYSTEM_CONFIG = {
    'name': '小米集团股票交易预测系统',
    'version': '0.1.0',
    'debug': True,
    'timezone': 'Asia/Shanghai'
}

# 数据源配置
DATA_SOURCES = {
    'itick': {
        'enabled': True,
        'api_key': os.getenv('ITICK_API_KEY', ''),
        'base_url': 'https://api.itick.com',
        'rate_limit': 1000,  # 每分钟请求数
        'priority': 1  # 优先级
    },
    'yahoo': {
        'enabled': True,
        'priority': 2
    },
    'akshare': {
        'enabled': True,
        'priority': 3
    },
    'alpha_vantage': {
        'enabled': False,  # 需要API key
        'api_key': os.getenv('ALPHA_VANTAGE_KEY', ''),
        'priority': 4
    }
}

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None)
}

# 目标股票配置
TARGET_STOCK = {
    'symbol': '1810.HK',  # 小米集团港股
    'name': '小米集团-W',
    'exchange': 'HKEX',
    'currency': 'HKD',
    'sector': '科技/消费电子',
    'industry': '智能手机/IoT/互联网服务/电动汽车'
}

# 监控配置
MONITORING_CONFIG = {
    'realtime_interval': 1,  # 秒级监控
    'price_change_threshold': 0.02,  # 2%价格变动预警
    'volume_spike_threshold': 3.0,  # 成交量突增3倍预警
    'market_hours': {
        'hk': {
            'open': '09:30',
            'close': '16:00',
            'lunch_start': '12:00',
            'lunch_end': '13:00'
        }
    }
}

# 飞书通知配置
FEISHU_CONFIG = {
    'enabled': True,
    'webhook_url': os.getenv('FEISHU_WEBHOOK_URL', ''),
    'app_id': os.getenv('FEISHU_APP_ID', ''),
    'app_secret': os.getenv('FEISHU_APP_SECRET', ''),
    'default_chat_id': os.getenv('FEISHU_CHAT_ID', '')
}

# 模型配置
MODEL_CONFIG = {
    'prediction_horizons': {
        'intraday': ['1min', '5min', '15min'],  # 日内
        'swing': ['1h', '4h'],  # 短线
        'longterm': ['1d', '1w']  # 长线
    },
    'features': {
        'technical_indicators': [
            'sma', 'ema', 'macd', 'rsi', 'kdj', 'bollinger',
            'atr', 'obv', 'cci', 'williams_r'
        ],
        'price_features': [
            'returns', 'log_returns', 'volatility',
            'price_momentum', 'price_acceleration'
        ],
        'volume_features': [
            'volume_ma', 'volume_ratio', 'money_flow',
            'volume_price_trend'
        ]
    },
    'models': {
        'lstm': {
            'enabled': True,
            'sequence_length': 60,
            'hidden_units': 128,
            'dropout': 0.2
        },
        'xgboost': {
            'enabled': True,
            'n_estimators': 1000,
            'max_depth': 8,
            'learning_rate': 0.01
        },
        'transformer': {
            'enabled': True,
            'd_model': 64,
            'nhead': 4,
            'num_layers': 3
        }
    }
}

# 风控配置
RISK_CONFIG = {
    'max_position_size': 0.2,  # 最大仓位20%
    'stop_loss': 0.05,  # 止损5%
    'take_profit': 0.10,  # 止盈10%
    'max_daily_loss': 0.03,  # 单日最大亏损3%
    'volatility_filter': 0.25  # 波动率过滤阈值
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}',
    'rotation': '1 day',
    'retention': '7 days',
    'path': 'logs/'
}

# 数据存储配置
STORAGE_CONFIG = {
    'raw_data_path': 'data/raw/',
    'processed_data_path': 'data/processed/',
    'features_path': 'data/features/',
    'models_path': 'models/saved/',
    'reports_path': 'reports/'
}
