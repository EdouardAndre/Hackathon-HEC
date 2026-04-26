import datetime


def build_payment_draft(po: dict, invoice: dict, matching: dict) -> dict | None:
    if matching.get("status") == "MATCH_FAILED":
        return None

    ts = datetime.datetime.utcnow()
    draft_id = f"PD-{ts.strftime('%Y%m%d%H%M%S')}"

    risk_flags = []
    if matching["status"] == "MATCH_WITH_WARNING":
        risk_flags = [f"WARNING: {w}" for w in matching.get("warnings", [])]

    return {
        "payment_draft_id": draft_id,
        "created_at": ts.isoformat() + "Z",
        "po_reference": po.get("po_reference", ""),
        "invoice_reference": invoice.get("invoice_reference", ""),
        "supplier_id": po.get("supplier_id", ""),
        "supplier_name": po.get("supplier_name", ""),
        "iban": po.get("supplier_iban", ""),
        "amount": float(invoice.get("total_eur", 0)),
        "currency": po.get("currency", "EUR"),
        "justification": (
            f"Payment for {po.get('part_reference')} — "
            f"PO {po.get('po_reference')} — "
            f"INV {invoice.get('invoice_reference')}"
        ),
        "matching_status": matching["status"],
        "matching_issues": matching.get("issues", []),
        "risk_flags": risk_flags,
        "status": "READY_FOR_APPROVAL",
    }
