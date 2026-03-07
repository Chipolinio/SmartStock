import pandas as pd
import numpy as np
import os
from catboost import CatBoostRegressor

class SalesModel:
    def __init__(self, model_path="catboost_sales_model.bin"):
        self.model_path = model_path
        self.features = [
            'price', 'discount_pct', 'rating',
            'feedbacks', 'stock_left', 'price_rank_in_category'
        ]
        self.model = CatBoostRegressor(
            iterations=1000,
            learning_rate=0.03,
            depth=6,
            l2_leaf_reg=3,
            loss_function='RMSE',
            random_seed=42,
            verbose=False
        )
        if os.path.exists(self.model_path):
            try:
                self.model.load_model(self.model_path)
                self._is_trained = True
            except:
                self._is_trained = False
        else:
            self._is_trained = False

    def train(self, df: pd.DataFrame):
        if df.empty or 'target_sales' not in df.columns:
            return False

        X = df[self.features]
        y = df['target_sales']

        self.model.fit(X, y)
        self.model.save_model(self.model_path)
        self._is_trained = True
        return True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self._is_trained:
            return np.zeros(len(df))

        X = df[self.features]
        try:
            prediction = self.model.predict(X)
            return np.maximum(prediction, 0)
        except Exception as e:
            print(f"Prediction error: {e}")
            return np.zeros(len(df))