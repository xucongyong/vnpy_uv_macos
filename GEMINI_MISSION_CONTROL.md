# 🛰️ GEMINI QUANT: MISSION CONTROL
# 项目核心架构与 AI 开发规范

> **AI 必读**: 在对本项目进行任何增删改之前，必须先读取本文件以确保代码逻辑与架构风格的一致性。

---

## 🏗️ 1. 系统架构图 (System Architecture)

本项目采用模块化设计，分为四大核心“车间”：

1.  **`gemini_quant/factors/` (原料车间)**:
    *   **职责**: 存放纯数学计算逻辑。
    *   **规范**: 仅接收数据 (DataFrame/ArrayManager)，返回数值或信号。不允许有交易逻辑。
    *   **子模块**: `technical.py` (经典指标), `alpha101.py` (学术指标)。

2.  **`gemini_quant/ml/` (大脑车间)**:
    *   **职责**: 存放数据处理、因子筛选 (LASSO) 和 预测模型 (Random Forest, XGBoost)。
    *   **规范**: 使用 `scikit-learn` 风格的封装。

3.  **`gemini_quant/strategies/` (决策车间)**:
    *   **职责**: 存放具体的交易策略类 (基于 VNPY CtaTemplate)。
    *   **规范**: 从 `factors` 调用指标，从 `ml` 调用预测模型。

5. **`research/` (投研情报车间)**:
    *   **职责**: 自动搜集全球论文(Arxiv)、机构研报，并利用 AI 提取交易因子。
    *   **规范**: 抓取的数据存放在 `papers/` 和 `reports/`，生成的代码存放在 `gemini_quant/factors/research_factors.py`。

---

## 📂 2. 目录结构规范 (File Structure)

```text
/vnpy_uv_macos/            <-- 项目根目录
├── gemini_quant/          <-- 核心逻辑包
│   ├── factors/           <-- 因子库 (包含 Alpha101, research_factors)
│   ├── ml/                <-- 机器学习库
│   ├── strategies/        <-- 策略库
│   └── arbitrage/         <-- 套利库
├── research/              <-- 投研情报中心 (New!)
│   ├── papers/            <-- 存放 PDF 论文
│   ├── reports/           <-- 存放机构研报
│   └── arxiv_scanner.py   <-- 自动搜集工具
├── scripts/               <-- 实验脚本
├── GEMINI_MISSION_CONTROL.md <-- 指挥中心
└── GEMINI_ROADMAP.md      <-- 进度表
```

---

## 🤖 3. AI 代理操作指南 (Agent Instructions)

### 3.4 投研一体化流程 (Research-to-Production - R2P):
1.  **情报搜集**: 运行 `research/arxiv_scanner.py` 获取最新研究。
2.  **理解与翻译**: AI 读取 PDF 摘要，将数学公式翻译为 Python 逻辑。
3.  **自动测试**: 将新因子加入回测序列，验证其在 MSTR 等标的上的有效性。

### 3.1 当你想添加一个“新因子”时：
1.  **位置**: 在 `gemini_quant/factors/` 下创建或修改文件。
2.  **命名**: 必须以 `factor_` 开头。
3.  **文档**: 在函数注释中写明数学公式。

### 3.2 当你想添加一个“机器学习模型”时：
1.  **位置**: 在 `gemini_quant/ml/models.py` 中继承 `MachineLearningModel` 基类。
2.  **库**: 优先使用 `scikit-learn` 或 `lightgbm`。

### 3.3 当你想运行回测时：
1.  **工具**: 使用 `uv run` 确保环境一致。
2.  **记录**: 结果必须保存到 `batch_backtest_results.csv` 并同步更新 `GEMINI_ROADMAP.md`。

---

## 🎯 4. 当前核心任务 (Active Task)
---

## 🔄 5. 标准操作流程 (Standard Operational Workflow)

当你想要开发并验证一个新的交易想法时，请遵循以下 SOP：

### 步骤 A: 因子开发 (Factor Creation)
1. 在 `gemini_quant/factors/` 下编写数学公式。
2. 目标：将原始价格变成有意义的“分数值”。

### 步骤 B: 因子筛选 (Feature Selection)
1. 运行 `gemini_quant/ml/feature_selection.py`。
2. 目标：使用 LASSO 剔除与收益无关的噪音因子。

### 步骤 C: 策略组装 (Strategy Assembly)
1. 在 `gemini_quant/strategies/` 下创建策略类。
2. 引入筛选后的因子，设置买卖门槛（例如：模型预测概率 > 0.6）。

### 步骤 D: 批量回测 (Mass Backtesting)
1. 使用 `scripts/batch_backtest.py` 在多个品种（TSLA, NVDA, MSTR）上测试。
2. 目标：寻找具有普适性的盈利参数。

### 步骤 E: 结果存档 (Archiving)
1. 将表现最好的组合更新至 `GEMINI_ROADMAP.md` 的“冠军榜”中。
