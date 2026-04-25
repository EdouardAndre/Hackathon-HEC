from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import AP2ClientDep, DBSession
from app.integrations.ap2.client import AP2Client
from app.repositories.purchase_orders import PurchaseOrderRepository
from app.repositories.suppliers import SupplierRepository
from app.schemas.orders import PurchaseOrderCreate, PurchaseOrderRead
from app.services.order_management import OrderManagementService

router = APIRouter()


@router.post("/drafts", response_model=PurchaseOrderRead, status_code=201)
def create_draft_order(
    payload: PurchaseOrderCreate,
    db: Session = DBSession,
) -> PurchaseOrderRead:
    service = OrderManagementService(
        supplier_repository=SupplierRepository(db),
        purchase_order_repository=PurchaseOrderRepository(db),
    )
    order = service.create_draft_order(payload)
    return PurchaseOrderRead.model_validate(order)


@router.post("/{order_id}/confirm", response_model=PurchaseOrderRead)
def confirm_order(
    order_id: int,
    db: Session = DBSession,
    ap2_client: AP2Client = AP2ClientDep,
) -> PurchaseOrderRead:
    service = OrderManagementService(
        supplier_repository=SupplierRepository(db),
        purchase_order_repository=PurchaseOrderRepository(db),
        ap2_client=ap2_client,
    )
    order = service.confirm_order(order_id)
    return PurchaseOrderRead.model_validate(order)


@router.get("/{order_id}", response_model=PurchaseOrderRead)
def get_order(order_id: int, db: Session = DBSession) -> PurchaseOrderRead:
    repository = PurchaseOrderRepository(db)
    order = repository.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    return PurchaseOrderRead.model_validate(order)
