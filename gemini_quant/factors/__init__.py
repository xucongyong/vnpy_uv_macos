"""因子工厂包入口
"""
from gemini_quant.factors.base import register_factor, get_all_factors
import gemini_quant.factors.core_factors

__all__ = ["register_factor", "get_all_factors"]
