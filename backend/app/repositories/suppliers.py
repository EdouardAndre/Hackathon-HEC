from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.schemas.suppliers import SupplierCreate


class SupplierRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SupplierCreate) -> Supplier:
        supplier = Supplier(**payload.model_dump())
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        return supplier

    def list_all(self) -> list[Supplier]:
        statement = select(Supplier).order_by(
            Supplier.reliability_score.desc(),
            Supplier.current_unit_price.asc(),
        )
        return list(self.session.scalars(statement).all())

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        statement = select(Supplier).where(Supplier.id == supplier_id)
        return self.session.scalars(statement).first()
