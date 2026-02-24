"""
飞书通知模块
支持实时推送股价预警、交易信号、系统报告
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, webhook_url: str = None, app_id: str = None, app_secret: str = None):
        """
        初始化飞书通知器
        
        Args:
            webhook_url: 飞书Webhook URL
            app_id: 飞书App ID（可选，用于API方式）
            app_secret: 飞书App Secret（可选）
        """
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        
        # 测试连接
        if self.webhook_url:
            logger.info("✅ 飞书通知器初始化完成")
        else:
            logger.warning("⚠️ 未配置飞书Webhook URL")
    
    def send_text(self, message: str, at_users: List[str] = None) -> bool:
        """
        发送纯文本消息
        
        Args:
            message: 消息内容
            at_users: @的用户ID列表
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            logger.error("❌ 飞书Webhook URL未配置")
            return False
        
        # 构建@信息
        at_text = ""
        if at_users:
            for user in at_users:
                at_text += f"<at id=\"{user}\"></at>"
        
        payload = {
            "msg_type": "text",
            "content": {
                "text": message + at_text
            }
        }
        
        return self._send_request(payload)
    
    def send_markdown(self, title: str, content: str) -> bool:
        """
        发送Markdown格式消息
        
        Args:
            title: 标题
            content: Markdown内容
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            logger.error("❌ 飞书Webhook URL未配置")
            return False
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
            }
        }
        
        return self._send_request(payload)
    
    def send_alert_card(self, alert: Dict) -> bool:
        """
        发送预警卡片
        
        Args:
            alert: 预警信息字典
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            return False
        
        # 根据预警级别选择颜色
        level_colors = {
            'high': 'red',
            'medium': 'orange',
            'low': 'yellow'
        }
        template = level_colors.get(alert.get('level', 'medium'), 'orange')
        
        # 根据预警类型选择图标
        type_icons = {
            'price_spike': '📈',
            'volume_spike': '💥',
            'new_high': '🚀',
            'new_low': '⬇️',
            'order_imbalance': '⚖️',
            'signal_buy': '🔥',
            'signal_sell': '❄️'
        }
        icon = type_icons.get(alert.get('type'), '⚠️')
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} 股票预警 - {alert.get('symbol', 'Unknown')}"
                    },
                    "template": template
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{alert.get('message', '')}**"
                        }
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**股票代码**\n{alert.get('symbol', '-')}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**预警级别**\n{alert.get('level', '-').upper()}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**当前价格**\n¥{alert.get('current_price', 0):.2f}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**时间**\n{alert.get('timestamp', datetime.now()).strftime('%H:%M:%S')}\n"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        return self._send_request(card)
    
    def send_price_update(self, symbol: str, price: float, 
                         change_pct: float, volume: int) -> bool:
        """
        发送价格更新
        
        Args:
            symbol: 股票代码
            price: 当前价格
            change_pct: 涨跌幅(%)
            volume: 成交量
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            return False
        
        # 涨跌颜色
        color = 'green' if change_pct >= 0 else 'red'
        arrow = '📈' if change_pct >= 0 else '📉'
        sign = '+' if change_pct >= 0 else ''
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{arrow} {symbol} 价格更新"
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**当前价格**\n¥{price:.2f}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**涨跌幅**\n{sign}{change_pct:.2f}%\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**成交量**\n{volume:,}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**更新时间**\n{datetime.now().strftime('%H:%M:%S')}\n"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        return self._send_request(card)
    
    def send_prediction_signal(self, symbol: str, prediction: Dict) -> bool:
        """
        发送预测信号
        
        Args:
            symbol: 股票代码
            prediction: 预测结果字典
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            return False
        
        signal = prediction.get('signal', 'hold')
        confidence = prediction.get('confidence', 0)
        
        # 信号颜色
        signal_colors = {
            'buy': 'green',
            'sell': 'red',
            'hold': 'grey'
        }
        template = signal_colors.get(signal, 'grey')
        
        # 信号图标
        signal_icons = {
            'buy': '🟢 买入信号',
            'sell': '🔴 卖出信号',
            'hold': '⚪ 持有观望'
        }
        
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{signal_icons.get(signal, 'Unknown')} - {symbol}"
                    },
                    "template": template
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**预测信号**\n{signal.upper()}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**置信度**\n{confidence*100:.1f}%\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**预测价格**\n¥{prediction.get('predicted_price', 0):.2f}\n"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**预期收益**\n{prediction.get('expected_return', 0)*100:.2f}%\n"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        return self._send_request(card)
    
    def send_daily_report(self, report_data: Dict) -> bool:
        """
        发送每日报告
        
        Args:
            report_data: 报告数据字典
        
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            return False
        
        # 构建报告内容
        content = f"""## 📊 股票交易日报 - {report_data.get('date', datetime.now().strftime('%Y-%m-%d'))}

### 今日概况
- **总资产**: ¥{report_data.get('total_assets', 0):,.2f}
- **今日盈亏**: {report_data.get('pnl_pct', 0):+.2f}%
- **夏普比率**: {report_data.get('sharpe_ratio', 0):.4f}
- **最大回撤**: {report_data.get('max_drawdown', 0)*100:.2f}%

### 持仓情况
"""
        
        # 添加持仓
        positions = report_data.get('positions', [])
        for pos in positions[:5]:  # 最多显示5个
            content += f"- **{pos.get('symbol')}**: {pos.get('quantity')}股 @ ¥{pos.get('avg_price'):.2f} (盈亏: {pos.get('pnl_pct', 0):+.2f}%)\n"
        
        # 添加交易记录
        content += "\n### 今日交易\n"
        trades = report_data.get('trades', [])
        for trade in trades[:5]:
            content += f"- {trade.get('time')} | {trade.get('action')} {trade.get('symbol')} @ ¥{trade.get('price'):.2f}\n"
        
        content += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return self.send_markdown("📊 每日交易报告", content)
    
    def _send_request(self, payload: Dict) -> bool:
        """
        发送HTTP请求
        
        Args:
            payload: 请求体
        
        Returns:
            发送是否成功
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info("✅ 飞书消息发送成功")
                    return True
                else:
                    logger.error(f"❌ 飞书API错误: {result.get('msg')}")
                    return False
            else:
                logger.error(f"❌ HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送请求失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试飞书连接"""
        if not self.webhook_url:
            logger.error("❌ Webhook URL未配置")
            return False
        
        return self.send_text("🔔 飞书通知测试消息\n如果您看到这条消息，说明通知系统配置成功！")


class NotificationManager:
    """通知管理器 - 整合多种通知渠道"""
    
    def __init__(self):
        self.notifiers = {}
        self.alert_rules = []
    
    def add_feishu(self, name: str, webhook_url: str, **kwargs):
        """添加飞书通知器"""
        self.notifiers[name] = FeishuNotifier(webhook_url, **kwargs)
        logger.info(f"✅ 添加通知渠道: {name} (Feishu)")
    
    def send_to_all(self, message: str, msg_type: str = 'text'):
        """
        发送到所有通知渠道
        
        Args:
            message: 消息内容
            msg_type: 消息类型
        """
        for name, notifier in self.notifiers.items():
            try:
                if msg_type == 'text':
                    notifier.send_text(message)
                elif msg_type == 'markdown':
                    notifier.send_markdown("通知", message)
                logger.info(f"✅ 已发送到 {name}")
            except Exception as e:
                logger.error(f"❌ 发送到 {name} 失败: {e}")
    
    def send_alert(self, alert: Dict):
        """
        发送预警到所有渠道
        
        Args:
            alert: 预警信息
        """
        for name, notifier in self.notifiers.items():
            try:
                if isinstance(notifier, FeishuNotifier):
                    notifier.send_alert_card(alert)
                logger.info(f"✅ 预警已发送到 {name}")
            except Exception as e:
                logger.error(f"❌ 预警发送到 {name} 失败: {e}")


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("飞书通知模块")
    print("="*70)
    
    # 创建通知器
    notifier = FeishuNotifier()
    
    print("\n✅ 飞书通知模块就绪")
    print("   • 支持文本/Markdown/卡片消息")
    print("   • 支持价格更新、预测信号、每日报告")
    print("   • 支持多通知渠道管理")
    
    # 示例预警
    sample_alert = {
        'type': 'price_spike',
        'symbol': '1810.HK',
        'message': '价格上涨 5.2%，突破20日均线',
        'current_price': 15.8,
        'previous_price': 15.0,
        'timestamp': datetime.now(),
        'level': 'high'
    }
    
    print("\n📋 示例预警:")
    print(f"   类型: {sample_alert['type']}")
    print(f"   股票: {sample_alert['symbol']}")
    print(f"   消息: {sample_alert['message']}")
    
    print("\n⚠️ 注意: 需要配置飞书Webhook URL才能实际发送消息")
    print("="*70)
