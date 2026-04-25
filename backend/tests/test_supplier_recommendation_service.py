from dataclasses import dataclass
from decimal import Decimal

from app.services.supplier_recommendation import rank_suppliers


@dataclass
class SupplierStub:
    id: int
    name: str
    lead_time_days: int
    available_quantity: int
    current_unit_price: Decimal
    reliability_score: float


def test_rank_suppliers_prioritizes_fulfillment_and_balance() -> None:
    suppliers = [
        SupplierStub(
            id=1,
            name="Budget Supplier",
            lead_time_days=6,
            available_quantity=300,
            current_unit_price=Decimal("10.00"),
            reliability_score=0.70,
        ),
        SupplierStub(
            id=2,
            name="Reliable Supplier",
            lead_time_days=4,
            available_quantity=500,
            current_unit_price=Decimal("11.50"),
            reliability_score=0.95,
        ),
        SupplierStub(
            id=3,
            name="Partial Supplier",
            lead_time_days=2,
            available_quantity=120,
            current_unit_price=Decimal("9.00"),
            reliability_score=0.99,
        ),
    ]

    ranked = rank_suppliers(suppliers=suppliers, required_quantity=250)

    assert ranked[0].supplier_name == "Reliable Supplier"
    assert ranked[1].supplier_name == "Budget Supplier"
    assert ranked[2].can_fulfill is False
