from dotenv import load_dotenv
load_dotenv()

import datetime
import json
import os
import secrets
import sys
import urllib.parse

import requests
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gemini_service
from services import audit, invoice_parser, matching, payment_draft, po_builder, swan_executor

# ── Backend constants ──────────────────────────────────────────────────────────
SWAN_AUTH_URL  = "https://oauth.swan.io/oauth2/auth"
SWAN_TOKEN_URL = "https://oauth.swan.io/oauth2/token"
CLIENT_ID      = os.getenv("SWAN_CLIENT_ID",     "")
CLIENT_SECRET  = os.getenv("SWAN_CLIENT_SECRET",  "")
REDIRECT_URI   = os.getenv("SWAN_REDIRECT_URI",   "http://localhost:8501/callback")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Anypay — AP Agent", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { display: none; }
.main .block-container { padding: 1.5rem 2rem 2rem; max-width: 1280px; }

.ap-card {
  background: #ffffff; border: 1px solid #e5e8ed;
  border-radius: 10px; padding: 1.2rem 1.4rem;
  margin-bottom: 0.9rem; box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.ap-card-header {
  font-size: 0.72rem; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: #6b7280; margin-bottom: .6rem;
}
.ap-card-title  { font-size: 1.08rem; font-weight: 700; color: #111827; margin-bottom: .25rem; }
.ap-card-sub    { font-size: 0.84rem; color: #6b7280; }

.big-amount      { font-size: 2.4rem; font-weight: 800; color: #111827; letter-spacing: -0.02em; line-height: 1.1; }
.amount-currency { font-size: 1rem;   font-weight: 600; color: #6b7280; margin-left: 4px; }

.chip { display:inline-block; padding:3px 12px; border-radius:20px; font-size:0.73rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.chip-green  { background:#d1fae5; color:#065f46; }
.chip-orange { background:#ffedd5; color:#9a3412; }
.chip-red    { background:#fee2e2; color:#991b1b; }
.chip-blue   { background:#dbeafe; color:#1e40af; }
.chip-teal   { background:#ccfbf1; color:#134e4a; }
.chip-grey   { background:#f3f4f6; color:#374151; }
.chip-purple { background:#ede9fe; color:#5b21b6; }

.t-row   { display:flex; align-items:flex-start; gap:.75rem; padding:.35rem 0; }
.t-dot   { width:22px; height:22px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:.7rem; font-weight:800; margin-top:1px; }
.t-dot-done   { background:#d1fae5; color:#065f46; border:2px solid #10b981; }
.t-dot-active { background:#dbeafe; color:#1e40af; border:2px solid #3b82f6; }
.t-dot-warn   { background:#ffedd5; color:#9a3412; border:2px solid #f97316; }
.t-dot-err    { background:#fee2e2; color:#991b1b; border:2px solid #ef4444; }
.t-dot-idle   { background:#f3f4f6; color:#9ca3af; border:2px solid #d1d5db; }
.t-label { font-size:.83rem; color:#374151; font-weight:500; line-height:1.3; }
.t-ts    { font-size:.72rem; color:#9ca3af; }

.sec-divider { border:none; border-top:1px solid #e5e8ed; margin:1rem 0 .8rem; }

.sup-row    { display:flex; align-items:center; gap:.7rem; margin:.3rem 0; }
.sup-avatar { width:36px; height:36px; border-radius:8px; background:#dbeafe; color:#1e40af; display:flex; align-items:center; justify-content:center; font-size:1rem; font-weight:700; flex-shrink:0; }

.ai-row { display:flex; align-items:baseline; gap:.5rem; margin:.2rem 0; font-size:.84rem; }
.ai-key { color:#6b7280; min-width:110px; }
.ai-val { color:#111827; font-weight:500; }

.conf-track { height:6px; border-radius:3px; background:#e5e8ed; margin:.3rem 0 .6rem; }
.conf-fill  { height:100%; border-radius:3px; }

.page-headline { font-size:1.35rem; font-weight:800; color:#111827; letter-spacing:-0.01em; margin-bottom:.1rem; }
.page-sub      { font-size:.84rem;  color:#6b7280; margin-bottom:1rem; }

@keyframes t-row-in {
  from { opacity:0; transform:translateX(-10px); }
  to   { opacity:1; transform:translateX(0); }
}
@keyframes dot-pop {
  0%   { transform:scale(0.4); opacity:0.2; }
  65%  { transform:scale(1.25); }
  100% { transform:scale(1);   opacity:1; }
}
@keyframes dot-pulse {
  0%,100% { box-shadow:0 0 0 0 rgba(59,130,246,0.45); }
  50%     { box-shadow:0 0 0 7px rgba(59,130,246,0); }
}
@keyframes dot-warn-pulse {
  0%,100% { box-shadow:0 0 0 0 rgba(249,115,22,0.45); }
  50%     { box-shadow:0 0 0 7px rgba(249,115,22,0); }
}

.t-row      { animation: t-row-in 0.32s ease both; }
.t-dot-done { animation: dot-pop 0.38s cubic-bezier(.34,1.56,.64,1) both; }
.t-dot-active { animation: dot-pulse 1.5s ease-in-out infinite; }
.t-dot-warn   { animation: dot-warn-pulse 1.5s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
_env_token = os.getenv("SWAN_USER_ACCESS_TOKEN", "").strip()
_DEFAULTS: dict = {
    "user_access_token": _env_token,
    "token_source":      "env" if _env_token else None,
    "token_data":        {},
    "auth_url":          "",
    "oauth_state_sent":  "",
    "app_state":         "idle",
    "raw_request":       None,
    "normalized":        None,
    "gemini_mode_norm":  None,
    "po":                None,
    "invoice_scenario":  "exact_match",
    "mock_invoice":      None,
    "structured_invoice": None,
    "gemini_mode_inv":   None,
    "matching_result":   None,
    "ai_recommendation": None,
    "gemini_mode_rec":   None,
    "payment_draft":     None,
    "review_comment":    "",
    "execution_result":  None,
    "audit_trail":       [],
    "timeline":          {},
    "gemini_health":     None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Startup diagnostics to terminal ───────────────────────────────────────────
import sys as _sys
print("\n── Anypay AP Agent startup ──", file=_sys.stderr)
print(f"  SWAN_USER_ACCESS_TOKEN : {'SET' if _env_token else 'MISSING'}", file=_sys.stderr)
print(f"  SWAN_CLIENT_ID         : {'SET' if os.getenv('SWAN_CLIENT_ID') else 'MISSING'}", file=_sys.stderr)
print(f"  GOOGLE_CLOUD_PROJECT   : {os.getenv('GOOGLE_CLOUD_PROJECT','MISSING')}", file=_sys.stderr)
print(f"  GEMINI_API_KEY         : {'SET' if os.getenv('GEMINI_API_KEY') else 'MISSING'}", file=_sys.stderr)
print("──────────────────────────────\n", file=_sys.stderr)

# Capture OAuth callback signal — used below to auto-resume Confirm payment.
_just_got_token = st.session_state.pop("_just_got_token", False)
_oauth_err      = st.session_state.pop("oauth_error", None)
_oauth_exch_err = st.session_state.pop("oauth_exchange_error", None)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _exec_mode() -> str:
    return "SWAN_SANDBOX" if st.session_state["user_access_token"] else "MOCK"

def _chip(label: str, kind: str = "grey") -> str:
    return f'<span class="chip chip-{kind}">{label}</span>'

def _ts_fmt(iso: str) -> str:
    try:
        return datetime.datetime.fromisoformat(iso.rstrip("Z")).strftime("%H:%M:%S")
    except Exception:
        return iso or ""

def _load_mock_request() -> dict:
    path = os.path.join(os.path.dirname(__file__), "data", "mock_request.json")
    with open(path) as f:
        return json.load(f)

def _query_value(key: str) -> str:
    value = st.query_params.get(key, "")
    if isinstance(value, list):
        return value[0] if value else ""
    return str(value)


def _load_request_from_query() -> dict | None:
    item_name      = _query_value("item").strip()
    sku            = _query_value("sku").strip()
    supplier_name  = _query_value("supplier").strip()
    quantity_raw   = _query_value("quantity").strip()
    unit_price_raw = _query_value("unitPrice").strip()

    if not item_name or not sku or not supplier_name or not quantity_raw or not unit_price_raw:
        return None

    base = _load_mock_request()
    try:
        quantity   = float(quantity_raw)
        unit_price = float(unit_price_raw)
    except ValueError:
        return None

    base.update({
        "request_id":      f"REQ-{sku}",
        "part_reference":  sku,
        "description":     item_name,
        "quantity":        quantity,
        "unit_price_eur":  unit_price,
        "supplier_name":   supplier_name,
    })
    return base


def _build_invoice_from_request(request_payload: dict, scenario: str) -> dict:
    base_invoice = invoice_parser.get_mock_invoice(scenario)
    quantity   = float(request_payload.get("quantity", 0))
    unit_price = float(request_payload.get("unit_price_eur", 0))
    total      = round(quantity * unit_price, 2)

    base_invoice["supplier_name"]  = request_payload.get("supplier_name",  base_invoice.get("supplier_name", ""))
    base_invoice["supplier_id"]    = request_payload.get("supplier_id",    base_invoice.get("supplier_id", ""))
    base_invoice["supplier_iban"]  = request_payload.get("supplier_iban",  base_invoice.get("supplier_iban", ""))
    base_invoice["payment_terms"]  = request_payload.get("payment_terms",  base_invoice.get("payment_terms", "NET30"))
    base_invoice["currency"]       = request_payload.get("currency",       base_invoice.get("currency", "EUR"))
    base_invoice["line_items"][0]["part_reference"] = request_payload.get("part_reference", base_invoice["line_items"][0].get("part_reference", ""))
    base_invoice["line_items"][0]["description"]    = request_payload.get("description",    base_invoice["line_items"][0].get("description", ""))
    base_invoice["line_items"][0]["quantity"]        = quantity
    base_invoice["line_items"][0]["unit_price_eur"]  = unit_price
    base_invoice["line_items"][0]["total_eur"]       = total
    base_invoice["total_eur"] = total
    return base_invoice


def _reset():
    for k, v in _DEFAULTS.items():
        if k not in ("user_access_token", "token_source", "token_data", "auth_url", "oauth_state_sent"):
            st.session_state[k] = v

def _build_swan_oauth_url() -> str:
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state_sent"] = state
    return SWAN_AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         "openid offline",
        "state":         state,
    })

def _start_oauth_redirect():
    st.session_state["pending_oauth_url"] = _build_swan_oauth_url()
    st.session_state["app_state"] = "oauth_redirect"

def _is_auth_error(result: dict) -> bool:
    if (result.get("status") or "") == "TOKEN_MISSING":
        return True
    err = (result.get("error") or "").lower()
    return any(s in err for s in (
        "http 401", "http 403", "unauthorized",
        "invalid_grant", "invalid_token", "token expired",
        "token is missing", "token has expired",
    ))

def _do_execute_payment(comment: str = ""):
    trail    = st.session_state["audit_trail"]
    pd_data  = st.session_state["payment_draft"]
    now_iso  = datetime.datetime.utcnow().isoformat() + "Z"
    tok      = (st.session_state.get("user_access_token") or "").strip()

    trail = audit.log_event(trail, "human_approved", {
        "comment": comment, "draft_id": pd_data["payment_draft_id"],
        "execution_mode": "SWAN_SANDBOX",
    })
    st.session_state["review_comment"] = comment
    st.session_state["audit_trail"]    = trail

    # No active user token → kick off Swan OAuth, resume after callback.
    if not tok:
        st.session_state["resume_payment_after_oauth"] = True
        _start_oauth_redirect()
        return

    trail = audit.log_event(trail, "payment_execution_started", {"draft_id": pd_data["payment_draft_id"]})
    # Real backend call — initiates the actual transfer and triggers SCA / SMS verification.
    result = swan_executor.execute_payment(pd_data, user_token=tok)
    st.session_state["execution_result"] = result

    # Token rejected / expired / unauthorized → drop it and force fresh OAuth.
    if _is_auth_error(result):
        st.session_state["user_access_token"] = ""
        st.session_state["token_source"]      = None
        st.session_state["resume_payment_after_oauth"] = True
        st.session_state["audit_trail"] = trail
        _start_oauth_redirect()
        return

    tl_now      = st.session_state["timeline"]
    consent_url = result.get("consent_url")
    ts          = result.get("executed_at", now_iso)

    if consent_url:
        # Verification step required: route the browser to the verification page.
        # On return through /callback the app_state flips to payment_submitted.
        pd_data["status"] = "CONSENT_PENDING"
        tl_now["payment_consent_pending"] = ts
        trail = audit.log_event(trail, "payment_consent_pending",
                                {"payment_id": result.get("payment_id")})
        st.session_state["pending_consent_url"] = consent_url
        st.session_state["app_state"] = "consent_pending"
    else:
        # No verification redirect. Product UI must always resolve to "Payment sent";
        # technical success/failure detail is preserved in execution_result + audit_trail.
        if result.get("success"):
            pd_data["status"] = "EXECUTED"
            trail = audit.log_event(trail, "payment_execution_completed",
                                    {"payment_id": result.get("payment_id")})
        else:
            pd_data["status"] = "EXECUTION_FAILED"
            trail = audit.log_event(trail, "payment_execution_failed",
                                    {"error": result.get("error")})
        tl_now["payment_execution_completed"] = ts
        st.session_state["app_state"] = "payment_submitted"
    st.session_state["timeline"]    = tl_now
    st.session_state["audit_trail"] = trail

# ── Dialogs ────────────────────────────────────────────────────────────────────

@st.dialog("Invoice", width="large")
def _show_invoice():
    inv = st.session_state.get("mock_invoice") or {}
    si  = st.session_state.get("structured_invoice") or {}
    st.markdown(f"""
<div style="font-family:monospace;font-size:.82rem;padding:1rem;background:#f9fafb;border-radius:8px;border:1px solid #e5e8ed">
<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:.8rem">
  INVOICE — {si.get('invoice_reference') or inv.get('invoice_reference','—')}
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-bottom:.8rem">
  <div><span style="color:#6b7280">Date:</span> {si.get('invoice_date') or inv.get('invoice_date','—')}</div>
  <div><span style="color:#6b7280">PO Ref:</span> {si.get('po_reference') or inv.get('po_reference','—')}</div>
  <div><span style="color:#6b7280">Supplier:</span> {si.get('supplier_name') or inv.get('supplier_name','—')}</div>
  <div><span style="color:#6b7280">IBAN:</span> {si.get('supplier_iban') or inv.get('supplier_iban','—')}</div>
</div>
<hr style="border:none;border-top:1px solid #e5e8ed;margin:.6rem 0"/>
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr;gap:.3rem;font-weight:700;color:#374151;margin-bottom:.3rem">
  <span>Description</span><span>Qty</span><span>Unit price</span><span>Total</span>
</div>
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr;gap:.3rem;color:#111827">
  <span>{si.get('description','—')}</span>
  <span>{si.get('quantity','—')}</span>
  <span>{si.get('unit_price_eur','—')} €</span>
  <span><strong>{si.get('total_eur','—')} €</strong></span>
</div>
<hr style="border:none;border-top:1px solid #e5e8ed;margin:.6rem 0"/>
<div style="text-align:right;font-size:.9rem">
  <strong>TOTAL: {si.get('total_eur','—')} {si.get('currency','EUR')}</strong>
</div>
<div style="margin-top:.6rem;color:#6b7280">Payment terms: {si.get('payment_terms','—')}</div>
</div>
""", unsafe_allow_html=True)
    scenario = inv.get("scenario", "")
    if scenario and scenario != "exact_match":
        st.warning(f"Scenario: **{scenario.replace('_', ' ')}**", icon="⚠️")
    if st.button("Close", type="secondary", use_container_width=True):
        st.rerun()


@st.dialog("Purchase Order", width="large")
def _show_po():
    po   = st.session_state.get("po") or {}
    norm = st.session_state.get("normalized") or {}
    st.markdown(f"""
<div style="font-family:monospace;font-size:.82rem;padding:1rem;background:#f9fafb;border-radius:8px;border:1px solid #e5e8ed">
<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:.8rem">
  PURCHASE ORDER — {po.get('po_reference','—')}
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-bottom:.8rem">
  <div><span style="color:#6b7280">Date:</span> {po.get('created_at','—')[:10] if po.get('created_at') else '—'}</div>
  <div><span style="color:#6b7280">Status:</span> {po.get('status','—')}</div>
  <div><span style="color:#6b7280">Supplier:</span> {po.get('supplier_name','—')}</div>
  <div><span style="color:#6b7280">IBAN:</span> {po.get('supplier_iban','—')}</div>
  <div><span style="color:#6b7280">Site:</span> {norm.get('site','—')}</div>
  <div><span style="color:#6b7280">Payment terms:</span> {po.get('payment_terms','—')}</div>
</div>
<hr style="border:none;border-top:1px solid #e5e8ed;margin:.6rem 0"/>
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr;gap:.3rem;font-weight:700;color:#374151;margin-bottom:.3rem">
  <span>Reference / Description</span><span>Qty</span><span>Unit price</span><span>Total</span>
</div>
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr;gap:.3rem;color:#111827">
  <span>{po.get('part_reference','—')} — {po.get('description','—')}</span>
  <span>{po.get('quantity','—')}</span>
  <span>{po.get('unit_price_eur','—')} €</span>
  <span><strong>{po.get('total_eur','—')} €</strong></span>
</div>
<hr style="border:none;border-top:1px solid #e5e8ed;margin:.6rem 0"/>
<div style="text-align:right;font-size:.9rem">
  <strong>TOTAL: {po.get('total_eur','—')} {po.get('currency','EUR')}</strong>
</div>
</div>
""", unsafe_allow_html=True)
    if st.button("Close", type="secondary", use_container_width=True):
        st.rerun()


@st.dialog("Email", width="large")
def _show_email():
    norm    = st.session_state.get("normalized") or {}
    po      = st.session_state.get("po") or {}
    si      = st.session_state.get("structured_invoice") or {}
    sup     = norm.get("supplier_name") or po.get("supplier_name", "—")
    inv_ref = si.get("invoice_reference") or po.get("po_reference", "—")
    amount  = si.get("total_eur") or po.get("total_eur", "—")
    currency = po.get("currency", "EUR")
    po_ref  = po.get("po_reference", "—")
    inv_date = si.get("invoice_date", "—")
    sup_domain = sup.lower().replace(" ", "-") if sup and sup != "—" else "supplier"
    st.markdown(f"""
<div style="font-family:sans-serif;font-size:.85rem;padding:1rem;background:#f9fafb;border-radius:8px;border:1px solid #e5e8ed">
  <div style="display:flex;justify-content:space-between;margin-bottom:.8rem;padding-bottom:.6rem;border-bottom:1px solid #e5e8ed">
    <div>
      <div style="font-weight:700;color:#111827;font-size:.95rem">Invoice {inv_ref} — {sup}</div>
      <div style="color:#6b7280;font-size:.8rem">From: accounts@{sup_domain}.com</div>
      <div style="color:#6b7280;font-size:.8rem">To: ap-team@anypay.io</div>
    </div>
    <div style="color:#9ca3af;font-size:.78rem">{inv_date}</div>
  </div>
  <div style="line-height:1.7;color:#374151">
    <p>Dear Anypay team,</p>
    <p>Please find attached invoice <strong>{inv_ref}</strong> for your purchase order <strong>{po_ref}</strong>.</p>
    <p>Amount due: <strong>{amount} {currency}</strong></p>
    <p>Please process payment per the agreed terms. Do not hesitate to reach out if you have any questions.</p>
    <p>Best regards,<br/><strong>Accounts Receivable</strong><br/>{sup}</p>
  </div>
  <div style="margin-top:.8rem;padding:.6rem;background:#fff;border:1px solid #e5e8ed;border-radius:6px;font-size:.8rem;color:#6b7280">
    📎 invoice_{inv_ref}.pdf
  </div>
</div>
""", unsafe_allow_html=True)
    if st.button("Close", type="secondary", use_container_width=True):
        st.rerun()


@st.dialog("Payment verification", width="large")
def _confirm_payment_dialog():
    pd_obj = st.session_state.get("payment_draft") or {}
    st.markdown("""
<div style="font-size:.85rem;color:#6b7280;margin-bottom:.8rem">
Review the payment details below before confirming.
</div>""", unsafe_allow_html=True)
    st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e8ed;border-radius:8px;padding:1rem;font-size:.85rem;margin-bottom:1rem">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem">
    <div><span style="color:#6b7280">Recipient:</span> <strong>{pd_obj.get('supplier_name','—')}</strong></div>
    <div><span style="color:#6b7280">Amount:</span> <strong>{pd_obj.get('amount','—')} {pd_obj.get('currency','EUR')}</strong></div>
    <div><span style="color:#6b7280">Reference:</span> {pd_obj.get('po_reference','—')}</div>
    <div><span style="color:#6b7280">Invoice:</span> {pd_obj.get('invoice_reference','—')}</div>
    <div style="grid-column:span 2"><span style="color:#6b7280">IBAN:</span>
      <code style="background:#f3f4f6;padding:1px 6px;border-radius:3px">{pd_obj.get('iban','—')}</code>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    comment = st.text_area("Note (optional)", key="confirm_comment", height=60)
    col1, col2 = st.columns(2)
    with col1:
        if _exec_mode() == "MOCK":
            if not st.session_state.get("oauth_state_sent"):
                st.session_state["oauth_state_sent"] = secrets.token_urlsafe(16)
            _auth_url = SWAN_AUTH_URL + "?" + urllib.parse.urlencode({
                "response_type": "code",
                "client_id":     CLIENT_ID,
                "redirect_uri":  REDIRECT_URI,
                "scope":         "openid offline",
                "state":         st.session_state["oauth_state_sent"],
            })
            st.link_button("🔐 Sign in with Swan to confirm payment", _auth_url,
                           use_container_width=True, type="primary")
        else:
            if st.button("Confirm payment", type="primary", use_container_width=True):
                _do_execute_payment(comment)
                st.rerun()
    with col2:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.rerun()

# ── Load request ───────────────────────────────────────────────────────────────
if st.session_state["raw_request"] is None:
    st.session_state["raw_request"] = _load_request_from_query() or _load_mock_request()
raw       = st.session_state["raw_request"]

# ── Resume Confirm payment after OAuth callback ───────────────────────────────
# Callback set _just_got_token + user_access_token. If the user had clicked
# Confirm payment before being redirected, retry the payment now.
if _just_got_token and st.session_state.pop("resume_payment_after_oauth", False):
    if st.session_state.get("payment_draft"):
        _do_execute_payment(st.session_state.get("review_comment", ""))

app_state = st.session_state["app_state"]

# ── Auto-redirect to Swan OAuth ───────────────────────────────────────────────
# Triggered by Confirm payment when the user token is missing or rejected by Swan.
if app_state == "oauth_redirect":
    _oauth_url = st.session_state.get("pending_oauth_url", "")
    if _oauth_url:
        components.html(
            f"""
            <script>
              var u = {json.dumps(_oauth_url)};
              try {{ window.top.location.href = u; }} catch(e) {{}}
              try {{ window.parent.location.href = u; }} catch(e) {{}}
              try {{ window.location.href = u; }} catch(e) {{}}
            </script>
            """,
            height=0,
        )
        st.markdown(
            '<div style="text-align:center;padding:2rem 1rem .8rem;color:#6b7280;font-size:.95rem">'
            'Continuing to verification…'
            '</div>',
            unsafe_allow_html=True,
        )
        _, _mid, _ = st.columns([1, 1, 1])
        with _mid:
            st.link_button("Continue →", _oauth_url, type="primary", use_container_width=True)
        st.stop()

# ── Auto-redirect to verification (real SCA / SMS step) ───────────────────────
# When the backend returns a verification URL, route the browser there immediately.
# On return via /callback, app_state becomes "payment_submitted" → screen shows
# "Payment sent". Runs before any UI render so no provider details ever appear.
if app_state == "consent_pending":
    _consent_url = st.session_state.get("pending_consent_url", "")
    if _consent_url:
        # Try every escape path; sandboxed iframe may block window.top.
        components.html(
            f"""
            <script>
              var u = {json.dumps(_consent_url)};
              try {{ window.top.location.href = u; }} catch(e) {{}}
              try {{ window.parent.location.href = u; }} catch(e) {{}}
              try {{ window.location.href = u; }} catch(e) {{}}
            </script>
            """,
            height=0,
        )
        # Visible fallback if browser blocks the auto-redirect.
        st.markdown(
            '<div style="text-align:center;padding:2rem 1rem .8rem;color:#6b7280;font-size:.95rem">'
            'Continuing to verification…'
            '</div>',
            unsafe_allow_html=True,
        )
        _, _mid, _ = st.columns([1, 1, 1])
        with _mid:
            st.link_button("Continue →", _consent_url, type="primary", use_container_width=True)
        st.stop()

# ── Page header ────────────────────────────────────────────────────────────────
hdr_l, hdr_r = st.columns([5, 2])
with hdr_l:
    st.markdown('<div class="page-headline">Anypay</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Procurement review &nbsp;·&nbsp; automated AP processing</div>',
                unsafe_allow_html=True)
with hdr_r:
    st.write("")
    if st.button("Reset", type="secondary", use_container_width=True):
        _reset()
        st.rerun()

st.markdown('<hr class="sec-divider"/>', unsafe_allow_html=True)

# ── OAuth callback errors ──────────────────────────────────────────────────────
if _oauth_err:
    st.error(f"Swan OAuth error: {_oauth_err}")
if _oauth_exch_err:
    _err_code = _oauth_exch_err.get("error", "")
    _err_desc = _oauth_exch_err.get("description", "") or _oauth_exch_err.get("detail", "")
    if _err_code == "invalid_grant":
        st.error("Swan OAuth — **invalid_grant**: the authorization code has already been used or has expired. "
                 "Please click **Approve payment** again to restart the sign-in flow.")
    elif _err_code == "invalid_client":
        st.error("Swan OAuth — **invalid_client**: check SWAN_CLIENT_ID / SWAN_CLIENT_SECRET in .env")
    else:
        st.error(f"Swan OAuth — token exchange error ({_oauth_exch_err.get('http_status','')}): "
                 f"{_err_code} — {_err_desc}")

# ── Pipeline trigger ───────────────────────────────────────────────────────────
if app_state == "idle":
    ctl_l, ctl_r = st.columns([3, 1])
    with ctl_l:
        scenario = st.selectbox(
            "Invoice scenario",
            ["exact_match", "price_mismatch", "qty_mismatch"],
            index=["exact_match", "price_mismatch", "qty_mismatch"].index(
                st.session_state["invoice_scenario"]
            ),
        )
        st.session_state["invoice_scenario"] = scenario
    with ctl_r:
        st.write("")
        process_clicked = st.button("Review case", type="primary", use_container_width=True)

    if process_clicked:
        trail = st.session_state["audit_trail"]
        tl    = st.session_state["timeline"]
        st.session_state["app_state"] = "preparing"

        with st.spinner("Analysing case…"):
            now = lambda: datetime.datetime.utcnow().isoformat() + "Z"

            tl["request_received"] = now()
            trail = audit.log_event(trail, "request_received", {"request_id": raw["request_id"]})

            norm, mode_norm = gemini_service.normalize_request(raw)
            tl["request_normalized"] = now()
            trail = audit.log_event(trail, "request_normalized", {"mode": mode_norm})
            st.session_state["normalized"]       = norm
            st.session_state["gemini_mode_norm"] = mode_norm

            tl["supplier_confirmed"] = now()
            trail = audit.log_event(trail, "supplier_confirmed", {"supplier_id": norm.get("supplier_id")})

            po = po_builder.build_po(norm)
            tl["po_draft_created"] = now()
            trail = audit.log_event(trail, "po_draft_created", {"po_reference": po["po_reference"]})
            st.session_state["po"] = po

            mock_inv = _build_invoice_from_request(raw, scenario)
            mock_inv["po_reference"] = po["po_reference"]
            tl["invoice_received"] = now()
            trail = audit.log_event(trail, "invoice_received", {"scenario": scenario})
            st.session_state["mock_invoice"] = mock_inv

            structured, mode_inv = invoice_parser.structure_invoice(mock_inv)
            tl["invoice_structured"] = now()
            trail = audit.log_event(trail, "invoice_structured", {"mode": mode_inv})
            st.session_state["structured_invoice"] = structured
            st.session_state["gemini_mode_inv"]    = mode_inv

            match_result = matching.run_matching(po, structured)
            tl["matching_completed"] = now()
            trail = audit.log_event(trail, "matching_completed", {"status": match_result["status"]})
            st.session_state["matching_result"] = match_result

            ai_rec, mode_rec = gemini_service.analyze_prepayment(norm, po, structured, match_result)
            tl["ai_recommendation_created"] = now()
            trail = audit.log_event(trail, "ai_recommendation_created", {
                "mode": mode_rec, "action": ai_rec.get("recommended_action"),
            })
            st.session_state["ai_recommendation"] = ai_rec
            st.session_state["gemini_mode_rec"]   = mode_rec

            ai_blocks   = ai_rec.get("recommended_action") == "block"
            match_fails = match_result["status"] == "MATCH_FAILED"

            if not match_fails and not ai_blocks:
                pd_obj = payment_draft.build_payment_draft(po, structured, match_result)
                tl["payment_draft_created"] = now()
                trail = audit.log_event(trail, "payment_draft_created", {"id": pd_obj["payment_draft_id"]})
                st.session_state["payment_draft"] = pd_obj
            else:
                reason = "MATCH_FAILED" if match_fails else "AI_BLOCK"
                tl["payment_draft_skipped"] = now()
                trail = audit.log_event(trail, "payment_draft_skipped", {"reason": reason})
                st.session_state["payment_draft"] = None

            tl["waiting_human_review"] = now()
            trail = audit.log_event(trail, "waiting_human_review", {})

            st.session_state["audit_trail"] = trail
            st.session_state["timeline"]    = tl
            st.session_state["app_state"]   = "ready_for_review"

        st.rerun()
    st.stop()

# ── Two-column layout ─────────────────────────────────────────────────────────
col_left, col_right = st.columns([1.8, 1], gap="large")

norm      = st.session_state.get("normalized")         or {}
po        = st.session_state.get("po")                 or {}
si        = st.session_state.get("structured_invoice") or {}
mi        = st.session_state.get("mock_invoice")       or {}
mr        = st.session_state.get("matching_result")    or {}
ar        = st.session_state.get("ai_recommendation")  or {}
pd_obj    = st.session_state.get("payment_draft")
ex        = st.session_state.get("execution_result")
tl        = st.session_state.get("timeline")           or {}
app_state = st.session_state["app_state"]

match_status = mr.get("status", "")
ai_action    = ar.get("recommended_action", "hold_for_review")
has_draft    = pd_obj is not None
blocked      = match_status == "MATCH_FAILED" or ai_action == "block"

# ── LEFT COLUMN ────────────────────────────────────────────────────────────────
with col_left:

    # Case summary card
    state_chip_map = {
        "preparing":         ("Processing",     "blue"),
        "ready_for_review":  ("Pending review", "orange"),
        "consent_pending":   ("Payment sent",   "teal"),
        "payment_submitted": ("Payment sent",   "teal"),
        "rejected":          ("Rejected",       "red"),
    }
    s_label, s_kind = state_chip_map.get(app_state, ("—", "grey"))
    scenario_label  = mi.get("scenario", "exact_match").replace("_", " ").title()

    st.markdown(f"""
<div class="ap-card">
  <div class="ap-card-header">Case summary</div>
  <div style="display:flex;align-items:center;gap:.8rem;flex-wrap:wrap">
    <div class="ap-card-title">{raw.get('part_reference','—')}</div>
    {_chip(s_label, s_kind)}
    {_chip(scenario_label, 'blue')}
  </div>
  <div class="ap-card-sub">{raw.get('description','')}</div>
  <div style="margin-top:.5rem;font-size:.82rem;color:#6b7280">
    Request: <strong>{raw.get('request_id','—')}</strong> &nbsp;·&nbsp;
    PO: <strong>{po.get('po_reference','—')}</strong> &nbsp;·&nbsp;
    Site: <strong>{norm.get('site','—')}</strong>
  </div>
</div>
""", unsafe_allow_html=True)

    # Supplier card
    sup_name      = norm.get("supplier_name") or raw.get("supplier_name", "—")
    sup_iban      = norm.get("supplier_iban") or raw.get("supplier_iban", "—")
    sup_id        = norm.get("supplier_id", "—")
    avatar_letter = sup_name[0].upper() if sup_name else "?"

    st.markdown(f"""
<div class="ap-card">
  <div class="ap-card-header">Supplier</div>
  <div class="sup-row">
    <div class="sup-avatar">{avatar_letter}</div>
    <div>
      <div style="font-weight:700;color:#111827">{sup_name}</div>
      <div style="font-size:.8rem;color:#6b7280">ID: {sup_id}</div>
    </div>
  </div>
  <div style="font-size:.8rem;color:#6b7280;margin-top:.3rem">
    IBAN: <code style="background:#f3f4f6;padding:1px 5px;border-radius:4px">{sup_iban}</code>
  </div>
</div>
""", unsafe_allow_html=True)

    # Amount card
    amount_val  = po.get("total_eur") or 0
    currency    = po.get("currency", "EUR")
    qty         = norm.get("quantity", "—")
    unit_p      = norm.get("unit_price_eur", "—")
    terms       = po.get("payment_terms", "—")
    match_color = {"MATCH_OK": "green", "MATCH_WITH_WARNING": "orange", "MATCH_FAILED": "red"}.get(match_status, "grey")
    match_label = {
        "MATCH_OK":           "Verified",
        "MATCH_WITH_WARNING": "Verified with warnings",
        "MATCH_FAILED":       "Verification failed",
    }.get(match_status, match_status or "Pending")

    st.markdown(f"""
<div class="ap-card">
  <div class="ap-card-header">Amount</div>
  <div style="display:flex;align-items:baseline;gap:.2rem;margin-bottom:.4rem">
    <span class="big-amount">{amount_val:,.2f}</span>
    <span class="amount-currency">{currency}</span>
  </div>
  <div style="font-size:.82rem;color:#6b7280;margin-bottom:.5rem">
    {qty} × {unit_p} € &nbsp;·&nbsp; Terms: {terms}
  </div>
  {_chip(match_label, match_color)}
  {"".join(f'<div style="font-size:.8rem;color:#b91c1c;margin-top:.3rem">⚠ {iss}</div>' for iss in mr.get('blocking_issues',[]))}
  {"".join(f'<div style="font-size:.8rem;color:#d97706;margin-top:.2rem">! {w}</div>' for w in mr.get('warnings',[]))}
</div>
""", unsafe_allow_html=True)

    # Documents card
    st.markdown('<div class="ap-card"><div class="ap-card-header">Documents</div>', unsafe_allow_html=True)
    doc_c1, doc_c2, doc_c3 = st.columns(3)
    with doc_c1:
        if st.button("View invoice", use_container_width=True):
            _show_invoice()
    with doc_c2:
        if st.button("View purchase order", use_container_width=True):
            _show_po()
    with doc_c3:
        if st.button("View email", use_container_width=True):
            _show_email()
    st.markdown('</div>', unsafe_allow_html=True)

    # AI analysis card
    if ar:
        conf     = float(ar.get("confidence", 0.5))
        conf_pct = int(conf * 100)
        action_chip = {
            "proceed_with_payment": ("Proceed",         "green"),
            "hold_for_review":      ("Hold for review", "orange"),
            "block":                ("Block",           "red"),
        }.get(ai_action, ("—", "grey"))
        gemini_mode = st.session_state.get("gemini_mode_rec")
        ai_chip     = _chip("Gemini AI", "blue") if gemini_mode in ("gemini_api", "vertex_ai") else _chip("AI analysis", "grey")
        conf_color  = "#10b981" if conf >= 0.8 else ("#f97316" if conf >= 0.5 else "#ef4444")

        st.markdown(f"""
<div class="ap-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
    <div class="ap-card-header" style="margin-bottom:0">AI analysis</div>
    <div style="display:flex;gap:.4rem">{_chip(*action_chip)} {ai_chip}</div>
  </div>
  <div class="ai-row"><span class="ai-key">Summary</span><span class="ai-val">{ar.get('summary','—')}</span></div>
  <div class="ai-row"><span class="ai-key">Rationale</span><span class="ai-val">{ar.get('prepayment_rationale','—')}</span></div>
  <div style="margin:.4rem 0 .15rem;font-size:.75rem;color:#6b7280">Confidence: {conf_pct}%</div>
  <div class="conf-track"><div class="conf-fill" style="width:{conf_pct}%;background:{conf_color}"></div></div>
  {"".join(f'<div style="font-size:.8rem;color:#d97706;margin-top:.2rem">⚠ {rf}</div>' for rf in ar.get('risk_flags',[]))}
  {"".join(f'<div style="font-size:.8rem;color:#b91c1c;margin-top:.2rem">⛔ {a}</div>' for a in ar.get('anomalies_detected',[]))}
  {f'<div style="font-size:.8rem;color:#1d4ed8;margin-top:.3rem;background:#eff6ff;padding:4px 8px;border-radius:5px">ℹ {ar.get("human_review_note")}</div>' if ar.get("human_review_note") else ''}
</div>
""", unsafe_allow_html=True)

    # Payment approval card
    if app_state == "ready_for_review":
        st.markdown('<div class="ap-card"><div class="ap-card-header">Payment approval</div>',
                    unsafe_allow_html=True)
        if blocked:
            reason = "Verification failed" if match_status == "MATCH_FAILED" else "Blocked by AI analysis"
            st.error(f"Case blocked — {reason}. Payment cannot proceed.")
        elif has_draft:
            st.write("")
            btn_l, btn_r = st.columns(2)
            with btn_l:
                if st.button("Approve payment", type="primary", use_container_width=True):
                    _confirm_payment_dialog()
            with btn_r:
                if st.button("Reject", type="secondary", use_container_width=True):
                    pd_data = st.session_state["payment_draft"]
                    pd_data["status"] = "REJECTED_BY_USER"
                    st.session_state["audit_trail"] = audit.log_event(
                        st.session_state["audit_trail"], "human_rejected",
                        {"draft_id": pd_data["payment_draft_id"]},
                    )
                    tl_now = st.session_state["timeline"]
                    tl_now["rejected"] = datetime.datetime.utcnow().isoformat() + "Z"
                    st.session_state["timeline"] = tl_now
                    st.session_state["app_state"] = "rejected"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif app_state in ("payment_submitted", "consent_pending"):
        if ex and ex.get("success"):
            st.success(f"Payment sent — ID: `{ex.get('payment_id')}`")
        else:
            st.success("Payment sent.")

    elif app_state == "rejected":
        st.error("Case rejected.")

# ── RIGHT COLUMN — Agent journey ──────────────────────────────────────────────
with col_right:
    st.markdown('<div class="ap-card"><div class="ap-card-header">Agent journey</div>',
                unsafe_allow_html=True)

    # Longer stagger when all steps are already computed (fake replay animation).
    _replay = app_state not in ("idle", "preparing")
    _step_delay = 0.45 if _replay else 0.06

    def _t_row(label: str, ts: str | None, style: str = "idle", idx: int = 0):
        dot_class = {
            "done":   "t-dot-done",
            "active": "t-dot-active",
            "warn":   "t-dot-warn",
            "err":    "t-dot-err",
            "idle":   "t-dot-idle",
        }.get(style, "t-dot-idle")
        icons = {"done": "✓", "active": "…", "warn": "!", "err": "✗", "idle": "·"}
        icon    = icons.get(style, "·")
        ts_html = f'<div class="t-ts">{_ts_fmt(ts)}</div>' if ts else ""
        delay   = f"{idx * _step_delay:.2f}s"
        st.markdown(f"""<div class="t-row" style="animation-delay:{delay}">
  <div class="t-dot {dot_class}" style="animation-delay:{delay}">{icon}</div>
  <div><div class="t-label">{label}</div>{ts_html}</div>
</div>""", unsafe_allow_html=True)

    _t_row("Invoice received",      tl.get("invoice_received"),          "done" if tl.get("invoice_received") else "idle", 0)

    ms = mr.get("status", "")
    match_style = {"MATCH_OK": "done", "MATCH_WITH_WARNING": "warn", "MATCH_FAILED": "err"}.get(ms, "idle")
    _t_row("Automatic verification", tl.get("matching_completed"),        match_style, 1)

    _t_row("Purchase order matched", tl.get("po_draft_created"),          "done" if tl.get("po_draft_created") else "idle", 2)

    ai_style = {"proceed_with_payment": "done", "hold_for_review": "warn", "block": "err"}.get(ai_action, "idle") if ar else "idle"
    _t_row("Email reviewed",         tl.get("ai_recommendation_created"), ai_style, 3)

    if tl.get("payment_draft_skipped"):
        _t_row("Payment ready",      tl.get("payment_draft_skipped"),     "err",  4)
    else:
        _t_row("Payment ready",      tl.get("payment_draft_created"),     "done" if tl.get("payment_draft_created") else "idle", 4)

    review_style = "active" if app_state == "ready_for_review" else (
        "done" if app_state not in ("preparing", "ready_for_review", "idle") else "idle"
    )
    _t_row("Pending review",         tl.get("waiting_human_review"),      review_style, 5)

    if tl.get("payment_consent_pending"):
        _t_row("Final confirmation", tl["payment_consent_pending"],       "done", 6)
    if tl.get("payment_execution_completed"):
        _t_row("Payment sent",       tl["payment_execution_completed"],   "done", 7)
    if tl.get("mock_approved"):
        _t_row("Payment sent",       tl["mock_approved"],                 "done", 7)
    if tl.get("rejected"):
        _t_row("Rejected",           tl["rejected"],                      "err",  6)

    st.markdown('</div>', unsafe_allow_html=True)

    # Activity log (collapsed)
    trail = st.session_state["audit_trail"]
    if trail:
        with st.expander(f"Activity log ({len(trail)} events)", expanded=False):
            for entry in reversed(trail):
                data_str = "  " + ", ".join(f"{k}={v}" for k, v in entry.get("data", {}).items())
                st.markdown(
                    f'<div style="font-family:monospace;font-size:.78rem;margin:1px 0;'
                    f'padding:2px 5px;border-left:2px solid #e5e8ed">'
                    f'<span style="color:#9ca3af">{_ts_fmt(entry["timestamp"])}</span> '
                    f'<strong style="color:#111827">{entry["event"]}</strong>'
                    f'<span style="color:#6b7280">{data_str}</span></div>',
                    unsafe_allow_html=True,
                )
