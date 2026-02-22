import pytest
import pandas as pd
import numpy as np
from src.ml.model import SalesModel

@pytest.fixture
def train_df():
    return pd.DataFrame([
        {
            'price': 100.0 + i,
            'discount_pct': 5.0 + i,
            'rating': 4.0 + (i % 2),
            'feedbacks': 10 + i,
            'stock_left': 50 - i,
            'price_rank_in_category': i,
            'target_sales': 5.0 + i
        } for i in range(20)
    ])

def test_sales_model_train_success(train_df):
    model = SalesModel()
    result = model.train(train_df)
    assert result is True

def test_sales_model_train_invalid_data():
    model = SalesModel()
    df = pd.DataFrame([{'price': 100.0}])
    result = model.train(df)
    assert result is False

def test_sales_model_predict_output_shape():
    model = SalesModel()
    df = pd.DataFrame([
        {'price': 100.0, 'discount_pct': 5.0, 'rating': 4.0,
         'feedbacks': 10, 'stock_left': 5,
         'price_rank_in_category': 2}
        for _ in range(5)
    ])

    predictions = model.predict(df)
    assert len(predictions) == 5
    assert np.all(predictions == 5.0)