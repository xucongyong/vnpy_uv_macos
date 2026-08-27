"""策略注册表: 自动扫描所有策略文件, 按名字加载策略类。

扫描范围:
  1. strategies/ 目录下所有 .py
  2. 项目根目录下的 x_*.py

用法:
    from strategies.registry import get_strategy, list_strategies

    cls = get_strategy("dual_ma")          # 名字匹配(模糊)
    cls = get_strategy("XDualMaStrategy")  # 类名精确匹配
"""

import importlib
import sys
from pathlib import Path

from vnpy_ctastrategy import CtaTemplate

ROOT = Path(__file__).resolve().parent.parent
STRATEGY_DIR = ROOT / "strategies"


def _iter_module_paths():
    """返回 (模块名, 文件路径) 列表。"""
    paths = []
    if STRATEGY_DIR.is_dir():
        for py in sorted(STRATEGY_DIR.glob("*.py")):
            if py.name.startswith("_"):
                continue
            paths.append((f"strategies.{py.stem}", py))
    for py in sorted(ROOT.glob("x_*.py")):
        paths.append((py.stem, py))
    return paths


_CACHE: tuple[dict, dict] | None = None


def _load_classes():
    """加载所有策略类, 返回 {归一化名: 类} 和 {类名: 类}。"""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    by_norm: dict[str, type] = {}
    by_clsname: dict[str, type] = {}

    for modname, path in _iter_module_paths():
        try:
            spec = importlib.util.spec_from_file_location(modname, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[modname] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"⚠️  跳过 {path.name}: {e}")
            continue

        for name, obj in vars(mod).items():
            if not isinstance(obj, type):
                continue
            if not issubclass(obj, CtaTemplate):
                continue
            if obj is CtaTemplate:
                continue

            by_clsname[name] = obj
            by_norm[_normalize(name)] = obj

    _CACHE = (by_clsname, by_norm)
    return by_clsname, by_norm


def _normalize(name: str) -> str:
    """XDualMaStrategy -> dualma; RsiStrategy -> rsi"""
    s = name
    if s.startswith("X"):
        s = s[1:]
    if s.endswith("Strategy"):
        s = s[:-len("Strategy")]
    return s.lower().replace("_", "").replace("-", "")


def list_strategies() -> list[tuple[str, str]]:
    """列出所有可用策略 (归一化名, 类名)。"""
    by_clsname, by_norm = _load_classes()
    return sorted((n, c.__name__) for n, c in by_norm.items())


def get_strategy(name: str) -> type:
    """按名字(类名或归一化名)返回策略类。"""
    by_clsname, by_norm = _load_classes()

    if name in by_clsname:
        return by_clsname[name]

    norm = _normalize(name)
    if norm in by_norm:
        return by_norm[norm]

    # 模糊匹配: 输入包含即可
    matches = [c for n, c in by_norm.items() if norm in n]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(sorted(n for n, _ in by_norm.items() if norm in n))
        raise KeyError(f"'{name}' 匹配到多个策略: {names}")

    raise KeyError(
        f"找不到策略 '{name}'。可用策略: {', '.join(sorted(by_clsname.keys()))}"
    )


def _clsname(name: str) -> str:
    return get_strategy(name).__name__
