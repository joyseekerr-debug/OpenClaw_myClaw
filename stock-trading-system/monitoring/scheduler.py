"""
监控调度器
整合实时监控、预警系统和飞书通知
"""

import asyncio
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from monitoring.realtime import RealtimeMonitor, MultiSymbolMonitor
from monitoring.notifier import FeishuNotifier, NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """监控调度器"""
    
    def __init__(self, config: dict = None):
        """
        初始化监控调度器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 监控组件
        self.multi_monitor = MultiSymbolMonitor()
        self.notification_manager = NotificationManager()
        
        # 飞书通知器
        self.feishu = None
        if self.config.get('feishu_webhook_url'):
            self.feishu = FeishuNotifier(
                webhook_url=self.config.get('feishu_webhook_url'),
                app_id=self.config.get('feishu_app_id'),
                app_secret=self.config.get('feishu_app_secret')
            )
            self.notification_manager.add_feishu('feishu_main', self.config.get('feishu_webhook_url'))
        
        # 状态
        self.is_running = False
        self.tasks = []
        
        logger.info("✅ 监控调度器初始化完成")
    
    def setup_monitoring(self, symbols: List[str], monitor_config: dict = None):
        """
        设置监控
        
        Args:
            symbols: 监控的股票代码列表
            monitor_config: 监控配置
        """
        monitor_config = monitor_config or {}
        
        for symbol in symbols:
            # 创建监控
            self.multi_monitor.add_symbol(symbol, monitor_config)
            
            # 获取监控实例
            monitor = self.multi_monitor.monitors[symbol]
            
            # 添加数据更新回调
            monitor.add_data_callback(
                lambda data, sym=symbol: self._on_data_update(sym, data)
            )
            
            # 添加预警回调
            monitor.add_alert_callback(
                lambda alert, sym=symbol: self._on_alert(sym, alert)
            )
            
            logger.info(f"✅ 已设置监控: {symbol}")
    
    def _on_data_update(self, symbol: str, data: dict):
        """数据更新回调"""
        # 可以在这里进行数据存储、日志记录等
        logger.debug(f"[{symbol}] 价格更新: ¥{data.get('price', 0):.2f}")
    
    def _on_alert(self, symbol: str, alert: dict):
        """预警回调"""
        logger.warning(f"🚨 [{symbol}] 预警: {alert.get('message', '')}")
        
        # 发送飞书通知
        if self.feishu:
            self.feishu.send_alert_card(alert)
    
    async def start_monitoring(self):
        """启动监控"""
        logger.info("🚀 启动监控系统...")
        self.is_running = True
        
        # 启动所有监控
        self.multi_monitor.start_all()
        
        # 发送启动通知
        if self.feishu:
            self.feishu.send_text(
                f"🔔 股票监控系统已启动\n"
                f"监控股票: {list(self.multi_monitor.monitors.keys())}\n"
                f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # 保持运行
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("⏹️ 监控任务被取消")
        
        logger.info("⏹️ 监控系统已停止")
    
    def stop_monitoring(self):
        """停止监控"""
        logger.info("⏹️ 正在停止监控系统...")
        self.is_running = False
        self.multi_monitor.stop_all()
        
        # 发送停止通知
        if self.feishu:
            self.feishu.send_text(
                f"⏹️ 股票监控系统已停止\n"
                f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
    
    def get_status(self) -> dict:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'monitored_symbols': list(self.multi_monitor.monitors.keys()),
            'stats': self.multi_monitor.get_all_stats()
        }
    
    def run(self):
        """运行监控调度器"""
        try:
            # 设置信号处理
            loop = asyncio.get_event_loop()
            
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self.stop_monitoring)
            
            # 启动监控
            loop.run_until_complete(self.start_monitoring())
            
        except KeyboardInterrupt:
            logger.info("⛔ 用户中断")
            self.stop_monitoring()
        except Exception as e:
            logger.error(f"❌ 监控异常: {e}")
            self.stop_monitoring()
            raise


# 主程序入口
def main():
    """主程序"""
    print("="*70)
    print("小米集团股票监控系统 v0.1.0")
    print("="*70)
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # 配置
    config = {
        'feishu_webhook_url': os.getenv('FEISHU_WEBHOOK_URL'),
        'feishu_app_id': os.getenv('FEISHU_APP_ID'),
        'feishu_app_secret': os.getenv('FEISHU_APP_SECRET')
    }
    
    # 创建调度器
    scheduler = MonitoringScheduler(config)
    
    # 设置监控（小米集团）
    monitor_config = {
        'price_change_threshold': 0.02,  # 2%价格变动预警
        'volume_spike_threshold': 3.0,   # 3倍成交量预警
        'update_interval': 5              # 5秒更新
    }
    
    scheduler.setup_monitoring(['1810.HK'], monitor_config)
    
    # 测试飞书连接
    if scheduler.feishu:
        scheduler.feishu.test_connection()
    
    print("\n🚀 系统配置完成，准备启动...")
    print("="*70)
    
    # 运行
    scheduler.run()


if __name__ == "__main__":
    main()
