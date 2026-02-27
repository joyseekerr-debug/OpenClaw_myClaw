#!/usr/bin/env python3
"""
股价预测系统 - 主入口
专业股价预测系统 v1.0.0

功能:
- 多时间框架预测 (1m-1w)
- 多模型集成 (LSTM/XGBoost/Transformer/PriceAction)
- 概率输出与校准
- 历史回测验证
"""

import sys
import os
import argparse
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     股价预测系统 v1.0.0 - Stock Price Prediction System   ║
║                                                           ║
║     多时间框架 | 多模型集成 | 概率输出 | 回测验证        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def predict_command(args):
    """预测命令"""
    print(f"\n📊 预测 {args.symbol} ({args.timeframe})")
    
    try:
        from deployment.prediction_service import PredictionService
        
        service = PredictionService()
        result = service.predict(args.symbol, args.timeframe)
        
        if 'error' in result:
            print(f"❌ 错误: {result['error']}")
            return
        
        print(f"\n✅ 预测结果:")
        print(f"  股票代码: {result['symbol']}")
        print(f"  当前价格: {result['current_price']}")
        print(f"  预测方向: {result['prediction']['direction'].upper()}")
        print(f"  上涨概率: {result['prediction']['up_probability']:.2%}")
        print(f"  下跌概率: {result['prediction']['down_probability']:.2%}")
        print(f"  置信度: {result['prediction']['confidence']:.2%}")
        print(f"  置信区间: [{result['prediction']['confidence_interval'][0]:.2%}, {result['prediction']['confidence_interval'][1]:.2%}]")
        print(f"  建议: {result['recommendation']}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 结果已保存到: {args.output}")
        
    except Exception as e:
        print(f"❌ 预测失败: {e}")


def backtest_command(args):
    """回测命令"""
    print(f"\n📈 回测 {args.symbol}")
    print("注意: 回测功能需要完整的数据和模型，当前为演示模式")
    
    # 模拟回测结果
    mock_result = {
        'total_trades': 50,
        'win_rate': 0.52,
        'profit_factor': 1.3,
        'sharpe_ratio': 1.1,
        'max_drawdown': -0.15,
        'total_return': 0.25
    }
    
    print(f"\n📊 回测结果 (模拟数据):")
    print(f"  总交易次数: {mock_result['total_trades']}")
    print(f"  胜率: {mock_result['win_rate']:.2%}")
    print(f"  盈亏比: {mock_result['profit_factor']:.2f}")
    print(f"  夏普比率: {mock_result['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {mock_result['max_drawdown']:.2%}")
    print(f"  总收益率: {mock_result['total_return']:.2%}")


def train_command(args):
    """训练命令"""
    print(f"\n🎯 训练模型")
    print(f"  模型类型: {args.model}")
    print(f"  股票: {args.symbol}")
    
    print("\n⚠️ 注意: 模型训练需要大量数据和计算资源")
    print("  请确保已配置正确的数据源和计算环境")
    
    if args.model == 'all':
        models = ['LSTM', 'XGBoost', 'Transformer', 'PriceAction']
    else:
        models = [args.model]
    
    print(f"\n📝 计划训练模型: {', '.join(models)}")
    print("使用 --dry-run 查看详细配置")


def optimize_command(args):
    """优化命令"""
    print(f"\n🔧 参数优化")
    print(f"  模型: {args.model}")
    print(f"  方法: {args.method}")
    
    print("\n⚠️ 参数优化可能需要较长时间")
    print("  建议使用较小的数据集进行快速验证")


def status_command(args):
    """状态命令"""
    print("\n📋 系统状态")
    
    try:
        from deployment.prediction_service import PredictionService
        
        service = PredictionService()
        health = service.health_check()
        
        print(f"\n✅ 服务状态: {health['status']}")
        print(f"  已初始化: {health['initialized']}")
        print(f"  检查时间: {health['timestamp']}")
        
        if 'dependencies' in health:
            print("\n📦 依赖状态:")
            for dep, status in health['dependencies'].items():
                symbol = "✅" if status else "❌"
                print(f"  {symbol} {dep}")
        
    except Exception as e:
        print(f"⚠️ 无法获取状态: {e}")


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description='股价预测系统 - 专业股价预测工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预测小米集团股价
  python main.py predict 1810.HK
  
  # 回测
  python main.py backtest 1810.HK --days 365
  
  # 训练模型
  python main.py train --model xgboost --symbol 1810.HK
  
  # 参数优化
  python main.py optimize --model xgboost --method random
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # predict 命令
    predict_parser = subparsers.add_parser('predict', help='预测股价')
    predict_parser.add_argument('symbol', help='股票代码 (如 1810.HK)')
    predict_parser.add_argument('--timeframe', '-t', default='1d',
                               choices=['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
                               help='时间框架 (默认: 1d)')
    predict_parser.add_argument('--output', '-o', help='输出文件路径')
    predict_parser.set_defaults(func=predict_command)
    
    # backtest 命令
    backtest_parser = subparsers.add_parser('backtest', help='历史回测')
    backtest_parser.add_argument('symbol', help='股票代码')
    backtest_parser.add_argument('--days', '-d', type=int, default=365,
                                help='回测天数 (默认: 365)')
    backtest_parser.add_argument('--initial-capital', type=float, default=100000,
                                help='初始资金 (默认: 100000)')
    backtest_parser.set_defaults(func=backtest_command)
    
    # train 命令
    train_parser = subparsers.add_parser('train', help='训练模型')
    train_parser.add_argument('--model', '-m', default='all',
                             choices=['all', 'lstm', 'xgboost', 'transformer', 'price_action'],
                             help='模型类型 (默认: all)')
    train_parser.add_argument('--symbol', '-s', default='1810.HK',
                             help='股票代码 (默认: 1810.HK)')
    train_parser.add_argument('--epochs', '-e', type=int, default=100,
                             help='训练轮数 (默认: 100)')
    train_parser.set_defaults(func=train_command)
    
    # optimize 命令
    optimize_parser = subparsers.add_parser('optimize', help='参数优化')
    optimize_parser.add_argument('--model', '-m', default='xgboost',
                                choices=['lstm', 'xgboost', 'transformer'],
                                help='模型类型 (默认: xgboost)')
    optimize_parser.add_argument('--method', default='random',
                                choices=['grid', 'random', 'bayesian'],
                                help='优化方法 (默认: random)')
    optimize_parser.set_defaults(func=optimize_command)
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='系统状态')
    status_parser.set_defaults(func=status_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    args.func(args)
    
    print("\n✨ 完成")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
