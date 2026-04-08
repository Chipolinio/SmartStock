from datetime import date, datetime
from sqlalchemy import BigInteger, Date, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


class AdRecommendation(Base):
    __tablename__ = "ad_recommendations"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    category: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Категория рекомендации: campaign, keyword, budget, strategy"
    )
    recommendation_text: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Текст рекомендации от LLM"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Приоритет: 1 = высокий, 2 = средний, 3 = низкий"
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Дополнительные данные (JSON) — бюджет, ключевые слова и т.д."
    )
