from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.models.inventory import InventorySnapshot
from app.presentation.schemas.inventory import InventorySnapshotCreate


class InventoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: InventorySnapshotCreate) -> InventorySnapshot:
        snapshot = InventorySnapshot(stock_level=payload.stock_level)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def get_latest(self) -> InventorySnapshot | None:
        statement = select(InventorySnapshot).order_by(InventorySnapshot.recorded_at.desc())
        return self.session.scalars(statement).first()
