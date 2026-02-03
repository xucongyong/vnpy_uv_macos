# 🏗️ Gemini Quant System Architecture Plan
# 量化交易系统架构清单

> **版本**: v1.0
> **目标**: 构建一个模块化、可扩展、融合传统金融数学与现代 AI 的全栈量化系统。
> **工作流**: 架构清单确认 -> 逐个模块代码实现 -> 单元测试 -> 组合回测。

---

## 1. 🧪 因子库 (Factor Library)
*负责将市场数据转化为数学信号 (Input Features)。*

### 1.1 技术面因子 (Technical Indicators)
*   [ ] **趋势型 (Trend)**:
    *   Dual MA (双均线差值)
    *   MACD (平滑异同移动平均)
    *   ADX (趋势强度，过滤震荡)
    *   TRIX (三重指数平滑)
*   [ ] **动量型 (Momentum)**:
    *   RSI (相对强弱指数)
    *   ROC (变动率)
    *   Momentum (MOM, 纯动量)
    *   CMO (钱德动量摆动指标)
*   [ ] **波动率型 (Volatility)**:
    *   ATR (平均真实波幅, 用于止损)
    *   Bollinger Band Width (布林带宽度, 预测变盘)
    *   StdDev (标准差)
*   [ ] **量价型 (Volume)**:
    *   OBV (能量潮)
    *   VWAP (成交量加权平均价)
    *   Volume Ratio (量比)

### 1.2 学术界因子 (Alpha 101)
*   [ ] **Alpha 001**: `rank(Ts_ArgMax(SignedPower((returns < 0 ? stddev(returns, 20) : close), 2.), 5)) - 0.5` (经典公式因子)
*   [ ] **Alpha 101系列**: 逐步实现《101 Formulaic Alphas》中的高胜率因子。

### 1.3 预测市场专用因子 (Prediction Market Factors)
*   *基于 @reference/test_1.md*
*   [ ] **Arbitrage Spread**: 无套利价差因子 (`1 - (Bid_Yes + Bid_No)`)。
*   [ ] **BSM Deviation**: 风险中性概率偏离 (`Polymarket_Price` vs `BSM_Price`)。
*   [ ] **Liquidity Depth**: 订单簿深度差因子 (流动性错配捕捉)。
*   [ ] **Time Decay**: 临期时间价值衰减因子。

---

## 2. ⚔️ 策略库 (Strategy Library)
*负责接收因子信号，执行买卖逻辑 (Execution Logic)。*

### 2.1 经典 CTA 策略 (Classic CTA)
*   [ ] **Trend Following**: 趋势跟踪 (突破买入，跌破卖出)。
*   [ ] **Mean Reversion**: 均值回归 (RSI 超买做空，布林下轨抄底)。
*   [ ] **Turtle Trading**: 海龟法则 (唐奇安通道突破 + 加仓逻辑)。
*   [ ] **Grid Trading**: 网格交易 (震荡市自动高抛低吸)。

### 2.2 组合策略 (Ensemble Strategies)
*   [ ] **Multi-Factor Score**: 多因子打分法 (例如: 均线金叉 + RSI < 50 + 量比 > 1 = 买入)。
*   [ ] **Risk Parity**: 风险平价策略 (根据波动率动态调整仓位)。

---

## 3. 🧠 机器学习库 (Machine Learning Library)
*负责预测涨跌概率、筛选有效因子 (The Brain)。*

### 3.1 因子预处理 (Preprocessing)
*   [ ] **Standardization**: Z-Score 标准化 (让不同量纲的因子可以比较)。
*   [ ] **Labeling**: 自动标注未来 N 天的涨跌 (作为训练目标 Y)。

### 3.2 因子筛选 (Feature Selection)
*   [ ] **LASSO Regression**: 利用 L1 正则化自动将无效因子的权重降为 0。
*   [ ] **Elastic Net**: 结合 L1 和 L2 正则化，处理多重共线性。
*   [ ] **PCA**: 主成分分析 (降维)。
*   [ ] **Random Forest Importance**: 利用随机森林输出因子重要性排序。

### 3.3 预测模型 (Prediction Models)
*   [ ] **Random Forest Classifier**: 随机森林分类器 (预测 涨/跌)。
*   [ ] **XGBoost / LightGBM**: 梯度提升树 (目前最强表格数据模型)。
*   [ ] **LSTM (Deep Learning)**: 长短期记忆网络 (处理时间序列，预测股价曲线)。

### 3.4 强化学习 (Reinforcement Learning)
*   [ ] **Q-Learning / DQN**: 离散动作空间 (买/卖/持)。
*   [ ] **PPO**: 连续动作空间 (决定最佳仓位比例)。

---

## 4. ⚖️ 套利库 (Arbitrage Library)
*负责寻找无风险或低风险的价差 (The Sniper)。*

### 4.1 统计套利 (Statistical Arbitrage)
*   [ ] **Pairs Trading**: 配对交易 (协整性检验, 做多低估/做空高估)。
*   [ ] **Basket Arbitrage**: 一篮子股票套利。

### 4.2 跨市场套利 (Cross-Market)
*   [ ] **Crypto-Derivatives**: 现货 vs 期货基差套利。
*   [ ] **Prediction Market Arb**: 预测市场 (Polymarket) vs 外部期权 (Deribit) 对冲套利 (实现 `test_1.md` 的核心逻辑)。

### 4.3 波动率套利 (Volatility Arb)
*   [ ] **Gamma Scalping**: 动态对冲。

---

## 📅 下一步开发计划 (Roadmap)

1.  **因子库搭建**: 实现 `factors/` 目录下的 5 个核心技术因子。
2.  **LASSO 筛选器**: 编写脚本，用 LASSO 跑一遍这 5 个因子，看 MSTR 到底吃哪一套。
3.  **预测市场套利**: 实现 `arbitrage/prediction_arb.py`，把论文里的逻辑代码化。
