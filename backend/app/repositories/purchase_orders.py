from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.models.purchase_order import PurchaseOrder
from app.presentation.schemas.orders import PurchaseOrderCreate


class PurchaseOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: PurchaseOrderCreate, unit_price: float) -> PurchaseOrder:
        order = PurchaseOrder(
            supplier_id=payload.supplier_id,
            quantity=payload.quantity,
            unit_price=unit_price,
            expected_shortage_date=payload.expected_shortage_date,
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def get_by_id(self, order_id: int) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        return self.session.scalars(statement).first()

    def save(self, order: PurchaseOrder) -> PurchaseOrder:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order
