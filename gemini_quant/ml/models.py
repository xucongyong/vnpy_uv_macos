from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, classification_report
import pandas as pd
import numpy as np
# try:
#     import xgboost as xgb
# except ImportError:
#     print("Warning: xgboost not installed. XGBoostModel will not work.")

class MachineLearningModel:
    """
    ML 模型基类
    """
    def train(self, X_train, y_train):
        raise NotImplementedError

    def predict(self, X_test):
        raise NotImplementedError

class RandomForestAlpha(MachineLearningModel):
    """
    随机森林预测策略
    """
    def __init__(self, n_estimators=100, max_depth=5, mode="classification"):
        """
        :param mode: 'classification' (预测涨跌 1/0) 或 'regression' (预测具体涨幅)
        """
        self.mode = mode
        if mode == "classification":
            self.model = RandomForestClassifier(
                n_estimators=n_estimators, 
                max_depth=max_depth, 
                random_state=42,
                n_jobs=-1 # 使用所有 CPU 核
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_estimators, 
                max_depth=max_depth, 
                random_state=42,
                n_jobs=-1
            )

    def train(self, X_train, y_train):
        print(f"🌲 正在训练随机森林 ({self.mode})...")
        self.model.fit(X_train, y_train)
        print("✅ 训练完成")

    def predict(self, X_test):
        return self.model.predict(X_test)
    
    def predict_proba(self, X_test):
        """只对分类模型有效，返回概率"""
        if self.mode == "classification":
            return self.model.predict_proba(X_test)
        return None

    def get_feature_importance(self, feature_names):
        """获取因子重要性排序"""
        importances = self.model.feature_importances_
        df = pd.DataFrame({
            "Factor": feature_names,
            "Importance": importances
        })
        return df.sort_values(by="Importance", ascending=False)

# 可以在这里继续添加 XGBoostModel, LSTMModel 等
