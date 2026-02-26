"""
股票交易系统主入口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from config import SYSTEM_CONFIG, LOG_CONFIG, TARGET_STOCK
from price_provider import get_price_provider

# 配置日志
logger.add(
    LOG_CONFIG['path'] + "trading_system.log",
    rotation=LOG_CONFIG['rotation'],
    retention=LOG_CONFIG['retention'],
    level=LOG_CONFIG['level'],
    format=LOG_CONFIG['format']
)


class StockTradingSystem:
    """股票交易系统主类"""
    
    def __init__(self):
        self.name = SYSTEM_CONFIG['name']
        self.version = SYSTEM_CONFIG['version']
        self.data_manager = None
        self.feature_engine = None
        self.model_manager = None
        self.monitor = None
        self.notifier = None
        
        logger.info(f"🚀 启动 {self.name} v{self.version}")
    
    def initialize(self):
        """初始化系统组件"""
        logger.info("🔧 正在初始化系统组件...")
        
        # 1. 初始化数据源
        from data.data_source import DataSourceManager
        from config import DATA_SOURCES
        
        self.data_manager = DataSourceManager(DATA_SOURCES)
        logger.info("✅ 数据源管理器初始化完成")
        
        # 2. 初始化缓存
        from utils.cache import RedisCache
        from config import REDIS_CONFIG
        
        self.cache = RedisCache(**REDIS_CONFIG)
        logger.info("✅ 缓存系统初始化完成")
        
        # 3. 初始化通知系统
        # from monitoring.notifier import FeishuNotifier
        # self.notifier = FeishuNotifier()
        # logger.info("✅ 通知系统初始化完成")
        
        logger.info("🎉 系统初始化完成！")
    
    def test_data_pipeline(self):
        """测试数据管道"""
        logger.info("🧪 测试数据管道...")
        
        symbol = TARGET_STOCK['symbol']
        
        # 测试历史数据获取
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = self.data_manager.get_data(
            symbol=symbol,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if not data.empty:
            logger.info(f"✅ 数据获取成功: {len(data)} 条记录")
            logger.info(f"📊 数据样例:\n{data.head()}")
            return True
        else:
            logger.error("❌ 数据获取失败")
            return False
    
    def run(self):
        """运行系统"""
        try:
            self.initialize()
            
            # 测试数据管道
            if self.test_data_pipeline():
                logger.info("✅ 系统测试通过，准备就绪！")
            else:
                logger.warning("⚠️ 数据管道测试未通过")
            
            # 测试实时价格获取
            self.test_realtime_price()
            
            # 这里可以启动实时监控等
            logger.info("📈 系统运行中...")
            
        except Exception as e:
            logger.error(f"❌ 系统运行失败: {e}")
            raise
    
    def test_realtime_price(self):
        """测试实时价格获取 - 使用真实数据源"""
        logger.info("Testing realtime price fetch with REAL data sources...")
        
        try:
            provider = get_price_provider(TARGET_STOCK['symbol'])
            # 强制使用真实网络数据，禁止模拟数据
            price_data = provider.get_price(use_network=True, allow_simulated=False)
            
            logger.info(f"SUCCESS: Price fetched from {price_data['source']}")
            logger.info(f"   Symbol: {price_data['symbol']}")
            logger.info(f"   Price: HK$ {price_data['price']:.3f}")
            logger.info(f"   Change: {price_data['change_pct']:+.2f}%")
            
            # 验证数据来源
            if price_data.get('source') == 'simulated':
                logger.error("CRITICAL: Got simulated data when real data was required!")
                raise Exception("Simulated data is not allowed for production use")
            
        except Exception as e:
            logger.error(f"Price fetch failed: {e}")
            logger.error("Real-time price is unavailable. Check data sources and network.")
    
    def shutdown(self):
        """关闭系统"""
        logger.info("🛑 正在关闭系统...")
        # 清理资源
        logger.info("👋 系统已关闭")


def main():
    """主函数"""
    print("═══════════════════════════════════════════════════════════")
    print(f"     {SYSTEM_CONFIG['name']}")
    print(f"     版本: {SYSTEM_CONFIG['version']}")
    print("═══════════════════════════════════════════════════════════\n")
    
    system = StockTradingSystem()
    
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n⛔ 用户中断")
    finally:
        system.shutdown()


if __name__ == "__main__":
    main()
