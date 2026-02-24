"""
实时监控模块
秒级股价监控和信息预警系统
"""

import asyncio
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """实时监控系统"""
    
    def __init__(self, symbol: str, config: dict = None):
        """
        初始化实时监控
        
        Args:
            symbol: 监控的股票代码 (如 '1810.HK')
            config: 监控配置
        """
        self.symbol = symbol
        self.config = config or {}
        
        # 监控配置
        self.price_change_threshold = self.config.get('price_change_threshold', 0.02)  # 2%
        self.volume_spike_threshold = self.config.get('volume_spike_threshold', 3.0)  # 3倍
        self.update_interval = self.config.get('update_interval', 1)  # 1秒
        
        # 状态
        self.is_running = False
        self.latest_data = {}
        self.price_history = []
        self.volume_history = []
        self.alert_history = []
        
        # 回调函数
        self.data_callbacks = []
        self.alert_callbacks = []
        
        logger.info(f"✅ 实时监控初始化: {symbol}")
    
    def add_data_callback(self, callback: Callable):
        """添加数据更新回调"""
        self.data_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """添加预警回调"""
        self.alert_callbacks.append(callback)
    
    async def fetch_itick_data(self) -> Optional[Dict]:
        """从iTick获取实时数据"""
        try:
            # iTick WebSocket或HTTP接口
            # 这里使用HTTP轮询作为示例
            import os
            api_key = os.getenv('ITICK_API_KEY')
            
            url = f"https://api.itick.com/quote/realtime"
            params = {
                'symbol': self.symbol,
                'region': 'HK'
            }
            headers = {'Authorization': f'Bearer {api_key}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_itick_data(data)
                    else:
                        logger.warning(f"iTick API返回错误: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"获取iTick数据失败: {e}")
            return None
    
    def _parse_itick_data(self, data: Dict) -> Dict:
        """解析iTick数据"""
        return {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'price': data.get('price', 0),
            'open': data.get('open', 0),
            'high': data.get('high', 0),
            'low': data.get('low', 0),
            'volume': data.get('volume', 0),
            'bid': data.get('bid', 0),
            'ask': data.get('ask', 0),
            'bid_volume': data.get('bid_volume', 0),
            'ask_volume': data.get('ask_volume', 0)
        }
    
    async def fetch_yahoo_data(self) -> Optional[Dict]:
        """从Yahoo Finance获取数据（备用）"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'timestamp': datetime.now(),
                    'symbol': self.symbol,
                    'price': latest['Close'],
                    'open': latest['Open'],
                    'high': latest['High'],
                    'low': latest['Low'],
                    'volume': latest['Volume']
                }
            return None
            
        except Exception as e:
            logger.error(f"获取Yahoo数据失败: {e}")
            return None
    
    async def fetch_data(self) -> Optional[Dict]:
        """获取实时数据（自动切换数据源）"""
        # 优先iTick
        data = await self.fetch_itick_data()
        
        # iTick失败，使用Yahoo
        if data is None:
            logger.warning("iTick数据获取失败，切换到Yahoo")
            data = await self.fetch_yahoo_data()
        
        return data
    
    def check_alerts(self, current_data: Dict) -> List[Dict]:
        """
        检查预警条件
        
        Returns:
            预警列表
        """
        alerts = []
        
        if not self.latest_data:
            return alerts
        
        current_price = current_data['price']
        previous_price = self.latest_data.get('price', current_price)
        current_volume = current_data.get('volume', 0)
        
        # 1. 价格变动预警
        price_change_pct = (current_price - previous_price) / previous_price
        
        if abs(price_change_pct) >= self.price_change_threshold:
            alert = {
                'type': 'price_spike',
                'timestamp': datetime.now(),
                'symbol': self.symbol,
                'message': f"价格{'上涨' if price_change_pct > 0 else '下跌'} {abs(price_change_pct)*100:.2f}%",
                'current_price': current_price,
                'previous_price': previous_price,
                'change_pct': price_change_pct * 100,
                'level': 'high' if abs(price_change_pct) > 0.05 else 'medium'
            }
            alerts.append(alert)
        
        # 2. 成交量突增预警
        if len(self.volume_history) >= 20:
            avg_volume = np.mean(self.volume_history[-20:])
            if avg_volume > 0 and current_volume / avg_volume > self.volume_spike_threshold:
                alert = {
                    'type': 'volume_spike',
                    'timestamp': datetime.now(),
                    'symbol': self.symbol,
                    'message': f"成交量突增 {current_volume/avg_volume:.1f} 倍",
                    'current_volume': current_volume,
                    'avg_volume': avg_volume,
                    'ratio': current_volume / avg_volume,
                    'level': 'medium'
                }
                alerts.append(alert)
        
        # 3. 价格突破预警（基于历史）
        if len(self.price_history) >= 20:
            recent_high = max(self.price_history[-20:])
            recent_low = min(self.price_history[-20:])
            
            if current_price > recent_high * 0.995:  # 接近新高
                alert = {
                    'type': 'new_high',
                    'timestamp': datetime.now(),
                    'symbol': self.symbol,
                    'message': f"接近20日新高: {current_price:.2f}",
                    'current_price': current_price,
                    'recent_high': recent_high,
                    'level': 'medium'
                }
                alerts.append(alert)
            
            elif current_price < recent_low * 1.005:  # 接近新低
                alert = {
                    'type': 'new_low',
                    'timestamp': datetime.now(),
                    'symbol': self.symbol,
                    'message': f"接近20日新低: {current_price:.2f}",
                    'current_price': current_price,
                    'recent_low': recent_low,
                    'level': 'high'
                }
                alerts.append(alert)
        
        # 4. 大单交易预警（如果有订单簿数据）
        if 'bid_volume' in current_data and 'ask_volume' in current_data:
            total_volume = current_data['bid_volume'] + current_data['ask_volume']
            if total_volume > 0:
                order_imbalance = abs(current_data['bid_volume'] - current_data['ask_volume']) / total_volume
                if order_imbalance > 0.7:  # 订单严重失衡
                    direction = '买盘' if current_data['bid_volume'] > current_data['ask_volume'] else '卖盘'
                    alert = {
                        'type': 'order_imbalance',
                        'timestamp': datetime.now(),
                        'symbol': self.symbol,
                        'message': f"{direction}力量强 ({order_imbalance*100:.0f}%)",
                        'bid_volume': current_data['bid_volume'],
                        'ask_volume': current_data['ask_volume'],
                        'imbalance': order_imbalance,
                        'level': 'medium'
                    }
                    alerts.append(alert)
        
        return alerts
    
    async def monitor_loop(self):
        """监控主循环"""
        logger.info(f"🚀 启动实时监控: {self.symbol}")
        self.is_running = True
        
        while self.is_running:
            try:
                # 获取数据
                data = await self.fetch_data()
                
                if data:
                    # 更新历史
                    self.latest_data = data
                    self.price_history.append(data['price'])
                    self.volume_history.append(data.get('volume', 0))
                    
                    # 限制历史长度
                    max_history = 1000
                    if len(self.price_history) > max_history:
                        self.price_history = self.price_history[-max_history:]
                    if len(self.volume_history) > max_history:
                        self.volume_history = self.volume_history[-max_history:]
                    
                    # 数据回调
                    for callback in self.data_callbacks:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"数据回调错误: {e}")
                    
                    # 检查预警
                    alerts = self.check_alerts(data)
                    
                    for alert in alerts:
                        self.alert_history.append(alert)
                        
                        # 预警回调
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                logger.error(f"预警回调错误: {e}")
                        
                        logger.warning(f"🚨 预警: {alert['message']}")
                
                # 等待下一次更新
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.update_interval)
        
        logger.info("⏹️ 实时监控已停止")
    
    def start(self):
        """启动监控"""
        if not self.is_running:
            asyncio.create_task(self.monitor_loop())
    
    def stop(self):
        """停止监控"""
        self.is_running = False
    
    def get_monitoring_stats(self) -> Dict:
        """获取监控统计"""
        return {
            'symbol': self.symbol,
            'is_running': self.is_running,
            'data_points': len(self.price_history),
            'alerts_triggered': len(self.alert_history),
            'latest_price': self.latest_data.get('price') if self.latest_data else None,
            'price_change_24h': self._calculate_24h_change(),
            'alert_summary': self._summarize_alerts()
        }
    
    def _calculate_24h_change(self) -> Optional[float]:
        """计算24小时价格变动"""
        if len(self.price_history) < 2:
            return None
        
        # 假设1秒一个数据点，取近似24小时前的数据
        points_24h = min(86400, len(self.price_history))  # 最多取24小时
        if points_24h < 2:
            return 0
        
        price_24h_ago = self.price_history[-points_24h]
        current_price = self.price_history[-1]
        
        return (current_price - price_24h_ago) / price_24h_ago * 100
    
    def _summarize_alerts(self) -> Dict[str, int]:
        """预警摘要"""
        summary = {}
        for alert in self.alert_history:
            alert_type = alert['type']
            summary[alert_type] = summary.get(alert_type, 0) + 1
        return summary


class MultiSymbolMonitor:
    """多股票监控系统"""
    
    def __init__(self):
        self.monitors = {}
        self.global_callbacks = []
    
    def add_symbol(self, symbol: str, config: dict = None):
        """添加监控股票"""
        if symbol not in self.monitors:
            monitor = RealtimeMonitor(symbol, config)
            self.monitors[symbol] = monitor
            logger.info(f"✅ 添加监控: {symbol}")
    
    def remove_symbol(self, symbol: str):
        """移除监控股票"""
        if symbol in self.monitors:
            self.monitors[symbol].stop()
            del self.monitors[symbol]
            logger.info(f"❌ 移除监控: {symbol}")
    
    def start_all(self):
        """启动所有监控"""
        for symbol, monitor in self.monitors.items():
            monitor.start()
            logger.info(f"▶️ 启动监控: {symbol}")
    
    def stop_all(self):
        """停止所有监控"""
        for symbol, monitor in self.monitors.items():
            monitor.stop()
            logger.info(f"⏹️ 停止监控: {symbol}")
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有监控统计"""
        return {symbol: monitor.get_monitoring_stats() 
                for symbol, monitor in self.monitors.items()}


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("实时监控系统")
    print("="*70)
    
    # 创建监控
    monitor = RealtimeMonitor('1810.HK', {
        'price_change_threshold': 0.02,  # 2%
        'volume_spike_threshold': 3.0,   # 3倍
        'update_interval': 5              # 5秒
    })
    
    # 添加数据回调
    def on_data_update(data):
        print(f"[{data['timestamp'].strftime('%H:%M:%S')}] "
              f"{data['symbol']}: ¥{data['price']:.2f} "
              f"Vol: {data.get('volume', 0):,}")
    
    # 添加预警回调
    def on_alert(alert):
        print(f"\n🚨 [{alert['level'].upper()}] {alert['message']}\n")
    
    monitor.add_data_callback(on_data_update)
    monitor.add_alert_callback(on_alert)
    
    print("\n✅ 实时监控系统就绪")
    print("   • 监控股票: 1810.HK (小米集团)")
    print("   • 更新频率: 5秒")
    print("   • 价格预警阈值: 2%")
    print("   • 成交量预警阈值: 3倍")
    print("="*70)
