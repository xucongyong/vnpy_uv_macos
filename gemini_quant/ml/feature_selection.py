from sklearn.linear_model import Lasso, ElasticNet, LassoCV, ElasticNetCV
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class FactorSelector:
    """
    机器学习因子筛选器
    使用 LASSO 或 ElasticNet 自动剔除无效因子，实现'降维'。
    """

    def __init__(self, method="lasso", alpha=0.001):
        """
        :param method: "lasso" 或 "elastic_net"
        :param alpha: 惩罚力度。Alpha 越大，筛选越严格（留下的因子越少）。
        """
        self.method = method
        self.alpha = alpha
        self.scaler = StandardScaler() # 因子必须先标准化，否则量纲不同没法比
        self.selector = None
        self.selected_features = []

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        训练筛选器
        :param X: 因子数据 (DataFrame), 列是因子名, 行是时间
        :param y: 预测目标 (Series), 比如'未来3日涨跌幅'
        """
        # 1. 数据标准化 (Z-Score)
        # LASSO 对数据的幅度非常敏感，必须把所有因子都缩放到均值为0，方差为1
        X_scaled = self.scaler.fit_transform(X)

        # 2. 选择模型
        if self.method == "lasso":
            # Lasso: L1正则化，会将无关特征系数压缩为0
            model = Lasso(alpha=self.alpha, random_state=42)
        elif self.method == "lasso_cv":
            # 自动寻找最佳 alpha 的 Lasso
            model = LassoCV(cv=5, random_state=42)
        elif self.method == "elastic_net":
            # ElasticNet: L1 + L2 正则化
            model = ElasticNet(alpha=self.alpha, l1_ratio=0.5, random_state=42)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        # 3. 拟合模型
        print(f"🤖 正在使用 {self.method} 筛选因子...")
        model.fit(X_scaled, y)

        # 4. 提取结果
        # SelectFromModel 会帮我们把系数不为0的特征选出来
        self.selector = SelectFromModel(model, prefit=True)
        
        # 记录被选中的列名
        support = self.selector.get_support()
        self.selected_features = X.columns[support].tolist()
        
        # 打印系数情况
        coefs = pd.Series(model.coef_, index=X.columns)
        print("\n📊 因子重要性 (LASSO 系数):")
        print(coefs[coefs != 0].sort_values(ascending=False))
        
        print(f"\n✅ 筛选完成! 输入 {X.shape[1]} 个因子 -> 留下 {len(self.selected_features)} 个有效因子")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        使用训练好的筛选器，过滤新数据
        """
        if not self.selector:
            raise ValueError("Selector not fitted yet!")
            
        X_scaled = self.scaler.transform(X)
        X_new = self.selector.transform(X_scaled)
        return pd.DataFrame(X_new, columns=self.selected_features, index=X.index)

# === 使用示例 ===
if __name__ == "__main__":
    # 模拟数据
    data = pd.DataFrame({
        "MA5": np.random.rand(100),
        "MA10": np.random.rand(100),   # 假设这是有用因子
        "RSI": np.random.rand(100) * 0.5 + np.random.rand(100), # 假设这也是有用因子
        "Garbage1": np.random.rand(100), # 垃圾因子
        "Garbage2": np.random.rand(100), # 垃圾因子
    })
    # 假设目标 y 只跟 MA10 和 RSI 有关
    target = data["MA10"] * 0.8 + data["RSI"] * 0.5 + np.random.normal(0, 0.1, 100)
    
    selector = FactorSelector(method="lasso", alpha=0.01)
    selector.fit(data, target)
