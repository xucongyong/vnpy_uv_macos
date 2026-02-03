from futu import *
import pandas as pd
import os

def fetch_all_symbols():
    """
    获取所有港股和美股的代码列表，并保存为 CSV 文件。
    """
    print("正在连接 Futu OpenD...")
    # 默认连接本地 127.0.0.1:11111
    try:
        ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    except Exception as e:
        print(f"连接失败: {e}")
        print("请确保 Futu OpenD 已运行并登录。")
        return

    # --- 1. 获取港股列表 ---
    print("\n正在获取港股 (HK) 股票列表...")
    # get_stock_basicinfo 可以获取指定市场的所有股票基础信息
    ret_hk, data_hk = ctx.get_stock_basicinfo(market=Market.HK, stock_type=SecurityType.STOCK)
    
    if ret_hk == RET_OK:
        # data_hk 是一个 DataFrame
        count = len(data_hk)
        print(f"成功获取 {count} 只港股代码！")
        
        # 筛选：我们通常只关心“主板”股票，去掉一些奇怪的创业板或暂停上市的
        # 这里简单一点，全部保存，或者你可以按 listing_date 筛选
        
        filename = "hk_symbols.csv"
        data_hk.to_csv(filename, index=False, encoding="utf-8-sig") # sig 解决中文乱码
        print(f"已保存到: {filename}")
        
        # 打印前5个看看样子
        print(data_hk[['code', 'name', 'listing_date']].head())
    else:
        print(f"获取港股失败: {data_hk}")

    # --- 2. 获取美股列表 ---
    print("\n正在获取美股 (US) 股票列表...")
    ret_us, data_us = ctx.get_stock_basicinfo(market=Market.US, stock_type=SecurityType.STOCK)
    
    if ret_us == RET_OK:
        count = len(data_us)
        print(f"成功获取 {count} 只美股代码！")
        
        filename = "us_symbols.csv"
        data_us.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"已保存到: {filename}")
        print(data_us[['code', 'name', 'listing_date']].head())
    else:
        print(f"获取美股失败: {data_us}")

    ctx.close()
    print("\n任务完成！")

if __name__ == "__main__":
    fetch_all_symbols()
