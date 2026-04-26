import datetime


def build_po(normalized: dict) -> dict:
    ts = datetime.datetime.utcnow()
    po_ref = f"PO-{ts.strftime('%Y%m%d%H%M%S')}"
    delivery = (ts + datetime.timedelta(days=30)).date().isoformat()

    qty = float(normalized.get("quantity", 0))
    unit = float(normalized.get("unit_price_eur", 0))
    total = round(qty * unit, 2)

    return {
        "po_reference": po_ref,
        "created_at": ts.isoformat() + "Z",
        "supplier_id": normalized.get("supplier_id", ""),
        "supplier_name": normalized.get("supplier_name", ""),
        "supplier_iban": normalized.get("supplier_iban", ""),
        "part_reference": normalized.get("part_reference", ""),
        "description": normalized.get("description", ""),
        "quantity": qty,
        "unit_price_eur": unit,
        "total_eur": total,
        "currency": normalized.get("currency", "EUR"),
        "site": normalized.get("site", ""),
        "requested_delivery_date": delivery,
        "payment_terms": normalized.get("payment_terms", "NET30"),
        "status": "DRAFT",
    }
