"""因子工厂基础设施: 注册器与因子装饰器
"""

from typing import Callable, Dict, Any
import pandas as pd

# 全局因子注册表: {因子英文名: {"func": 函数, "name": 名字, "category": 分类, "desc": 说明}}
FACTOR_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_factor(name: str, category: str = "general", desc: str = ""):
    """因子注册装饰器。
    
    用法:
        @register_factor(name="momentum_5d", category="momentum", desc="5日价格动量")
        def factor_momentum_5d(df: pd.DataFrame) -> pd.Series:
            return df["close"].pct_change(5)
    """
    def decorator(func: Callable[[pd.DataFrame], pd.Series]):
        FACTOR_REGISTRY[name] = {
            "name": name,
            "category": category,
            "desc": desc,
            "func": func
        }
        return func
    return decorator


def get_all_factors() -> Dict[str, Dict[str, Any]]:
    """获取所有已注册的因子。"""
    return FACTOR_REGISTRY
