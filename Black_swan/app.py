from dotenv import load_dotenv
load_dotenv()

import json
import streamlit as st
from agent import run_agent
from swan_onboarding import create_onboarding
from swan_pay_supplier import initiate_supplier_payment, SUPPLIER_NAME, SUPPLIER_IBAN, SUPPLIER_AMOUNT

st.title("Swan Payment Agent")

with st.sidebar:
    st.header("Swan Sandbox")
    if st.button("Generate Swan Onboarding"):
        with st.spinner("Calling Swan..."):
            try:
                result = create_onboarding()
                typename = result.get("__typename", "")
                if typename == "OnboardIndividualAccountHolderSuccessPayload":
                    ob = result["onboarding"]
                    st.success(f"onboarding.id : `{ob['id']}`")
                    if ob.get("onboardingUrl"):
                        st.markdown(f"[Ouvrir le lien onboarding]({ob['onboardingUrl']})")
                elif typename == "ValidationRejection":
                    st.error(f"ValidationRejection : {result.get('message')}")
                    for f in result.get("fields", []):
                        st.write(f"  • `{f['path']}` — {f['message']}")
                elif typename == "ForbiddenRejection":
                    st.error(f"ForbiddenRejection : {result.get('message')}")
                else:
                    st.error(f"{typename} : {result.get('message')}")
                st.json(result)
            except Exception as e:
                st.error(f"Erreur Swan : {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ex: Pay 200€ to Amazon")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response = run_agent(user_input)
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ── Supplier Payment ──────────────────────────────────────────────
st.divider()
st.subheader("Supplier payment")

_iban_display = f"{SUPPLIER_IBAN[:4]}...{SUPPLIER_IBAN[-4:]}" if len(SUPPLIER_IBAN) > 8 else SUPPLIER_IBAN

st.markdown("**Purchase recommendation**")
col_a, col_b, col_c = st.columns(3)
col_a.metric("Supplier", SUPPLIER_NAME)
col_b.metric("Amount", f"{SUPPLIER_AMOUNT} EUR")
col_c.metric("IBAN", _iban_display)
st.caption("Reference: Anypay MRO replenishment")

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None

if st.button("Approve supplier payment", type="primary"):
    with st.spinner("Initiating supplier payment..."):
        try:
            st.session_state.payment_result = initiate_supplier_payment()
        except Exception as e:
            st.session_state.payment_result = {"__error": str(e)}

if st.session_state.payment_result:
    result = st.session_state.payment_result

    if "__error" in result:
        st.error(f"Payment error: {result['__error']}")
    else:
        typename = result.get("__typename")

        if typename == "InitiateCreditTransfersSuccessPayload":
            payment = result["payment"]
            status_info = payment.get("statusInfo", {})
            st.success("Payment initiated successfully.")

            r1, r2 = st.columns(2)
            r1.metric("Payment ID", (payment.get("id") or "")[:12] + "…")
            r2.metric("Status", status_info.get("status", ""))

            for edge in payment.get("transactions", {}).get("edges", []):
                node = edge.get("node", {})
                creditor = node.get("creditor", {})
                amt = node.get("amount", {})
                r3, r4 = st.columns(2)
                r3.metric("Amount", f"{amt.get('value')} {amt.get('currency')}")
                r4.metric("Beneficiary", creditor.get("name", ""))
                st.caption(f"IBAN: `{creditor.get('IBAN', '')}`")

            consent = status_info.get("consent")
            if consent:
                st.warning("SCA consent required to finalize this transfer.")
                st.markdown(f"**Consent URL:** [{consent.get('consentUrl')}]({consent.get('consentUrl')})")

            st.info(
                "For Sandbox final booking, go to "
                "Swan Dashboard > Developers > Event Simulator > book an outgoing transfer"
            )
        else:
            st.error(f"{typename}: {result.get('message')}")
