"""
股票价格获取模块 - 多方案实现
方案1: 网络API (需要代理配置)
方案2: 本地模拟 (当前使用)
方案3: 文件/数据库读取
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import os


class StockPriceProvider:
    """股票价格提供者"""
    
    def __init__(self, symbol: str = '1810.HK'):
        self.symbol = symbol
        self.base_price = 15.0
        self.current_price = self.base_price
        self.price_history = []
        
        # 加载历史数据（如果有）
        self._load_history()
    
    def _load_history(self):
        """加载历史价格数据"""
        history_file = f'data/{self.symbol.replace(".", "_")}_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                self.price_history = json.load(f)
                if self.price_history:
                    self.current_price = self.price_history[-1]['price']
    
    def _save_history(self):
        """保存价格历史"""
        os.makedirs('data', exist_ok=True)
        history_file = f'data/{self.symbol.replace(".", "_")}_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.price_history[-1000:], f)  # 只保留最近1000条
    
    def get_real_time_price_network(self) -> Optional[Dict]:
        """
        从网络获取实时股价
        注: 需要配置代理或网络环境
        """
        # 方案1: AKShare
        try:
            import akshare as ak
            hk_df = ak.stock_hk_spot_em()
            xiaomi = hk_df[hk_df['代码'] == '01810']
            if not xiaomi.empty:
                row = xiaomi.iloc[0]
                return {
                    'source': 'akshare',
                    'symbol': self.symbol,
                    'price': float(row.get('最新价', 0)),
                    'open': float(row.get('开盘价', 0)),
                    'high': float(row.get('最高价', 0)),
                    'low': float(row.get('最低价', 0)),
                    'prev_close': float(row.get('昨收', 0)),
                    'volume': str(row.get('成交量', 'N/A')),
                    'change_pct': float(row.get('涨跌幅', 0)),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"AKShare获取失败: {e}")
        
        # 方案2: Yahoo Finance
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                latest = hist.iloc[-1]
                info = ticker.info
                prev_close = info.get('previousClose', latest['Close'])
                change_pct = (latest['Close'] - prev_close) / prev_close * 100
                
                return {
                    'source': 'yahoo',
                    'symbol': self.symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'prev_close': float(prev_close),
                    'volume': int(latest['Volume']),
                    'change_pct': change_pct,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Yahoo获取失败: {e}")
        
        return None
    
    def get_simulated_price(self) -> Dict:
        """
        获取模拟股价（用于测试和网络不可用时）
        """
        # 模拟价格变动
        change = random.gauss(0, 0.005)  # 正态分布，标准差0.5%
        self.current_price *= (1 + change)
        
        # 计算今日数据
        open_price = self.current_price * (1 + random.gauss(0, 0.002))
        high_price = max(self.current_price, open_price) * (1 + abs(random.gauss(0, 0.01)))
        low_price = min(self.current_price, open_price) * (1 - abs(random.gauss(0, 0.01)))
        
        # 计算涨跌幅
        prev_close = self.base_price
        change_pct = (self.current_price - prev_close) / prev_close * 100
        
        data = {
            'source': 'simulated',
            'symbol': self.symbol,
            'price': round(self.current_price, 3),
            'open': round(open_price, 3),
            'high': round(high_price, 3),
            'low': round(low_price, 3),
            'prev_close': round(prev_close, 3),
            'volume': random.randint(1000000, 10000000),
            'change_pct': round(change_pct, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存历史
        self.price_history.append(data)
        if len(self.price_history) % 10 == 0:  # 每10条保存一次
            self._save_history()
        
        return data
    
    def get_price(self, use_network: bool = True) -> Dict:
        """
        获取股价（自动选择方案）
        
        Args:
            use_network: 是否尝试网络获取
        
        Returns:
            股价数据字典
        """
        if use_network:
            # 先尝试网络获取
            network_data = self.get_real_time_price_network()
            if network_data:
                return network_data
            print("⚠️ 网络获取失败，使用模拟数据")
        
        # 使用模拟数据
        return self.get_simulated_price()
    
    def start_realtime_feed(self, callback=None, interval: int = 5):
        """
        启动实时价格推送
        
        Args:
            callback: 价格更新回调函数
            interval: 更新间隔（秒）
        """
        print(f"🚀 启动实时价格推送: {self.symbol}")
        print(f"   更新间隔: {interval}秒")
        print(f"   按 Ctrl+C 停止\n")
        
        try:
            while True:
                price_data = self.get_price(use_network=False)
                
                if callback:
                    callback(price_data)
                else:
                    self._print_price(price_data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ 实时推送已停止")
            self._save_history()
    
    def _print_price(self, data: Dict):
        """打印价格信息"""
        timestamp = datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S')
        symbol = data['symbol']
        price = data['price']
        change_pct = data['change_pct']
        
        arrow = "📈" if change_pct >= 0 else "📉"
        sign = "+" if change_pct >= 0 else ""
        
        print(f"[{timestamp}] {arrow} {symbol}: ¥{price:.3f} ({sign}{change_pct:.2f}%)")


# 全局实例
_price_provider = None

def get_price_provider(symbol: str = '1810.HK') -> StockPriceProvider:
    """获取价格提供者实例"""
    global _price_provider
    if _price_provider is None or _price_provider.symbol != symbol:
        _price_provider = StockPriceProvider(symbol)
    return _price_provider


# 使用示例
if __name__ == "__main__":
    print("="*60)
    print("股票价格获取模块")
    print("="*60)
    print()
    
    # 创建价格提供者
    provider = StockPriceProvider('1810.HK')
    
    # 获取单次价格
    print("[单次获取]")
    price_data = provider.get_price(use_network=False)
    
    print(f"\n股票: {price_data['symbol']}")
    print(f"来源: {price_data['source']}")
    print(f"最新价: ¥{price_data['price']:.3f} 港元")
    print(f"涨跌幅: {price_data['change_pct']:+.2f}%")
    print(f"今日最高: ¥{price_data['high']:.3f} 港元")
    print(f"今日最低: ¥{price_data['low']:.3f} 港元")
    print(f"成交量: {price_data['volume']:,} 股")
    print()
    
    # 启动实时推送（可选）
    choice = input("是否启动实时价格推送? (y/n): ").lower()
    if choice == 'y':
        print()
        provider.start_realtime_feed(interval=2)
    else:
        print("\n👋 退出")
