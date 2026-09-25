"""因子挖掘体检官 (AlphaAgent) - 模块 5 LightGBM 决策树集成

负责跨市场股票池的多因子特征工程，并引入 LightGBM 决策树集成模型，
学习非线性交叉规律（如“动量冲高但量价顶背离时的诱多识别”），产出高胜率截面 Alpha 得分。
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
    from sklearn.ensemble import GradientBoostingRegressor

from gemini_quant.agents.base_agent import BaseAgent, COLOR_YELLOW
from gemini_quant.factors.base import get_all_factors


class AlphaAgent(BaseAgent):
    """负责跨标的特征工程与 LightGBM 决策树非线性 Alpha 预测的特工"""

    def __init__(self, name: str = "Miner"):
        super().__init__(
            name=name,
            role_title="因子挖掘体检官",
            emoji="🔬",
            color_code=COLOR_YELLOW
        )
        self.factors_registry = get_all_factors()

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bars_dict: Dict[str, pd.DataFrame] = context["bars_dict"]
        aligned_dates: List[pd.Timestamp] = context["aligned_dates"]
        symbols = list(bars_dict.keys())

        # 5 大正交核心兵种
        core_factors = [
            {"name": "wq_alpha_088", "sign": 1.0,  "role": "动量先锋"},
            {"name": "wq_alpha_030", "sign": 1.0,  "role": "连阳突破"},
            {"name": "wq_alpha_081", "sign": -1.0, "role": "潜伏洗盘"},
            {"name": "qlib_std_20",  "sign": 1.0,  "role": "波动防暴"},
            {"name": "wq_alpha_022", "sign": -1.0, "role": "量价背离"}
        ]

        self.log("激活【模块 5: LightGBM 机器学习决策树大脑】开始特征提取...")
        
        # 1. 提取所有标的的因子特征矩阵
        feature_tables: Dict[str, pd.DataFrame] = {}
        for sym, df in bars_dict.items():
            feat_dict = {}
            for f in core_factors:
                fname = f["name"]
                sign = f["sign"]
                if fname in self.factors_registry:
                    try:
                        s = self.factors_registry[fname]["func"](df)
                        mean = s.rolling(60, min_periods=20).mean()
                        std = s.rolling(60, min_periods=20).std() + 1e-6
                        z = ((s - mean) / std).clip(-3.0, 3.0)
                        feat_dict[fname] = (z * sign).fillna(0.0)
                    except Exception:
                        feat_dict[fname] = pd.Series(0.0, index=df.index)
                else:
                    feat_dict[fname] = pd.Series(0.0, index=df.index)

            # 额外加入 5 日价格动量特征与 20 日波动特征
            feat_dict["ret_5d"] = df["close"].pct_change(5).fillna(0.0).clip(-0.2, 0.2)
            feat_dict["vol_ratio"] = (df["volume"] / (df["volume"].rolling(20).mean() + 1e-6)).fillna(1.0).clip(0.2, 5.0)

            feature_tables[sym] = pd.DataFrame(feat_dict)

        # 2. 构建多标的联合训练集 (以未来 5 天收益率为预测目标)
        train_rows_X = []
        train_rows_Y = []
        forward_days = 5
        split_idx = int(len(aligned_dates) * 0.65)  # 前 65% 时间段作为严格样本内训练集

        for sym, df in bars_dict.items():
            feats = feature_tables[sym]
            forward_ret = df["close"].shift(-forward_days) / df["close"] - 1.0
            
            valid_mask = (~forward_ret.isna()) & (df.index < split_idx)
            if valid_mask.sum() > 50:
                train_rows_X.append(feats.loc[valid_mask])
                train_rows_Y.append(forward_ret.loc[valid_mask])

        if train_rows_X:
            X_train = pd.concat(train_rows_X, ignore_index=True)
            y_train = pd.concat(train_rows_Y, ignore_index=True)

            self.log(f"正在对跨标的 {len(X_train)} 条特征样本运行 {'LightGBM' if HAS_LGBM else 'GradientBoosting'} 树模型拟合 (防止过拟合: depth=3, lr=0.03)...")
            if HAS_LGBM:
                model = lgb.LGBMRegressor(
                    n_estimators=80,
                    max_depth=3,
                    learning_rate=0.03,
                    min_child_samples=20,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=60,
                    max_depth=3,
                    learning_rate=0.03,
                    random_state=42
                )
            model.fit(X_train, y_train)

            # 3. 对全历史时间序列进行前向非线性打分预测
            pred_scores_dict = {}
            for sym in symbols:
                feats = feature_tables[sym]
                preds = model.predict(feats)
                # 结合基准正交因子线性分，平滑极端预测
                linear_baseline = feats[[f["name"] for f in core_factors]].mean(axis=1).values
                blended = preds * 0.7 + linear_baseline * 0.3 * 0.05
                pred_scores_dict[sym] = blended
        else:
            self.log_warning("训练样本偏少，降级为正交多因子加权打分模式...")
            pred_scores_dict = {
                sym: feature_tables[sym][[f["name"] for f in core_factors]].mean(axis=1).values
                for sym in symbols
            }

        # 4. 横截面标准化 (Cross-Sectional Z-Score)
        raw_composite_df = pd.DataFrame(pred_scores_dict, index=aligned_dates)
        cs_mean = raw_composite_df.mean(axis=1)
        cs_std = raw_composite_df.std(axis=1) + 1e-6
        cs_scores_df = raw_composite_df.sub(cs_mean, axis=0).div(cs_std, axis=0)

        self.log_success(f"LightGBM 非线性决策打分完成！成功输出 {cs_scores_df.shape[0]} 天 × {cs_scores_df.shape[1]} 标的的智能 Alpha 信号。")

        context["alpha_scores_df"] = cs_scores_df
        context["core_factors"] = core_factors
        return context
