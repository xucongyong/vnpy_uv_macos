import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
import warnings

# 忽略一些不重要的警告
warnings.filterwarnings('ignore')

def run_battle():
    # 1. 抓取 MSTR 数据
    print("📡 1. 正在抓取 MSTR 历史日记...")
    symbol = "MSTR"
    # 这里用 yfinance 下载数据
    df = yf.download(symbol, start="2022-01-01", progress=False)
    
    if df.empty:
        print("❌ 哎呀，没抓到数据！可能是网络问题。")
        return

    # yfinance 新版本返回多级索引，需要处理一下
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. 构造因子库 (找线索)
    print("🕵️ 2. 侦探正在寻找线索 (计算因子)...")
    # 为了避免 SettingWithCopyWarning，我们显式创建副本
    df = df.copy()
    
    df['Returns'] = df['Close'].pct_change()
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA_Diff'] = (df['MA5'] - df['MA10']) / df['MA10'] # 均线差
    df['Vol_Change'] = df['Volume'].pct_change() # 成交量变化
    df['Volatility'] = df['Returns'].rolling(10).std() # 波动率

    # 制造一些“垃圾线索”来看看 LASSO 聪不聪明
    df['Garbage1'] = np.random.randn(len(df)) 
    df['Garbage2'] = np.random.randn(len(df))

    # 目标：预测明天是涨(1)还是跌(0)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    # 清理掉最前面没数据的几天
    df_clean = df.dropna()

    # 准备数据
    features = ['MA_Diff', 'Vol_Change', 'Volatility', 'Garbage1', 'Garbage2']
    X = df_clean[features]
    y = df_clean['Target']

    # 3. LASSO 筛选因子 (严厉的老师)
    print("🗑️ 3. 严厉老师 LASSO 正在检查线索...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 开始筛选
    lasso = LassoCV(cv=5, random_state=42).fit(X_scaled, y)
    
    # 看看老师留下了谁
    # 这里的coef_就是每个线索的分数，0表示被扔掉了
    coefs = pd.Series(lasso.coef_, index=features)
    print("\n📋 线索评分表:")
    print(coefs.sort_values(ascending=False))
    
    # 选出非0的特征
    selected_features = coefs[abs(coefs) > 1e-4].index.tolist()
    print(f"\n✅ 老师留下的有用线索: {selected_features}")
    
    if not selected_features:
        print("⚠️ 老师觉得所有线索都是垃圾... 我们强制使用均线差试试。")
        selected_features = ['MA_Diff']

    # 4. 随机森林训练 (小矮人开会)
    print("\n🌲 4. 100个小矮人(随机森林)正在学习历史日记...")
    
    # 拿最后一天的数据来预测明天
    X_today = X[selected_features].iloc[[-1]] 
    
    # 拿之前的所有数据来训练
    X_train = X[selected_features].iloc[:-1]
    y_train = y.iloc[:-1]

    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)

    # 5. 预测明天
    pred = rf.predict(X_today)[0]
    prob = rf.predict_proba(X_today)[0] # 投票比例

    print("\n" + "="*40)
    print(f"🔮 MSTR 明日走势预测")
    print("="*40)
    
    if pred == 1:
        print(f"👉 结果: 📈 看涨 (UP)")
        print(f"🔥 信心: {prob[1]*100:.1f}% 的小矮人认为会涨")
    else:
        print(f"👉 结果: 📉 看跌 (DOWN)")
        print(f"❄️ 信心: {prob[0]*100:.1f}% 的小矮人认为会跌")
    print("="*40)

if __name__ == "__main__":
    run_battle()
