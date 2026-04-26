from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
import requests

SWAN_TOKEN_URL = "https://oauth.swan.io/oauth2/token"
CLIENT_ID      = os.getenv("SWAN_CLIENT_ID",    "")
CLIENT_SECRET  = os.getenv("SWAN_CLIENT_SECRET", "")
REDIRECT_URI   = os.getenv("SWAN_REDIRECT_URI",  "http://localhost:8501/callback")

st.set_page_config(page_title="Anypay — Callback", layout="centered")

_qp         = st.query_params
_code       = _qp.get("code",              "")
_state      = _qp.get("state",             "")
_err        = _qp.get("error",             "")
_edesc      = _qp.get("error_description", "")
_consent_id = _qp.get("consentId",         "")

# ── Swan payment SCA consent callback (consentId param, no code) ──────────────
if _consent_id and not _code:
    st.session_state["app_state"] = "payment_submitted"
    st.query_params.clear()
    st.switch_page("streamlit_app.py")

# ── OAuth error from Swan ─────────────────────────────────────────────────────
if _err:
    st.session_state["oauth_error"] = _edesc or _err
    st.query_params.clear()
    st.switch_page("streamlit_app.py")

# ── RENDER 1: stash code, clear URL, rerun ────────────────────────────────────
if _code and "_pending_code" not in st.session_state:
    st.session_state["_pending_code"]  = _code
    st.session_state["_pending_state"] = _state
    st.query_params.clear()
    st.rerun()

# ── RENDER 2: exchange the stashed code ───────────────────────────────────────
pending_code = st.session_state.pop("_pending_code", None)
st.session_state.pop("_pending_state", None)

if not pending_code:
    if st.session_state.get("user_access_token"):
        st.switch_page("streamlit_app.py")
    st.title("Sign-in callback")
    st.error("No authorization code in URL.")
    st.info("This page is only reachable via the sign-in redirect flow.")
    if st.button("← Back to app"):
        st.switch_page("streamlit_app.py")
    st.stop()

# ── Token exchange ─────────────────────────────────────────────────────────────
st.title("Completing sign-in…")

body        = {}
http_status = 0
raw_text    = ""

payload = {
    "grant_type":    "authorization_code",
    "code":          pending_code,
    "redirect_uri":  REDIRECT_URI,
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

with st.spinner("Exchanging credentials…"):
    try:
        resp     = requests.post(SWAN_TOKEN_URL, data=payload, timeout=15)
        http_status = resp.status_code
        raw_text    = resp.text
        try:
            body = resp.json()
        except Exception:
            body = {"raw": raw_text}
    except requests.exceptions.ConnectionError as e:
        st.session_state["oauth_exchange_error"] = {
            "type": "ConnectionError",
            "detail": str(e),
            "request_payload": {k: v for k, v in payload.items() if k != "client_secret"},
        }
        st.switch_page("streamlit_app.py")
    except Exception as e:
        st.session_state["oauth_exchange_error"] = {
            "type": type(e).__name__,
            "detail": str(e),
        }
        st.switch_page("streamlit_app.py")

access_token = body.get("access_token", "")

if http_status == 200 and access_token:
    st.session_state["user_access_token"] = access_token
    st.session_state["token_source"]      = "oauth"
    st.session_state["token_data"]        = body
    if body.get("refresh_token"):
        st.session_state["refresh_token"] = body["refresh_token"]
    # Clear any previous exchange error
    st.session_state.pop("oauth_exchange_error", None)
    st.session_state["_just_got_token"] = True
    st.switch_page("streamlit_app.py")

else:
    # Store full diagnostic so main app can display it
    err  = body.get("error",             "unknown_error")
    desc = body.get("error_description", "")
    st.session_state["oauth_exchange_error"] = {
        "http_status": http_status,
        "error":       err,
        "description": desc,
        "raw_body":    body,
        "redirect_uri_used": REDIRECT_URI,
        "request_payload": {k: v for k, v in payload.items() if k != "client_secret"},
    }
    # Redirect back — main app will display the error from session_state
    st.switch_page("streamlit_app.py")
