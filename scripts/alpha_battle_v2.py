
import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
import sys
import os

# 确保能找到 gemini_quant 包
sys.path.append(os.getcwd())

from gemini_quant.factors.alpha101 import Alpha101

def run_alpha_battle():
    print("📡 1. 抓取 MSTR 历史数据...")
    symbol = "MSTR"
    df = yf.download(symbol, start="2022-01-01", progress=False)
    if df.empty: return
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.copy()

    print("🕵️ 2. 计算 Alpha 101 高级因子 (华尔街配方)...")
    # 调用我们的新武器库
    df['Alpha001'] = Alpha101.factor_alpha001(df)
    df['Alpha006'] = Alpha101.factor_alpha006(df)
    df['Alpha101'] = Alpha101.factor_alpha101(df)
    df['Momentum'] = Alpha101.factor_momentum_5d(df)
    df['Volatility'] = Alpha101.factor_volatility_10d(df)

    # 目标：预测明天是涨(1)还是跌(0)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df_clean = df.dropna()

    features = ['Alpha001', 'Alpha006', 'Alpha101', 'Momentum', 'Volatility']
    X = df_clean[features]
    y = df_clean['Target']

    print("🗑️ 3. LASSO 老师正在从高级因子中进行筛选...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    lasso = LassoCV(cv=5, random_state=42).fit(X_scaled, y)
    
    coefs = pd.Series(lasso.coef_, index=features)
    print("\n📋 高级因子评分表:")
    print(coefs.sort_values(ascending=False))
    
    selected_features = coefs[abs(coefs) > 1e-4].index.tolist()
    if not selected_features: selected_features = ['Alpha101'] # 强行留一个

    print(f"\n✅ 选中的核心线索: {selected_features}")

    print("\n🌲 4. 小矮人们正在学习高级线索并投票...")
    X_today = X[selected_features].iloc[[-1]]
    X_train = X[selected_features].iloc[:-1]
    y_train = y.iloc[:-1]

    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)

    pred = rf.predict(X_today)[0]
    prob = rf.predict_proba(X_today)[0]

    print("\n" + "="*40)
    print(f"🔮 MSTR 【Alpha 101 升级版】 走势预测")
    print("="*40)
    direction = "📈 涨 (UP)" if pred == 1 else "📉 跌 (DOWN)"
    print(f"预测方向: {direction}")
    print(f"信心指数: {max(prob)*100:.1f}%")
    print("="*40)

if __name__ == "__main__":
    run_alpha_battle()
