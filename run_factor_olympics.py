"""因子全能交互式体检排行榜生成器 (12岁菜鸟专属秒懂版)

功能:
1. 从数据库读取真实股票行情 (A股/港股/美股)
2. 批量计算 20+ 个因子的历史表现
3. 统计每个因子的真实预测力 (IC)、稳定得分、胜率
4. 渲染一个像游戏战力榜一样直观的大屏网页: factor_olympics.html
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_factor_demo import load_bars_from_db
from gemini_quant.factors.base import get_all_factors
from gemini_quant.evaluation.evaluator import evaluate_factor_on_symbol


def build_factor_olympics(symbol="AAPL.NASDAQ", days=300, output_file="factor_olympics.html"):
    print(f"\n🏟️ 正在从数据库加载 {symbol} 真实数据，举办【20+ 因子全明星战力奥运会】...")
    df = load_bars_from_db(symbol, days)
    if df.empty:
        print("❌ 数据库数据读取失败")
        return

    all_factors = get_all_factors()
    results = []

    for name, meta in all_factors.items():
        try:
            series = meta["func"](df)
            metrics = evaluate_factor_on_symbol(series, df["close"], forward_periods=5)
            ic = float(metrics["ic"])
            rank_ic = float(metrics["rank_ic"])
            ir = float(metrics["ic_ir"])
            win = float(metrics["win_rate"])

            # 评定等级
            if rank_ic > 0.08:
                grade = "👑 S级 (神仙主力)"
                grade_color = "#ffd700"
                advice = "预测力极强！必须给大权重"
            elif rank_ic > 0.03:
                grade = "⭐ A级 (得力干将)"
                grade_color = "#00e676"
                advice = "稳定有效，适合作为辅助组合"
            elif rank_ic > -0.03:
                grade = "⚪ B级 (中庸观望)"
                grade_color = "#90a4ae"
                advice = "预测力微弱，属于噪声"
            else:
                grade = "❌ D级 (严重反指标)"
                grade_color = "#ff5252"
                advice = "反着买或者直接淘汰踢出"

            results.append({
                "name": name,
                "category": meta["category"],
                "desc": meta["desc"],
                "rank_ic": rank_ic,
                "ic": ic,
                "ir": ir,
                "win": win,
                "grade": grade,
                "grade_color": grade_color,
                "advice": advice
            })
        except Exception as e:
            print(f"  ⚠️ 因子 {name} 评估异常: {e}")
            continue

    df_res = pd.DataFrame(results).sort_values("rank_ic", ascending=False).reset_index(drop=True)

    # 生成 HTML 表格卡片
    table_rows = ""
    for rank, r in df_res.iterrows():
        medals = {0: "🥇 冠军", 1: "🥈 亚军", 2: "🥉 季军"}.get(rank, f"第 {rank+1} 名")
        bar_width = min(abs(r["rank_ic"]) * 400, 100)
        bar_color = "#00e676" if r["rank_ic"] > 0 else "#ff5252"

        table_rows += f"""
        <tr style="border-bottom: 1px solid #263238; text-align: center;">
            <td style="padding: 14px 8px; font-weight: bold; color: #ffd700;">{medals}</td>
            <td style="text-align: left;">
                <div style="font-weight: bold; font-size: 15px; color: #00e5ff;">{r['name']}</div>
                <div style="font-size: 12px; color: #8899a6;">{r['desc']}</div>
            </td>
            <td><span style="background: #1e293b; padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #cbd5e1;">{r['category']}</span></td>
            <td>
                <span style="color: {r['grade_color']}; font-weight: bold; font-size: 13px;">{r['grade']}</span>
            </td>
            <td style="font-weight: bold; font-size: 16px; color: {'#00e676' if r['rank_ic']>0 else '#ff5252'};">
                {r['rank_ic']:+.4f}
                <div style="background: #1e293b; border-radius: 4px; height: 6px; width: 100px; margin: 4px auto 0;">
                    <div style="background: {bar_color}; height: 6px; border-radius: 4px; width: {bar_width}%;"></div>
                </div>
            </td>
            <td style="color: #cbd5e1; font-weight: bold;">{r['ir']:.2f}</td>
            <td style="color: {'#00e676' if r['win'] > 50 else '#ff5252'};">{r['win']:.1f}%</td>
            <td style="text-align: left; font-size: 13px; color: #94a3b8;">{r['advice']}</td>
        </tr>
        """

    # 统计概要
    s_count = len(df_res[df_res["rank_ic"] > 0.08])
    a_count = len(df_res[(df_res["rank_ic"] > 0.03) & (df_res["rank_ic"] <= 0.08)])
    d_count = len(df_res[df_res["rank_ic"] < -0.03])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>20+ 因子全明星战力体检大榜 — {symbol}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0b0f17;
                color: #e2e8f0;
                margin: 0;
                padding: 24px;
            }}
            .card {{
                background-color: #131b29;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }}
            .grid-4 {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }}
            .stat-box {{
                background-color: #1a2538;
                padding: 16px;
                border-radius: 8px;
                border-left: 4px solid #00e5ff;
            }}
            .stat-val {{ font-size: 26px; font-weight: bold; margin-top: 4px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
            th {{ background-color: #1a2538; padding: 12px; color: #94a3b8; font-size: 13px; }}
            .kid-guide {{
                background: linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%);
                border: 1px solid #4338ca;
                padding: 16px 20px;
                border-radius: 8px;
                margin-bottom: 24px;
            }}
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h1 style="margin: 0; color: #fff;">🏆 20+ 因子全明星战力体检大榜</h1>
                <p style="color: #94a3b8; margin-top: 6px;">评测标的: <b style="color: #00e5ff;">{symbol}</b> | 样本区间: 过去 {days} 个真实交易日</p>
            </div>
            <div style="background: #1a2538; padding: 8px 16px; border-radius: 8px; border: 1px solid #334155;">
                🎮 <b>难度模式</b>: 12 岁小白极简秒懂版
            </div>
        </div>

        <div class="kid-guide">
            <h3 style="margin-top: 0; color: #a5b4fc;">👦 12 岁菜鸟速查口诀 (不用看复杂公式):</h3>
            <p style="margin: 4px 0; color: #cbd5e1; font-size: 14px;">
                1. <b>看【Rank IC (预测战力)】:</b> 数值越高 (绿色)，说明这个因子就像“神算子”，每次它发出信号，未来 5 天股票真的跟着大涨！<br>
                2. <b>看【稳定性 (IR)】:</b> 数值大于 1.5 说明这个因子月月都灵验，不是碰运气的！<br>
                3. <b>如果是红色负数:</b> 说明在苹果上是“反指标” (比如追涨动量在美股行不通，反而是跌透了抄底才赚钱)！
            </p>
        </div>

        <div class="grid-4">
            <div class="stat-box">
                <div style="color: #94a3b8; font-size: 13px;">参评主力因子总数</div>
                <div class="stat-val" style="color: #fff;">{len(df_res)} 个</div>
            </div>
            <div class="stat-box" style="border-left-color: #ffd700;">
                <div style="color: #94a3b8; font-size: 13px;">S级 神仙主力因子</div>
                <div class="stat-val" style="color: #ffd700;">{s_count} 个</div>
            </div>
            <div class="stat-box" style="border-left-color: #00e676;">
                <div style="color: #94a3b8; font-size: 13px;">A级 靠谱有效因子</div>
                <div class="stat-val" style="color: #00e676;">{a_count} 个</div>
            </div>
            <div class="stat-box" style="border-left-color: #ff5252;">
                <div style="color: #94a3b8; font-size: 13px;">D级 淘汰反指标因子</div>
                <div class="stat-val" style="color: #ff5252;">{d_count} 个</div>
            </div>
        </div>

        <div class="card">
            <h3 style="margin-top: 0; color: #00e5ff;">📊 战力总排行榜 (从最灵验到最不灵验)</h3>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>因子名称与大白话作用</th>
                        <th>所属兵团</th>
                        <th>评定等级</th>
                        <th>预测战力 (Rank IC)</th>
                        <th>稳定性 (IR)</th>
                        <th>方向胜率</th>
                        <th>小白使用建议</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    out_p = ROOT / output_file
    out_p.write_text(html_content, encoding="utf-8")
    print(f"🎉 专属秒懂版因子战力榜已生成: {out_p}")
    return str(out_p)


if __name__ == "__main__":
    build_factor_olympics()
