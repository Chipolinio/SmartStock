from datetime import date
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml.engine import SalesMLProvider
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate
from src.db.repositories.PredictedSalesTSRepositories import create_predict_sales_bulk
from src.db.repositories.ProductFeaturesDailyRepositories import (
    get_aggregated_features_data,
    get_all_features_for_train
)


class MLForecastService:
    def __init__(self, ml_provider: SalesMLProvider):
        self.ml_provider = ml_provider

    async def run_daily_forecast(self, session: AsyncSession, target_date: date):
        raw_data = await get_aggregated_features_data(session, target_date)
        if not raw_data:
            return

        df = self.ml_provider.predict_sales_and_oos(raw_data)

        await self._save_only_predictions(session, df, target_date)

        await session.commit()

    async def _save_only_predictions(self, session: AsyncSession, df: pd.DataFrame, target_date: date):
        predictions = [
            PredictedSalesTSCreate(
                product_id=row['product_id'],
                dt=target_date,
                predicted_sales=float(row['predicted_sales']),
                model_version=self.ml_provider.model_version
            ) for _, row in df.iterrows()
        ]
        if predictions:
            await create_predict_sales_bulk(predictions, session)

    async def run_model_training(self, session: AsyncSession):
        raw_history = await get_all_features_for_train(session)
        if not raw_history:
            return False

        df = pd.DataFrame([
            {
                'price': float(r.price),
                'discount_pct': float(r.discount_pct or 0),
                'rating': float(r.rating or 0),
                'feedbacks': r.feedbacks or 0,
                'stock_left': r.stock_left,
                'price_rank_in_category': r.price_rank_in_category,
                'target_sales': float(r.avg_sales_7d or 0)
            } for r in raw_history
        ])

        success = self.ml_provider.train_model(df)
        return success