from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import DBSession
from app.repositories.suppliers import SupplierRepository
from app.schemas.suppliers import SupplierCreate, SupplierRead

router = APIRouter()


@router.post("", response_model=SupplierRead, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = DBSession) -> SupplierRead:
    repository = SupplierRepository(db)
    supplier = repository.create(payload)
    return SupplierRead.model_validate(supplier)


@router.get("", response_model=list[SupplierRead])
def list_suppliers(db: Session = DBSession) -> list[SupplierRead]:
    repository = SupplierRepository(db)
    suppliers = repository.list_all()
    return [SupplierRead.model_validate(supplier) for supplier in suppliers]
