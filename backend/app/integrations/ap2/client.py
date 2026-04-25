from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AP2OrderSubmission:
    purchase_order_id: int
    supplier_name: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class AP2Confirmation:
    external_reference: str
    status: str


class AP2Client(Protocol):
    def submit_order(self, submission: AP2OrderSubmission) -> AP2Confirmation:
        raise NotImplementedError


class MockAP2Client:
    def submit_order(self, submission: AP2OrderSubmission) -> AP2Confirmation:
        # TODO: replace with real AP2 API calls once credentials and contract are available.
        return AP2Confirmation(
            external_reference=f"AP2-MOCK-{submission.purchase_order_id}",
            status="confirmed",
        )
