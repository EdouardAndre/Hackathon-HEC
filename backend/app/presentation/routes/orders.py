from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.presentation.deps import AP2ClientDep, DBSession
from app.services.integrations.ap2.client import AP2Client
from app.repositories.purchase_orders import PurchaseOrderRepository
from app.repositories.suppliers import SupplierRepository
from app.presentation.schemas.orders import PurchaseOrderCreate, PurchaseOrderRead
from app.services.order_management import OrderManagementService

router = APIRouter()


@router.post(
    "/drafts",
    response_model=PurchaseOrderRead,
    status_code=201,
    summary="Créer un bon de commande (brouillon)",
    description="Valide la disponibilité chez le fournisseur et crée la commande en statut DRAFT.",
)
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


@router.post(
    "/{order_id}/confirm",
    response_model=PurchaseOrderRead,
    summary="Confirmer une commande",
    description="Soumet la commande à l'API AP2 et passe le statut à CONFIRMED. Idempotent.",
)
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
