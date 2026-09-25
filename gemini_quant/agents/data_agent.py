"""数据清洗特工 (DataAgent)

负责从 PostgreSQL 中读取跨市场资产行情，执行交易日历对齐、停复牌与休市前向填充、质量校验。
"""

from typing import Dict, Any, List
import pandas as pd
import psycopg2
from gemini_quant.agents.base_agent import BaseAgent, COLOR_CYAN

DB_PARAMS = {
    "host": "v.xucongyong.com",
    "port": 5432,
    "user": "postgres",
    "password": "1121hotsren",
    "dbname": "postgres"
}


class DataAgent(BaseAgent):
    """负责跨市场异构数据清洗与对齐的特工"""

    def __init__(self, name: str = "Scout"):
        super().__init__(
            name=name,
            role_title="数据清洗特工",
            emoji="🕵️‍♂️",
            color_code=COLOR_CYAN
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        symbols: List[str] = context.get("symbols", [])
        limit_days: int = context.get("days", 750)

        self.log(f"开始对跨市场股票池 {symbols} 展开数据核验与对齐 (调取最近 {limit_days} 天行情)...")
        
        conn = psycopg2.connect(**DB_PARAMS)
        bars_dict: Dict[str, pd.DataFrame] = {}

        for sym in symbols:
            raw_sym = sym.split(".")[0]
            sql = f"""
                SELECT datetime as date, open_price as open, high_price as high, 
                       low_price as low, close_price as close, volume
                FROM quant_data.quant_data
                WHERE symbol = '{raw_sym}'
                ORDER BY datetime DESC
                LIMIT {limit_days};
            """
            df = pd.read_sql(sql, conn)
            if df.empty:
                self.log_warning(f"标的 {sym} 在数据库中未检索到任何数据！")
                continue
            
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            df = df.sort_values("date").reset_index(drop=True)
            bars_dict[sym] = df
            self.log(f"  已载入 {sym} 历史K线: {len(df)} 根 (范围: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')})")

        conn.close()

        if not bars_dict:
            raise ValueError("所有标的数据为空，无法继续后续流转！")

        # 跨市场交易日历对齐 (美股 / 港股 / A股休市日前向填充)
        all_dates = sorted(list(set.union(*[set(df["date"]) for df in bars_dict.values()])))
        aligned_df_dict: Dict[str, pd.DataFrame] = {}

        for sym, df in bars_dict.items():
            df_indexed = df.set_index("date").reindex(all_dates)
            # 价格缺失按前一日收盘价顺延填充 (休市不改变资产市值)
            df_indexed["close"] = df_indexed["close"].ffill().bfill()
            df_indexed["open"] = df_indexed["open"].fillna(df_indexed["close"])
            df_indexed["high"] = df_indexed["high"].fillna(df_indexed["close"])
            df_indexed["low"] = df_indexed["low"].fillna(df_indexed["close"])
            df_indexed["volume"] = df_indexed["volume"].fillna(0.0)
            
            cum_vol = df_indexed["volume"].cumsum()
            df_indexed["vwap"] = (df_indexed["close"] * df_indexed["volume"]).cumsum() / (cum_vol + 1e-6)
            
            aligned_df_dict[sym] = df_indexed.reset_index().rename(columns={"index": "date"})

        self.log_success(f"跨市场日历对齐完成！统一共识交易日: {len(all_dates)} 天，覆盖 {len(aligned_df_dict)} 只标的。")

        context["bars_dict"] = aligned_df_dict
        context["aligned_dates"] = all_dates
        return context
