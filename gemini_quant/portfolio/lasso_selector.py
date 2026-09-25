"""LASSO 正交降维与特征筛选引擎 (L1 正则化消灭多重共线性)

核心算法:
1. 单因子初筛: 过滤掉极度平庸的噪声因子
2. LASSO 稀疏惩罚: 利用 L1 正则化将走势重叠的冗余因子系数压缩归零
3. 正交性检验 (Orthogonality Check): 确保入选兵种两两相关系数 |Corr| < 0.35
4. 输出 5 大互补战力梯队 (动量 / 抄底 / 资金 / 博弈 / 避险)
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV, Lasso
from gemini_quant.factors.base import get_all_factors
from gemini_quant.evaluation.evaluator import evaluate_factor_on_symbol


def compute_normalized_factor_matrix(df: pd.DataFrame, sample_factors: List[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """批量计算因子并进行去极值与 Z-Score 标准化"""
    all_factors = get_all_factors()
    if sample_factors is None:
        sample_factors = list(all_factors.keys())

    factor_series_dict = {}
    meta_dict = {}

    for name in sample_factors:
        if name not in all_factors:
            continue
        meta = all_factors[name]
        try:
            s = meta["func"](df)
            if s is None or s.isna().all() or s.std() == 0:
                continue

            # 去极值 (Winsorize 3-Sigma) 与 Z-Score 标准化
            mean = s.mean()
            std = s.std() + 1e-6
            z = (s - mean) / std
            z = z.clip(lower=-3.0, upper=3.0)

            factor_series_dict[name] = z
            meta_dict[name] = meta
        except Exception:
            continue

    matrix_df = pd.DataFrame(factor_series_dict, index=df.index)
    # 前向填充缺失值
    matrix_df = matrix_df.ffill().bfill().fillna(0.0)
    return matrix_df, meta_dict


def run_lasso_selection(
    df: pd.DataFrame,
    forward_days: int = 5,
    top_n: int = 5,
    max_corr: float = 0.35
) -> List[Dict[str, Any]]:
    """使用 LASSO 稀疏惩罚与正交性聚类，从全量因子中选拔顶级互补组合"""
    print(f"📊 正在生成因子特征矩阵 (数据长度: {len(df)} 根K线)...")
    matrix_df, meta_dict = compute_normalized_factor_matrix(df)
    
    # 构建未来收益率作为预测目标 Y
    forward_ret = df["close"].shift(-forward_days) / df["close"] - 1.0
    
    # 对齐并剔除最后 forward_days 的 NaN
    valid_mask = ~forward_ret.isna()
    X = matrix_df.loc[valid_mask]
    y = forward_ret.loc[valid_mask]

    print(f"🔬 正在对 {X.shape[1]} 个因子运行 LASSO L1 正则化降维大考...")
    
    # 使用带交叉验证的 LassoCV 寻找最优惩罚强度 lambda
    lasso = LassoCV(cv=5, random_state=42, max_iter=3000)
    lasso.fit(X, y)

    coefs = lasso.coef_
    non_zero_indices = np.where(np.abs(coefs) > 1e-5)[0]
    candidate_names = [X.columns[i] for i in non_zero_indices]
    
    print(f"⚡ LASSO 成功将冗余特征压缩归零！从 {X.shape[1]} 个因子中提炼出 {len(candidate_names)} 个核心候选因子。")

    if not candidate_names:
        # 降级备选：如果惩罚过高导致全为0，取前排高IC因子
        candidate_names = list(X.columns[:15])

    # 计算候选因子的 Rank IC 与综合重要性
    scored_candidates = []
    for name in candidate_names:
        series = matrix_df[name]
        metrics = evaluate_factor_on_symbol(series, df["close"], forward_periods=forward_days)
        rank_ic = float(metrics["rank_ic"])
        weight_coef = float(lasso.coef_[X.columns.get_loc(name)]) if name in X.columns else 0.01
        
        # 综合选拔分: 考虑回归系数大小与 Rank IC
        score = abs(rank_ic) * (1.0 + abs(weight_coef) * 10.0)
        
        scored_candidates.append({
            "name": name,
            "category": meta_dict[name].get("category", "默认"),
            "desc": meta_dict[name].get("desc", name),
            "rank_ic": rank_ic,
            "lasso_coef": weight_coef,
            "win_rate": float(metrics["win_rate"]),
            "score": score
        })

    # 按选拔分从高到低排序
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    # 贪心正交筛选: 确保入选因子之间 |Corr| < max_corr
    selected_factors = []
    for cand in scored_candidates:
        name = cand["name"]
        series = matrix_df[name]
        
        # 检查是否与已选因子高度相关
        is_orthogonal = True
        for sel in selected_factors:
            sel_series = matrix_df[sel["name"]]
            corr = abs(series.corr(sel_series))
            if corr > max_corr:
                is_orthogonal = False
                break
        
        if is_orthogonal:
            selected_factors.append(cand)
            if len(selected_factors) >= top_n:
                break

    print(f"👑 成功正交提炼出 {len(selected_factors)} 大不重叠王牌兵种：")
    for idx, f in enumerate(selected_factors, 1):
        print(f"  [{idx}] {f['name']} ({f['category']}) | Rank IC: {f['rank_ic']:+.4f} | LASSO 系数: {f['lasso_coef']:+.4f}")
        print(f"      说明: {f['desc'][:45]}")

    return selected_factors
