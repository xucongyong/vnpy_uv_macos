# 强化学习策略实现指南
1. **构建环境**: 基于 `gymnasium` 编写强化学习环境（如 `CryptoPortfolioEnv`），将回测数据转化为 `State`。
2. **训练多头网络**: 使用 PyTorch 搭建 SAC + CNN + Multi-Head Attention 网络。
3. **推理部署**: 将训练好的权重保存（例如 `.pth`，或导出 `.onnx`）。然后在 `vnpy` 策略的 `__init__` 中加载，并在 `on_bars` 回调里推断动作目标仓位。
