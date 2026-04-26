from dotenv import load_dotenv
load_dotenv()

import os
import secrets
import uuid
import json
import urllib.parse
import requests
import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────
SWAN_AUTH_URL  = "https://oauth.swan.io/oauth2/auth"
SWAN_TOKEN_URL = "https://oauth.swan.io/oauth2/token"
SWAN_GQL_URL   = "https://api.swan.io/sandbox-partner/graphql"

# ── Env vars (read-only) ───────────────────────────────────────────────────────
CLIENT_ID             = os.getenv("SWAN_CLIENT_ID", "")
CLIENT_SECRET         = os.getenv("SWAN_CLIENT_SECRET", "")
REDIRECT_URI          = os.getenv("SWAN_REDIRECT_URI", "http://localhost:8501")
ACCOUNT_ID            = os.getenv("SWAN_ACCOUNT_ID", "")
ACCOUNT_MEMBERSHIP_ID = os.getenv("SWAN_ACCOUNT_MEMBERSHIP_ID", "")

# ── OAuth callback capture — runs on EVERY re-render ──────────────────────────
# When Swan redirects to http://localhost:8501?code=xxx&state=yyy, Streamlit
# exposes the params via st.query_params. We capture them once into session_state
# and immediately clear the URL so it doesn't trigger again on the next rerun.
_qp = st.query_params
if "code" in _qp and "oauth_code" not in st.session_state:
    st.session_state["oauth_code"]           = _qp["code"]
    st.session_state["oauth_state_received"] = _qp.get("state", "")
    st.query_params.clear()
elif "error" in _qp:
    st.session_state["oauth_error"] = _qp.get("error_description", _qp.get("error", "Unknown OAuth error"))
    st.query_params.clear()

# Pre-load SWAN_USER_ACCESS_TOKEN from .env if session is cold
if "user_access_token" not in st.session_state:
    _env_tok = os.getenv("SWAN_USER_ACCESS_TOKEN", "")
    if _env_tok:
        st.session_state["user_access_token"] = _env_tok
        st.session_state["token_source"] = "env"

# ── GraphQL helper ─────────────────────────────────────────────────────────────
def gql(query: str, variables: dict = None, token: str = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(
        SWAN_GQL_URL,
        headers=headers,
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    try:
        payload = r.json()
    except Exception:
        r.raise_for_status()
        raise
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}\n{json.dumps(payload, indent=2)}")
    if payload.get("errors"):
        raise RuntimeError("GraphQL errors:\n" + json.dumps(payload["errors"], indent=2))
    return payload["data"]


# ── GraphQL queries / mutations ────────────────────────────────────────────────
_USER_Q = """
{
  user {
    id
    fullName
    firstName
    lastName
    mobilePhoneNumber
    status
  }
}
"""

_MEMBERSHIP_Q = """
query GetMembership($id: ID!) {
  accountMembership(id: $id) {
    id
    statusInfo { status }
    user {
      id
      fullName
      firstName
      lastName
      mobilePhoneNumber
    }
    account {
      id
      name
      IBAN
      currency
      balances {
        available { value currency }
        booked    { value currency }
        pending   { value currency }
      }
    }
  }
}
"""

_PAYMENT_M = """
mutation InitiatePayment($input: InitiateCreditTransfersInput!) {
  initiateCreditTransfers(input: $input) {
    __typename
    ... on InitiateCreditTransfersSuccessPayload {
      payment {
        id
        statusInfo {
          status
          ... on PaymentConsentPending {
            consent {
              consentUrl
              status
            }
          }
        }
        transactions {
          edges {
            node {
              id
              amount { value currency }
              label
              statusInfo { status }
              creditor {
                ... on SEPACreditTransferOutCreditor {
                  name
                  IBAN
                }
              }
            }
          }
        }
      }
    }
    ... on Rejection {
      message
    }
  }
}
"""

# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Swan OAuth Tester", layout="wide")
st.title("Swan OAuth & Payment Tester")
st.caption("Local end-to-end test: OAuth login → token exchange → user verify → payment")

# Display any OAuth error that arrived via redirect
if "oauth_error" in st.session_state:
    st.error(f"OAuth error from Swan: {st.session_state.pop('oauth_error')}")

# ── Env vars status ────────────────────────────────────────────────────────────
with st.expander("Env vars status", expanded=False):
    env_checks = {
        "SWAN_CLIENT_ID":             CLIENT_ID,
        "SWAN_CLIENT_SECRET":         CLIENT_SECRET,
        "SWAN_REDIRECT_URI":          REDIRECT_URI,
        "SWAN_ACCOUNT_ID":            ACCOUNT_ID,
        "SWAN_ACCOUNT_MEMBERSHIP_ID": ACCOUNT_MEMBERSHIP_ID,
        "SWAN_USER_ACCESS_TOKEN":     os.getenv("SWAN_USER_ACCESS_TOKEN", ""),
    }
    for k, v in env_checks.items():
        icon = "✅" if v else "❌"
        st.write(f"{icon} `{k}` {'— set' if v else '— **MISSING**'}")
    session_tok = st.session_state.get("user_access_token", "")
    src = st.session_state.get("token_source", "oauth")
    if session_tok:
        st.write(f"✅ `Session token` ({src}) — `{session_tok[:12]}…{session_tok[-6:]}`")
    else:
        st.write("❌ `Session token` — not yet set")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — OAuth Authorization
# ══════════════════════════════════════════════════════════════════════════════
st.header("Step 1 · Generate authorization URL")

if not CLIENT_ID:
    st.error("SWAN_CLIENT_ID missing from .env — cannot build OAuth URL.")
elif not REDIRECT_URI:
    st.error("SWAN_REDIRECT_URI missing from .env.")
else:
    st.write(f"Redirect URI in use: `{REDIRECT_URI}`")
    st.caption(
        "Make sure this exact URI is registered as an OAuth redirect in your Swan Dashboard "
        "(Settings > OAuth clients > your client > Redirect URIs)."
    )

    if st.button("Generate authorization URL", key="btn_gen"):
        state = secrets.token_urlsafe(16)
        st.session_state["oauth_state_sent"] = state
        auth_url = SWAN_AUTH_URL + "?" + urllib.parse.urlencode({
            "response_type": "code",
            "client_id":     CLIENT_ID,
            "redirect_uri":  REDIRECT_URI,
            "scope":         "openid offline",
            "state":         state,
        })
        st.session_state["auth_url"] = auth_url

    if "auth_url" in st.session_state:
        st.code(st.session_state["auth_url"], language=None)
        st.link_button("Open Swan Login →", st.session_state["auth_url"])
        st.caption("After login Swan will redirect back here. Come back to this page — the code is captured automatically.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Callback + token exchange
# ══════════════════════════════════════════════════════════════════════════════
st.header("Step 2 · OAuth Callback & token exchange")

if "oauth_code" not in st.session_state:
    st.info("Waiting for callback… Complete the login in Step 1, then return here.")
else:
    code       = st.session_state["oauth_code"]
    state_rcv  = st.session_state.get("oauth_state_received", "")
    state_sent = st.session_state.get("oauth_state_sent", "")

    st.success("Callback received!")
    col1, col2 = st.columns(2)
    col1.metric("code (prefix)", code[:16] + "…")
    col2.metric("state (prefix)", (state_rcv[:14] + "…") if state_rcv else "—")

    # CSRF check
    if state_sent and state_rcv:
        if state_sent != state_rcv:
            st.error("State mismatch — possible CSRF attack. Do not proceed.")
            st.stop()
        else:
            st.caption("✅ State CSRF check passed")
    elif not state_sent:
        st.caption("ℹ️ No local state to compare (page may have reloaded) — proceeding without CSRF check")

    if st.button("Exchange code for token", type="primary", key="btn_exchange"):
        with st.spinner("Calling Swan token endpoint…"):
            try:
                resp = requests.post(SWAN_TOKEN_URL, data={
                    "grant_type":   "authorization_code",
                    "code":         code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id":    CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                }, timeout=15)
                body = resp.json()

                if resp.status_code != 200:
                    err = body.get("error", "unknown_error")
                    desc = body.get("error_description", "")
                    if err == "invalid_grant":
                        st.error("invalid_grant — code already used or expired. Redo step 1.")
                    elif err == "invalid_client":
                        st.error("invalid_client — check SWAN_CLIENT_ID / SWAN_CLIENT_SECRET in .env")
                    elif "redirect_uri" in desc.lower():
                        st.error(f"redirect_uri mismatch: `{REDIRECT_URI}` is not registered for this client in Swan Dashboard.")
                    else:
                        st.error(f"Token error ({resp.status_code}): {err} — {desc}")
                    with st.expander("Raw response"):
                        st.json(body)
                else:
                    access_token = body.get("access_token", "")
                    if not access_token:
                        st.error("Response OK but no access_token field.")
                        st.json(body)
                    else:
                        st.session_state["user_access_token"] = access_token
                        st.session_state["token_source"] = "oauth"
                        st.session_state["token_data"]   = body
                        # Clear used code so button can't be clicked twice
                        del st.session_state["oauth_code"]
                        st.success("Token exchanged successfully!")
                        st.code(f"SWAN_USER_ACCESS_TOKEN={access_token}", language="bash")
                        st.caption("Copy this value into .env to persist across sessions.")
                        if body.get("refresh_token"):
                            st.caption(f"refresh_token available: `{body['refresh_token'][:16]}…`")

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach oauth.swan.io — check network connectivity.")
            except Exception as e:
                st.error(f"Exception during token exchange: {e}")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Token management + user verify
# ══════════════════════════════════════════════════════════════════════════════
st.header("Step 3 · Token & current user")

token = st.session_state.get("user_access_token", "")

if token:
    src = st.session_state.get("token_source", "?")
    st.success(f"Token in session (source: **{src}**): `{token[:20]}…{token[-6:]}`")
else:
    st.warning("No user access token in session yet.")

with st.expander("Override / paste token manually"):
    manual = st.text_input("Paste SWAN_USER_ACCESS_TOKEN here", type="password", key="input_manual_tok")
    if st.button("Apply", key="btn_apply_tok") and manual:
        st.session_state["user_access_token"] = manual.strip()
        st.session_state["token_source"] = "manual"
        token = manual.strip()
        st.success("Token updated.")
        st.rerun()

if token:
    if st.button("Verify current user", key="btn_verify"):
        with st.spinner("Querying Swan…"):
            user_ok = False
            try:
                data = gql(_USER_Q, token=token)
                user = data.get("user")
                if user:
                    user_ok = True
                    st.subheader("Authenticated user")
                    u1, u2, u3 = st.columns(3)
                    u1.metric("Name", user.get("fullName") or f"{user.get('firstName','')} {user.get('lastName','')}".strip())
                    u2.metric("Phone", user.get("mobilePhoneNumber") or "—")
                    u3.metric("Status", user.get("status") or "—")
                    st.caption(f"user.id = `{user.get('id')}`")
                else:
                    st.warning("user query returned no data.")
            except Exception as e:
                st.warning(f"`user` query failed: {e}")

            # Always also show membership + account balance if ID is set
            if ACCOUNT_MEMBERSHIP_ID:
                st.subheader("Account membership")
                try:
                    data = gql(_MEMBERSHIP_Q, {"id": ACCOUNT_MEMBERSHIP_ID}, token=token)
                    m = data.get("accountMembership") or {}
                    acc = m.get("account") or {}
                    bal = acc.get("balances") or {}
                    av  = bal.get("available") or {}
                    bk  = bal.get("booked") or {}
                    u = m.get("user") or {}

                    if not user_ok:
                        n1, n2 = st.columns(2)
                        n1.metric("User", u.get("fullName") or f"{u.get('firstName','')} {u.get('lastName','')}".strip() or "—")
                        n2.metric("Membership status", (m.get("statusInfo") or {}).get("status", "—"))

                    b1, b2, b3 = st.columns(3)
                    b1.metric("Available", f"{av.get('value','?')} {av.get('currency','')}")
                    b2.metric("Booked",    f"{bk.get('value','?')} {bk.get('currency','')}")
                    b3.metric("Account IBAN", acc.get("IBAN") or "—")
                    st.caption(f"account.id = `{acc.get('id','—')}`  |  account.name = `{acc.get('name','—')}`")

                    with st.expander("Raw membership response"):
                        st.json(data)
                except Exception as e:
                    st.error(f"accountMembership query failed: {e}")
            else:
                st.caption("Set SWAN_ACCOUNT_MEMBERSHIP_ID in .env to also fetch account balances.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Initiate payment
# ══════════════════════════════════════════════════════════════════════════════
st.header("Step 4 · Initiate supplier payment")

token = st.session_state.get("user_access_token", "")

if not token:
    st.warning("Complete Step 3 first — a user access token is required.")
elif not ACCOUNT_ID:
    st.error("SWAN_ACCOUNT_ID missing from .env.")
else:
    with st.form("payment_form"):
        st.write("**Beneficiary**")
        fc1, fc2 = st.columns(2)
        supplier_name = fc1.text_input("Supplier name", os.getenv("DEMO_SUPPLIER_NAME", "Demo Industrial Supplier"))
        supplier_iban = fc2.text_input("Supplier IBAN",  os.getenv("DEMO_SUPPLIER_IBAN", "DE89370400440532013000"))

        st.write("**Transfer**")
        fa1, fa2 = st.columns(2)
        amount_str = fa1.text_input("Amount (EUR)", os.getenv("DEMO_SUPPLIER_AMOUNT", "1"))
        label_str  = fa2.text_input("Label", "Anypay MRO replenishment")

        submitted = st.form_submit_button("Initiate payment →", type="primary")

    if submitted:
        with st.spinner("Initiating supplier payment…"):
            try:
                variables = {
                    "input": {
                        "accountId":         ACCOUNT_ID,
                        "consentRedirectUrl": REDIRECT_URI,
                        "idempotencyKey":    str(uuid.uuid4()),
                        "creditTransfers": [{
                            "amount": {"value": amount_str, "currency": "EUR"},
                            "label":  label_str,
                            "sepaBeneficiary": {
                                "name": supplier_name,
                                "iban": supplier_iban,
                                "save": False,
                            },
                        }],
                    }
                }
                data   = gql(_PAYMENT_M, variables, token=token)
                result = data["initiateCreditTransfers"]
                tn     = result.get("__typename")

                if tn == "InitiateCreditTransfersSuccessPayload":
                    payment = result["payment"]
                    sinfo   = payment.get("statusInfo", {})

                    st.success("Payment initiated!")
                    m1, m2 = st.columns(2)
                    pid = payment.get("id") or ""
                    m1.metric("payment_id", pid[:14] + "…" if len(pid) > 14 else pid)
                    m2.metric("status", sinfo.get("status", "—"))

                    for edge in payment.get("transactions", {}).get("edges", []):
                        node     = edge["node"]
                        creditor = node.get("creditor", {})
                        amt      = node.get("amount", {})
                        t1, t2, t3 = st.columns(3)
                        t1.metric("amount",      f"{amt.get('value')} {amt.get('currency')}")
                        t2.metric("beneficiary", creditor.get("name", "—"))
                        t3.metric("tx status",   (node.get("statusInfo") or {}).get("status", "—"))
                        st.caption(f"IBAN: `{creditor.get('IBAN','—')}`  |  label: `{node.get('label','—')}`")

                    consent = sinfo.get("consent")
                    if consent:
                        curl = consent.get("consentUrl", "")
                        st.warning("SCA consent required to finalize this transfer.")
                        st.code(curl, language=None)
                        if curl:
                            st.link_button("Complete SCA →", curl)
                        st.caption(f"Consent status: `{consent.get('status','—')}`")

                    st.info(
                        "Sandbox: to book the transfer go to "
                        "Swan Dashboard > Developers > Event Simulator > book an outgoing transfer"
                    )
                    with st.expander("Raw API response"):
                        st.json(result)

                elif tn == "ForbiddenRejection":
                    st.error("ForbiddenRejection — the user token may lack permissions for this account.")
                    with st.expander("Raw"):
                        st.json(result)
                else:
                    st.error(f"Rejected: {tn} — {result.get('message','')}")
                    with st.expander("Raw"):
                        st.json(result)

            except RuntimeError as e:
                msg = str(e)
                if "invalid_grant" in msg or "Unauthorized" in msg or "401" in msg:
                    st.error("Token rejected by Swan (401 / invalid_grant). Redo OAuth flow in Step 1.")
                else:
                    st.error(f"API error:\n\n```\n{msg}\n```")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach api.swan.io — check network.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
