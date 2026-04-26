"""
Gemini AI service — uses google.genai (new SDK, replaces deprecated google.generativeai).

Auth priority:
  1. GEMINI_API_KEY env var  → genai.Client(api_key=...)
  2. Vertex AI + ADC         → genai.Client(vertexai=True, project=..., location=...)
     requires: GOOGLE_CLOUD_PROJECT + gcloud auth application-default login

If neither works, functions return (fallback_result, "fallback::<error>").
"""

from __future__ import annotations
import os
import json
import datetime

GEMINI_MODEL = "gemini-2.0-flash"

# Last error from _make_client or Gemini call — read by UI for diagnostics
_last_error: str = ""


def _make_client():
    """
    Build a google.genai Client.
    Returns (client, mode_str).
    Raises RuntimeError with actionable message on failure.
    """
    from google import genai  # google-genai >= 1.0

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key), "gemini_api"

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError(
            "No Gemini credentials found.\n"
            "Option A: set GEMINI_API_KEY in .env\n"
            "Option B: set GOOGLE_CLOUD_PROJECT + run:\n"
            "  /home/codespace/google-cloud-sdk/bin/gcloud auth application-default login"
        )

    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    try:
        import google.auth
        google.auth.default()  # will raise DefaultCredentialsError if ADC not set up
    except Exception as adc_err:
        raise RuntimeError(
            f"GOOGLE_CLOUD_PROJECT is set ({project}) but ADC is missing.\n"
            f"ADC error: {adc_err}\n"
            "Fix: run this command in your terminal, then restart the app:\n"
            "  /home/codespace/google-cloud-sdk/bin/gcloud auth application-default login"
        )

    return genai.Client(vertexai=True, project=project, location=location), "vertex_ai"


def health_check() -> tuple[str, str]:
    """
    Returns (status, detail).
    status: 'gemini_api' | 'vertex_ai' | 'fallback'
    detail: human-readable explanation.
    Makes a real tiny API call to verify connectivity.
    """
    global _last_error
    try:
        from google import genai
    except ImportError:
        _last_error = "google-genai not installed — run: pip install google-genai"
        return "fallback", _last_error

    try:
        client, mode = _make_client()
    except RuntimeError as e:
        _last_error = str(e)
        return "fallback", _last_error

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Reply with exactly one word: OK",
        )
        _last_error = ""
        return mode, f"Model reachable — response: {resp.text.strip()[:60]}"
    except Exception as e:
        _last_error = f"{type(e).__name__}: {e}"
        return "fallback", _last_error


def _call_gemini(prompt: str) -> tuple[dict | None, str]:
    """
    Core call. Returns (parsed_dict, mode) or (None, 'fallback::<reason>').
    """
    global _last_error
    try:
        from google import genai
        from google.genai import types
        client, mode = _make_client()
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        _last_error = ""
        return result, mode
    except Exception as e:
        _last_error = f"{type(e).__name__}: {e}"
        return None, f"fallback::{_last_error}"


def get_last_error() -> str:
    return _last_error


# ── Request normalization ──────────────────────────────────────────────────────

def _fallback_normalize(raw: dict) -> dict:
    issues = []
    if not raw.get("quantity") or float(raw.get("quantity", 0)) <= 0:
        issues.append("quantity must be > 0")
    if not raw.get("unit_price_eur") or float(raw.get("unit_price_eur", 0)) <= 0:
        issues.append("unit_price_eur must be > 0")
    if not raw.get("supplier_iban"):
        issues.append("supplier_iban is missing")
    qty   = float(raw.get("quantity", 0))
    price = float(raw.get("unit_price_eur", 0))
    return {
        "request_id":      raw.get("request_id", "UNKNOWN"),
        "part_reference":  raw.get("part_reference", ""),
        "description":     raw.get("description", ""),
        "quantity":        qty,
        "unit_price_eur":  price,
        "total_eur":       round(qty * price, 2),
        "supplier_id":     raw.get("supplier_id", ""),
        "supplier_name":   raw.get("supplier_name", ""),
        "supplier_iban":   raw.get("supplier_iban", ""),
        "site":            raw.get("site", ""),
        "payment_terms":   raw.get("payment_terms", "NET30"),
        "currency":        "EUR",
        "is_valid":        len(issues) == 0,
        "validation_issues": issues,
    }


def normalize_request(raw: dict) -> tuple[dict, str]:
    prompt = (
        "You are an AP normalization engine. Given this procurement request JSON, "
        "return a normalized structured version with these exact fields: "
        "request_id, part_reference, description, quantity (number), unit_price_eur (number), "
        "total_eur (quantity*unit_price_eur), supplier_id, supplier_name, supplier_iban, "
        "site, payment_terms, currency (always EUR), is_valid (bool), validation_issues (array of strings). "
        "Do NOT choose or change the supplier. "
        "Input:\n" + json.dumps(raw, indent=2)
    )
    result, mode = _call_gemini(prompt)
    if result is None:
        return _fallback_normalize(raw), mode
    # Ensure required booleans/arrays exist
    result.setdefault("is_valid", True)
    result.setdefault("validation_issues", [])
    return result, mode


# ── Invoice structuring ────────────────────────────────────────────────────────

def _fallback_structure_invoice(raw: dict) -> dict:
    item = raw.get("line_items", [{}])[0] if raw.get("line_items") else {}
    return {
        "invoice_reference": raw.get("invoice_reference", ""),
        "invoice_date":      raw.get("invoice_date", ""),
        "supplier_id":       raw.get("supplier_id", ""),
        "supplier_name":     raw.get("supplier_name", ""),
        "supplier_iban":     raw.get("supplier_iban", ""),
        "po_reference":      raw.get("po_reference") or "",
        "part_reference":    item.get("part_reference", ""),
        "description":       item.get("description", ""),
        "quantity":          float(item.get("quantity", 0)),
        "unit_price_eur":    float(item.get("unit_price_eur", 0)),
        "total_eur":         float(raw.get("total_eur", 0)),
        "currency":          raw.get("currency", "EUR"),
        "payment_terms":     raw.get("payment_terms", ""),
    }


def structure_invoice(raw: dict) -> tuple[dict, str]:
    prompt = (
        "You are an AP invoice parser. Given this raw invoice JSON, "
        "return a flat structured version with: invoice_reference, invoice_date, "
        "supplier_id, supplier_name, supplier_iban, po_reference, part_reference, "
        "description, quantity (number), unit_price_eur (number), total_eur (number), "
        "currency, payment_terms. Extract first line item. "
        "Input:\n" + json.dumps(raw, indent=2)
    )
    result, mode = _call_gemini(prompt)
    if result is None:
        return _fallback_structure_invoice(raw), mode
    return result, mode


# ── Prepayment AI recommendation ──────────────────────────────────────────────

_ACTION_MAP = {
    "MATCH_OK":           ("proceed_with_payment", 0.87),
    "MATCH_WITH_WARNING": ("hold_for_review",       0.60),
    "MATCH_FAILED":       ("block",                 0.95),
}


def _fallback_analyze_prepayment(norm: dict, po: dict, invoice: dict, match: dict) -> dict:
    status = match.get("status", "MATCH_FAILED")
    action, confidence = _ACTION_MAP.get(status, ("block", 0.50))
    issues   = match.get("blocking_issues", [])
    warnings = match.get("warnings", [])
    risk_flags = [f"Matching issue: {i}" for i in issues] + [f"Warning: {w}" for w in warnings]
    return {
        "summary": (
            f"PO {po.get('po_reference')} vs INV {invoice.get('invoice_reference')} — "
            f"matching result: {status}."
        ),
        "recommended_action":   action,
        "prepayment_rationale": (
            f"2-way match returned {status}. "
            + (f"Blocking issues: {'; '.join(issues)}." if issues else "No blocking issues.")
        ),
        "payment_justification": (
            f"Payment of {po.get('total_eur')} {po.get('currency','EUR')} "
            f"to {po.get('supplier_name')} for {po.get('part_reference')}."
        ),
        "risk_flags":        risk_flags,
        "confidence":        confidence,
        "anomalies_detected": list(issues),
        "human_review_note": (
            "Auto-approuvé par le moteur de règles." if action == "proceed_with_payment"
            else "Revue manuelle requise avant exécution."
        ),
    }


def analyze_prepayment(norm: dict, po: dict, invoice: dict, match: dict) -> tuple[dict, str]:
    prompt = (
        "You are an AP prepayment risk analyst. "
        "Analyze the procurement data and produce a structured prepayment recommendation. "
        "You must NOT choose or change the supplier. You must NOT trigger any payment. "
        "Return JSON with exactly: summary, recommended_action (one of: proceed_with_payment | hold_for_review | block), "
        "prepayment_rationale, payment_justification, risk_flags (array), confidence (0.0–1.0), "
        "anomalies_detected (array), human_review_note.\n"
        "NORMALIZED_REQUEST:\n" + json.dumps(norm, indent=2) + "\n"
        "PO_DRAFT:\n" + json.dumps(po, indent=2) + "\n"
        "STRUCTURED_INVOICE:\n" + json.dumps(invoice, indent=2) + "\n"
        "MATCHING_RESULT:\n" + json.dumps(match, indent=2)
    )
    result, mode = _call_gemini(prompt)
    if result is None:
        return _fallback_analyze_prepayment(norm, po, invoice, match), mode

    valid_actions = {"proceed_with_payment", "hold_for_review", "block"}
    if result.get("recommended_action") not in valid_actions:
        result["recommended_action"] = "hold_for_review"
    try:
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    except (TypeError, ValueError):
        result["confidence"] = 0.5

    return result, mode
