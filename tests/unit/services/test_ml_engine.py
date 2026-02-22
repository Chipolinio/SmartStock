import pytest
import numpy as np
from src.ml.engine import SalesMLProvider

class MockRow:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def _asdict(self):
        return self.__dict__

@pytest.fixture
def provider():
    return SalesMLProvider()

def test_provider_mapping_and_calculation(provider, mocker):
    mocker.patch.object(provider.engine, 'predict', return_value=np.array([5.0]))

    raw_rows = [
        MockRow(
            product_id=1, price_sale=1000.0, discount_pct=10.0,
            quantity=10, price_rank=1, rating=4.5, feedbacks=100, rating_rank=1
        )
    ]

    df_result = provider.predict_sales_and_oos(raw_rows)

    assert 'price' in df_result.columns
    assert 'stock_left' in df_result.columns
    assert df_result.iloc[0]['days_to_oos'] == 2.0
    assert df_result.iloc[0]['predicted_sales'] == 5.0

def test_provider_empty_input(provider):
    df_result = provider.predict_sales_and_oos([])
    assert df_result.empty