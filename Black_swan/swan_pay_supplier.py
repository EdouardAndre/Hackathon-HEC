from dotenv import load_dotenv
load_dotenv()

import os
import sys
import json
import uuid
import requests

SWAN_GRAPHQL_URL = "https://api.swan.io/sandbox-partner/graphql"

# Auth & account — checked at call time, not at import, to allow safe import in Streamlit
USER_ACCESS_TOKEN = os.getenv("SWAN_USER_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("SWAN_ACCOUNT_ID")
REDIRECT_URI = os.getenv("SWAN_REDIRECT_URI")

# Demo supplier — override via .env or use fallbacks
SUPPLIER_NAME = os.getenv("DEMO_SUPPLIER_NAME", "Demo Industrial Supplier")
SUPPLIER_IBAN = os.getenv("DEMO_SUPPLIER_IBAN", "DE89370400440532013000")
SUPPLIER_AMOUNT = os.getenv("DEMO_SUPPLIER_AMOUNT", "2500")

MUTATION = """
mutation InitiateSupplierPayment($input: InitiateCreditTransfersInput!) {
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
              amount {
                value
                currency
              }
              label
              statusInfo {
                status
              }
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


def gql(query: str, variables: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {USER_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        SWAN_GRAPHQL_URL,
        headers=headers,
        json={"query": query, "variables": variables},
        timeout=60,
    )
    try:
        payload = r.json()
    except Exception:
        r.raise_for_status()
        raise

    if r.status_code >= 400:
        raise RuntimeError(
            f"HTTP {r.status_code}\n" +
            json.dumps(payload, indent=2, ensure_ascii=False)
        )
    if payload.get("errors"):
        raise RuntimeError(
            "GraphQL errors:\n" +
            json.dumps(payload["errors"], indent=2, ensure_ascii=False)
        )
    return payload["data"]


def initiate_supplier_payment(
    supplier_name: str = SUPPLIER_NAME,
    supplier_iban: str = SUPPLIER_IBAN,
    amount: str = SUPPLIER_AMOUNT,
    currency: str = "EUR",
    label: str = "Anypay MRO replenishment",
    idempotency_key: str = None,
) -> dict:
    # Env checks at call time — fails cleanly whether run standalone or via Streamlit
    if not USER_ACCESS_TOKEN:
        raise RuntimeError(
            "Missing SWAN_USER_ACCESS_TOKEN in .env\n"
            "initiateCreditTransfers requires a user access token (OAuth Authorization Code flow),\n"
            "distinct from the project token used for onboarding."
        )
    if not ACCOUNT_ID:
        raise RuntimeError("Missing SWAN_ACCOUNT_ID in .env")
    if not REDIRECT_URI:
        raise RuntimeError(
            "Missing SWAN_REDIRECT_URI in .env\n"
            "consentRedirectUrl is required by Swan for the SCA consent flow."
        )

    if idempotency_key is None:
        idempotency_key = str(uuid.uuid4())

    variables = {
        "input": {
            "accountId": ACCOUNT_ID,
            "consentRedirectUrl": REDIRECT_URI,
            "idempotencyKey": idempotency_key,
            "creditTransfers": [
                {
                    "amount": {"value": amount, "currency": currency},
                    "label": label,
                    "sepaBeneficiary": {
                        "name": supplier_name,
                        "iban": supplier_iban,
                        "save": False,
                    },
                }
            ],
        }
    }

    print(f"Initiating SEPA transfer — account {ACCOUNT_ID}, {amount} {currency} → {supplier_name}")
    data = gql(MUTATION, variables)
    result = data["initiateCreditTransfers"]

    print("\nSwan raw response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    try:
        result = initiate_supplier_payment()
    except RuntimeError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    typename = result.get("__typename")
    print("\n" + "=" * 40)

    if typename == "InitiateCreditTransfersSuccessPayload":
        payment = result["payment"]
        status_info = payment.get("statusInfo", {})
        print("SUCCESS")
        print("payment_id =", payment.get("id"))
        print("status     =", status_info.get("status"))

        consent = status_info.get("consent")
        if consent:
            print("\nSCA required — open this URL to validate the transfer:")
            print("consent_url    =", consent.get("consentUrl"))
            print("consent_status =", consent.get("status"))
        else:
            print("\nNo consent URL returned — payment may be directly initiated.")

        for edge in payment.get("transactions", {}).get("edges", []):
            node = edge.get("node", {})
            creditor = node.get("creditor", {})
            amt = node.get("amount", {})
            print(f"\nTransaction:")
            print(f"  id          = {node.get('id')}")
            print(f"  amount      = {amt.get('value')} {amt.get('currency')}")
            print(f"  label       = {node.get('label')}")
            print(f"  status      = {node.get('statusInfo', {}).get('status')}")
            print(f"  beneficiary = {creditor.get('name')} / {creditor.get('IBAN')}")
    else:
        print("FAILED")
        print("type    =", typename)
        print("message =", result.get("message"))
        sys.exit(1)
