import pandas as pd
from src.ml.model import SalesModel

_engine = SalesModel()
MODEL_VERSION = "catboost_v1.0"


def train_model(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    return _engine.train(df)


def predict_sales_and_oos(raw_rows: list) -> pd.DataFrame:
    if not raw_rows:
        return pd.DataFrame()

    df = pd.DataFrame([row._asdict() for row in raw_rows])
    df = df.rename(columns={
        'price_sale': 'price',
        'quantity': 'stock_left',
        'price_rank': 'price_rank_in_category',
        'rating_rank': 'rating_rank_in_category'
    })

    for col in _engine.features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['predicted_sales'] = _engine.predict(df)

    df['days_to_oos'] = df.apply(
        lambda x: min(float(x['stock_left'] / x['predicted_sales']), 999.0)
        if x['predicted_sales'] > 0 else 999.0,
        axis=1
    )
    return df