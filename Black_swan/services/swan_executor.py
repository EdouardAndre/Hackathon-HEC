import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import swan_pay_supplier as _sp


def execute_payment(draft: dict, user_token: str | None = None) -> dict:
    """
    Wraps swan_pay_supplier.initiate_supplier_payment().
    Never raises — returns {"success": False, "error": ...} on any failure.
    Monkey-patches USER_ACCESS_TOKEN at call time so the module-level read doesn't block us.
    """
    token = user_token or os.getenv("SWAN_USER_ACCESS_TOKEN")

    if not token:
        return {
            "success": False,
            "execution_mode": "SWAN_SANDBOX",
            "error": "SWAN_USER_ACCESS_TOKEN is missing",
            "guidance": (
                "To get a user access token: run `streamlit run swan_oauth_app.py`, "
                "complete the OAuth flow, then add the token to .env as SWAN_USER_ACCESS_TOKEN=<token>"
            ),
            "payment_id": None,
            "status": "TOKEN_MISSING",
            "consent_url": None,
            "transactions": [],
            "raw_response": {},
            "executed_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

    # Patch the module-level var so gql() and initiate_supplier_payment() use our token
    old_token = _sp.USER_ACCESS_TOKEN
    _sp.USER_ACCESS_TOKEN = token
    try:
        raw = _sp.initiate_supplier_payment(
            supplier_name=draft["supplier_name"],
            supplier_iban=draft["iban"],
            amount=f"{float(draft['amount']):.2f}",
            currency=draft.get("currency", "EUR"),
            label=draft.get("justification", f"AP payment {draft.get('po_reference', '')}"),
            idempotency_key=draft["payment_draft_id"],
        )
    except RuntimeError as exc:
        return {
            "success": False,
            "execution_mode": "SWAN_SANDBOX",
            "error": str(exc),
            "guidance": None,
            "payment_id": None,
            "status": "ERROR",
            "consent_url": None,
            "transactions": [],
            "raw_response": {},
            "executed_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:
        return {
            "success": False,
            "execution_mode": "SWAN_SANDBOX",
            "error": f"Unexpected error: {exc}",
            "guidance": None,
            "payment_id": None,
            "status": "ERROR",
            "consent_url": None,
            "transactions": [],
            "raw_response": {},
            "executed_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
    finally:
        _sp.USER_ACCESS_TOKEN = old_token

    return _parse_swan_response(raw)


def _parse_swan_response(raw: dict) -> dict:
    executed_at = datetime.datetime.utcnow().isoformat() + "Z"
    typename = raw.get("__typename", "")

    if typename == "InitiateCreditTransfersSuccessPayload":
        payment = raw.get("payment", {})
        status_info = payment.get("statusInfo", {})
        status = status_info.get("status", "Unknown")

        consent_url = None
        consent_obj = status_info.get("consent")
        if consent_obj:
            consent_url = consent_obj.get("consentUrl")

        transactions = []
        for edge in payment.get("transactions", {}).get("edges", []):
            node = edge.get("node", {})
            amt = node.get("amount", {})
            creditor = node.get("creditor", {})
            transactions.append({
                "id": node.get("id"),
                "amount": f"{amt.get('value')} {amt.get('currency')}",
                "label": node.get("label"),
                "status": node.get("statusInfo", {}).get("status"),
                "beneficiary_name": creditor.get("name"),
                "beneficiary_iban": creditor.get("IBAN"),
            })

        return {
            "success": True,
            "execution_mode": "SWAN_SANDBOX",
            "payment_id": payment.get("id"),
            "status": status,
            "consent_url": consent_url,
            "transactions": transactions,
            "error": None,
            "guidance": "Open the consent_url to complete SCA validation." if consent_url else None,
            "raw_response": raw,
            "executed_at": executed_at,
        }

    # Rejection or unknown
    return {
        "success": False,
        "execution_mode": "SWAN_SANDBOX",
        "payment_id": None,
        "status": "REJECTED",
        "consent_url": None,
        "transactions": [],
        "error": raw.get("message", f"Swan returned: {typename}"),
        "guidance": None,
        "raw_response": raw,
        "executed_at": executed_at,
    }
