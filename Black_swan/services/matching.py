PRICE_TOLERANCE = 0.02  # 2%


def _pct_diff(a: float, b: float) -> float:
    if b == 0:
        return float("inf")
    return abs(a - b) / b


def run_matching(po: dict, invoice: dict) -> dict:
    issues = []
    warnings = []
    details = {}

    # Supplier consistency
    if po.get("supplier_id") != invoice.get("supplier_id"):
        issues.append(f"supplier_id mismatch: PO={po.get('supplier_id')} vs INV={invoice.get('supplier_id')}")
    details["supplier_id"] = {"po": po.get("supplier_id"), "inv": invoice.get("supplier_id")}

    # PO reference (invoice may not have it yet → warning only)
    inv_po_ref = invoice.get("po_reference") or ""
    if inv_po_ref and inv_po_ref != po.get("po_reference"):
        issues.append(f"po_reference mismatch: PO={po.get('po_reference')} vs INV={inv_po_ref}")
    elif not inv_po_ref:
        warnings.append("invoice does not reference a PO number")
    details["po_reference"] = {"po": po.get("po_reference"), "inv": inv_po_ref or "(not set)"}

    # Quantity
    po_qty = float(po.get("quantity", 0))
    inv_qty = float(invoice.get("quantity", 0))
    qty_diff = _pct_diff(inv_qty, po_qty)
    if qty_diff > PRICE_TOLERANCE:
        issues.append(f"quantity mismatch: PO={po_qty} vs INV={inv_qty} ({qty_diff*100:.1f}%)")
    details["quantity"] = {"po": po_qty, "inv": inv_qty, "diff_pct": round(qty_diff * 100, 2)}

    # Unit price
    po_price = float(po.get("unit_price_eur", 0))
    inv_price = float(invoice.get("unit_price_eur", 0))
    price_diff = _pct_diff(inv_price, po_price)
    if price_diff > PRICE_TOLERANCE:
        issues.append(f"unit_price mismatch: PO={po_price}€ vs INV={inv_price}€ ({price_diff*100:.1f}%)")
    elif price_diff > 0:
        warnings.append(f"minor unit_price variance: {price_diff*100:.2f}%")
    details["unit_price_eur"] = {"po": po_price, "inv": inv_price, "diff_pct": round(price_diff * 100, 2)}

    # Total amount
    po_total = float(po.get("total_eur", 0))
    inv_total = float(invoice.get("total_eur", 0))
    total_diff = _pct_diff(inv_total, po_total)
    if total_diff > PRICE_TOLERANCE:
        issues.append(f"total_eur mismatch: PO={po_total}€ vs INV={inv_total}€ ({total_diff*100:.1f}%)")
    details["total_eur"] = {"po": po_total, "inv": inv_total, "diff_pct": round(total_diff * 100, 2)}

    all_issues = issues + warnings
    if issues:
        status = "MATCH_FAILED"
    elif warnings:
        status = "MATCH_WITH_WARNING"
    else:
        status = "MATCH_OK"

    return {
        "status": status,
        "issues": all_issues,
        "blocking_issues": issues,
        "warnings": warnings,
        "details": details,
    }
