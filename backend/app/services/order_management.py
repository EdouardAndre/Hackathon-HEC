from __future__ import annotations

from fastapi import HTTPException

from app.integrations.ap2.client import AP2Client, AP2OrderSubmission, MockAP2Client
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.repositories.purchase_orders import PurchaseOrderRepository
from app.repositories.suppliers import SupplierRepository
from app.schemas.orders import PurchaseOrderCreate


class OrderManagementService:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
        purchase_order_repository: PurchaseOrderRepository,
        ap2_client: AP2Client | None = None,
    ) -> None:
        self.supplier_repository = supplier_repository
        self.purchase_order_repository = purchase_order_repository
        self.ap2_client = ap2_client or MockAP2Client()

    def create_draft_order(self, payload: PurchaseOrderCreate) -> PurchaseOrder:
        supplier = self.supplier_repository.get_by_id(payload.supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        if supplier.available_quantity < payload.quantity:
            raise HTTPException(
                status_code=400,
                detail="Supplier does not have enough available quantity.",
            )

        return self.purchase_order_repository.create(
            payload=payload,
            unit_price=float(supplier.current_unit_price),
        )

    def confirm_order(self, order_id: int) -> PurchaseOrder:
        order = self.purchase_order_repository.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found.")

        if order.status == PurchaseOrderStatus.CONFIRMED:
            return order

        supplier = self.supplier_repository.get_by_id(order.supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        confirmation = self.ap2_client.submit_order(
            AP2OrderSubmission(
                purchase_order_id=order.id,
                supplier_name=supplier.name,
                quantity=order.quantity,
                unit_price=float(order.unit_price),
            )
        )
        order.status = PurchaseOrderStatus.CONFIRMED
        order.ap2_reference = confirmation.external_reference
        return self.purchase_order_repository.save(order)
