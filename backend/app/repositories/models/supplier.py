from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(nullable=False)
    available_quantity: Mapped[int] = mapped_column(nullable=False)
    current_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reliability_score: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
