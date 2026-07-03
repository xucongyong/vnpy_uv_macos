
import akshare as ak
import traceback
import sys
import platform

def troubleshoot():
    print("="*50)
    print("🔍 AkShare 环境诊断报告")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    print(f"AkShare 版本: {ak.__version__}")
    print("="*50)

    tests = [
        {
            "name": "A股列表 (stock_zh_a_spot_em)",
            "source": "东方财富 (EastMoney)",
            "func": lambda: ak.stock_zh_a_spot_em()
        },
        {
            "name": "A股历史数据 (stock_zh_a_hist)",
            "source": "东方财富 (EastMoney)",
            "func": lambda: ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", adjust="qfq")
        },
        {
            "name": "港股列表 (stock_hk_spot_em)",
            "source": "东方财富 (EastMoney)",
            "func": lambda: ak.stock_hk_spot_em()
        },
        {
            "name": "美股列表 (stock_us_spot_em)",
            "source": "东方财富 (EastMoney)",
            "func": lambda: ak.stock_us_spot_em()
        },
        {
            "name": "备选A股接口 (stock_zh_a_daily)",
            "source": "新浪财经 (Sina)",
            "func": lambda: ak.stock_zh_a_daily(symbol="sz000001", start_date="20240101")
        }
    ]

    for test in tests:
        print(f"\n▶️ 正在测试: {test['name']}")
        print(f"   数据源: {test['source']}")
        try:
            df = test['func']()
            if df is not None and not df.empty:
                print(f"   ✅ 成功! 获取到 {len(df)} 行数据。")
            else:
                print("   ⚠️ 接口返回为空。")
        except Exception:
            print(f"   ❌ 失败!")
            print("-" * 30)
            traceback.print_exc()
            print("-" * 30)

    print("\n" + "="*50)
    print("💡 诊断结束。请将上述 [❌ 失败!] 部分的错误栈（Traceback）发给技术群或开发者。")
    print("="*50)

if __name__ == "__main__":
    troubleshoot()
