from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.presentation.deps import DBSession
from app.repositories.inventory import InventoryRepository
from app.presentation.schemas.inventory import InventorySnapshotCreate, InventorySnapshotRead

router = APIRouter()


@router.post("", response_model=InventorySnapshotRead, status_code=201)
def create_inventory_snapshot(
    payload: InventorySnapshotCreate,
    db: Session = DBSession,
) -> InventorySnapshotRead:
    repository = InventoryRepository(db)
    snapshot = repository.create(payload)
    return InventorySnapshotRead.model_validate(snapshot)


@router.get("/current", response_model=InventorySnapshotRead)
def get_current_inventory(db: Session = DBSession) -> InventorySnapshotRead:
    repository = InventoryRepository(db)
    snapshot = repository.get_latest()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No inventory snapshot found.")
    return InventorySnapshotRead.model_validate(snapshot)
