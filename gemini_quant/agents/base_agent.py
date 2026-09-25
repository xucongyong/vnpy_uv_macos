"""TradingAgents 核心基础基类与通信协议

定义统一的智能体接口、终端富文本着色日志、状态总线与上下文数据协议。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any


# 终端 ANSI 色彩配置
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_PURPLE = "\033[35m"
COLOR_BLUE = "\033[34m"


class BaseAgent(ABC):
    """TradingAgents 智能体基类"""

    def __init__(self, name: str, role_title: str, emoji: str, color_code: str = COLOR_CYAN):
        self.name = name
        self.role_title = role_title
        self.emoji = emoji
        self.color_code = color_code
        self.log_history = []

    def log(self, message: str, level: str = "INFO"):
        """统一着色带身份标识的终端日志"""
        now_str = datetime.now().strftime("%H:%M:%S")
        formatted = f"{self.color_code}[{now_str}] {self.emoji} 【{self.role_title} · {self.name}】{COLOR_RESET} {message}"
        print(formatted)
        self.log_history.append({"time": now_str, "level": level, "msg": message})

    def log_success(self, message: str):
        """成功日志"""
        self.log(f"{COLOR_GREEN}✔ {message}{COLOR_RESET}")

    def log_warning(self, message: str):
        """告警日志"""
        self.log(f"{COLOR_YELLOW}⚠ {message}{COLOR_RESET}", level="WARN")

    def log_error(self, message: str):
        """错误日志"""
        self.log(f"{COLOR_RED}✘ {message}{COLOR_RESET}", level="ERROR")

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体本职任务并产出结构化上下文"""
        pass
