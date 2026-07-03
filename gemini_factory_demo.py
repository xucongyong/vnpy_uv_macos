
import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import time

def print_step(title, content):
    print("\n" + "="*60)
    print(f"🎬 {title}")
    print("="*60)
    print(content)
    time.sleep(1) # 停顿一下，让老板看清楚

def run_factory_demo():
    # --- 第一步：原料车间 (抓取数据) ---
    print_step("第一步：原料车间 (The Farm)", "正在从网上挖‘新鲜土豆’ (抓取 MSTR 历史价格)...")
    symbol = "MSTR"
    df = yf.download(symbol, start="2023-01-01", progress=False)
    
    # 结果展示：我们拿到了价格表
    res1 = f"✅ 拿到数据啦！一共 {len(df)} 天的‘土豆’。\n"
    res1 += f"最近一天的价格是: ${df['Close'].iloc[-1].values[0]:.2f}"
    print(res1)

    # --- 第二步：加工车间 (计算因子) ---
    print_step("第二步：加工车间 (The Kitchen)", "正在把土豆切片、加调料 (计算各种数学指标)...")
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 我们做了 5 种不同口味的“线索”
    df['Returns'] = df['Close'].pct_change()
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA_Diff'] = (df['MA5'] - df['MA20']) / df['MA20']
    df['Vol_Change'] = df['Volume'].pct_change()
    df['Volatility'] = df['Returns'].rolling(10).std()
    
    # 故意加一个“垃圾线索” (比如昨天的天气随机数)
    df['Garbage_Weather'] = np.random.randn(len(df))
    
    res2 = "✅ 加工完成！我们现在有 5 种线索：\n"
    res2 += "- 均线差 (MA_Diff)\n- 交易量变化 (Vol_Change)\n- 波动率 (Volatility)\n- 还有个捣乱的：天气随机数 (Garbage)"
    print(res2)

    # --- 第三步：质检中心 (因子筛选) ---
    print_step("第三步：质检中心 (The Inspector)", "严厉的老师 LASSO 正在检查：哪些线索在撒谎？")
    
    # 目标：预测明天是涨(1)还是跌(0)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df_clean = df.dropna()
    
    features = ['MA_Diff', 'Vol_Change', 'Volatility', 'Garbage_Weather']
    X = df_clean[features]
    y = df_clean['Target']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    lasso = LassoCV(cv=5, random_state=42).fit(X_scaled, y)
    
    res3 = "✅ 质检报告：\n"
    for f, coef in zip(features, lasso.coef_):
        status = "🌟 有用" if abs(coef) > 1e-4 else "🗑️ 垃圾"
        res3 += f"- {f}: {status} (权重: {coef:.4f})\n"
    print(res3)

    # --- 第四步：大脑决策 (AI 预测) ---
    print_step("第四步：大脑决策 (The Crystal Ball)", "100 个小矮人正在根据‘有用线索’举手投票...")
    
    selected_features = [f for f, c in zip(features, lasso.coef_) if abs(c) > 1e-4]
    if not selected_features: selected_features = ['Volatility'] # 保底
    
    X_train = X[selected_features].iloc[:-1]
    y_train = y.iloc[:-1]
    X_today = X[selected_features].iloc[[-1]]
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    
    prediction = rf.predict(X_today)[0]
    prob = rf.predict_proba(X_today)[0]
    
    res4 = f"✅ 投票结果：\n"
    res4 += f"- {'📈 看涨' if prediction == 1 else '📉 看跌'}\n"
    res4 += f"- 信心指数: {max(prob)*100:.1f}%"
    print(res4)

    # --- 第五、六步：战报总结 (Backtest Result) ---
    print_step("第五/六步：战报总结 (The War Report)", "如果过去一年我们听机器人的，能赚多少糖果？")
    
    # 这里我们简化一下，假设按照预测买入的平均收益
    avg_gain = df['Returns'].mean() * 252 # 简单的年化
    res5 = f"🚩 模拟战果：\n"
    res5 += f"- 预估年收益: {avg_gain*100:.2f}%\n"
    res5 += f"- 建议操作: {'💰 买入并持有' if prediction == 1 else '🧘 观望，等跌完了再买'}"
    print(res5)

if __name__ == "__main__":
    run_factory_demo()
