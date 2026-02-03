# 🌌 GEMINI QUANTITATIVE ARCHITECTURE
# 量化交易终极架构图谱 (The Master Plan)

> **目标**: 构建一个融合传统金融数学与现代人工智能 (AI) 的全栈量化交易系统。
> **状态**: 🟢 进行中 (Phase 2: 因子库构建)

---

## 🏗️ Phase 1: 基础设施 (Infrastructure) [已完成]
*没有地基，无法盖楼。*
- [x] **数据获取**: Yahoo Finance / Futu API 接口打通。
- [x] **回测引擎**: 基于 VNPY 的事件驱动回测引擎。
- [x] **批量测试**: `batch_backtest.py` 支持多股票、多参数网格遍历。
- [x] **可视化**: 基础的收益率曲线和统计报表。

---

## 🧱 Phase 2: 因子工厂 (Alpha Factory) [进行中]
*因子是量化的燃料。我们将建立一个包含 50+ 因子的军火库。*

### 2.1 基础技术因子 (Technical)
- [x] **Trend (趋势)**: 
    - [x] Dual MA (双均线)
    - [ ] MACD (平滑异同移动平均)
    - [ ] Trix (三重指数平滑)
    - [ ] ADX (平均趋向指标 - 趋势强度)
- [ ] **Momentum (动量)**:
    - [ ] ROC (变动率)
    - [ ] RSI (相对强弱)
    - [ ] CMO (钱德动量摆动)
- [ ] **Volatility (波动率)**:
    - [ ] ATR (平均真实波幅)
    - [ ] Bollinger Bands (布林带)
    - [ ] Keltner Channels (肯特纳通道)
- [ ] **Volume (量价)**:
    - [ ] OBV (能量潮)
    - [ ] VWAP (成交量加权平均价)
    - [ ] MFI (资金流量指标)

### 2.2 统计与数学因子 (Math & Stat)
- [ ] **Hurst Exponent**: 赫斯特指数 (判断是趋势还是震荡)
- [ ] **Kalman Filter**: 卡尔曼滤波 (去噪，提取真实价格)
- [ ] **Linear Regression Slope**: 线性回归斜率
- [ ] **Spearman Correlation**: 斯皮尔曼相关系数 (IC分析核心)

### 2.3 另类因子 (Alternative)
- [ ] **Sentiment Score**: 基于 NLP (BERT/LLM) 的新闻/推特情绪打分。
- [ ] **Fear & Greed**: 恐慌贪婪指数。

---

## 🤖 Phase 3: 机器学习策略 (Machine Learning)
*从 "人工规则" 进化到 "数据驱动"。*

### 3.1 监督学习 (Supervised Learning)
*预测目标: Next Day Return (涨跌分类) 或 Next Price (回归预测)*
- [ ] **Random Forest (随机森林)**: 
    - *优势*: 可解释性强，自带 Feature Importance (因子筛选神器)。
- [ ] **XGBoost / LightGBM**: 
    - *优势*: 竞赛级算法，处理表格数据最强，速度快。
- [ ] **SVM (支持向量机)**: 
    - *优势*: 适合小样本寻找非线性边界。

### 3.2 无监督学习 (Unsupervised Learning)
- [ ] **K-Means / DBSCAN**: 
    - *应用*: 股票聚类 (Clustering)，找出走势相似的股票进行配对交易 (Pairs Trading)。
- [ ] **PCA (主成分分析)**: 
    - *应用*: 因子降维，从 100 个因子中提取 5 个主成分，消除多重共线性。

---

## 🧠 Phase 4: 深度学习 (Deep Learning)
*捕捉时间序列中的复杂模式。*

- [ ] **LSTM / GRU (RNN)**: 
    - *应用*: 专门处理时间序列数据，拥有“记忆”能力，预测未来走势。
- [ ] **1D-CNN**: 
    - *应用*: 像识别图片一样识别 K 线图中的“形态”（如头肩底）。
- [ ] **Transformer (Attention)**: 
    - *应用*: 目前最先进的架构 (Time-GPT)，捕捉长距离依赖关系。

---

## 🎮 Phase 5: 强化学习 (Reinforcement Learning)
*训练一个 AI Agent (智能体) 自己炒股。*

- [ ] **Deep Q-Network (DQN)**: 
    - *动作*: [买入, 卖出, 持仓]。Agent 通过不断试错学习最佳策略。
- [ ] **PPO (Proximal Policy Optimization)**: 
    - *优势*: OpenAI 最爱的算法，稳定性高，适合连续动作 (如决定买入 35% 仓位)。

---

## 🛡️ Phase 6: 资金管理与风控 (Money Management)
*这才是活下来的关键。*

- [ ] **Kelly Criterion (凯利公式)**: 
    - *功能*: 科学计算最佳下注比例，最大化长期财富。
- [ ] **Risk Parity (风险平价)**: 
    - *功能*: 根据波动率分配仓位，波动大的少买，波动小的多买。
- [ ] **Stop Loss / Trailing Stop**: 
    - *功能*: 动态止损与追踪止盈逻辑。

---

## 🚀 Execution Plan (执行计划)

1.  **完善因子库**: 编写 `factor_library.py`，把 Phase 2 里的经典指标全部实现。
2.  **ML 预测器**: 编写 `x_ml_strategy.py`，集成 Random Forest，用因子预测涨跌。
3.  **组合回测**: 跑通全市场回测，选出 "Top Alpha"。
4.  **实盘对接**: 连接 IB 或 Futu 接口进行模拟盘跑单。
