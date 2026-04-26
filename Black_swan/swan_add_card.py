from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

SWAN_GRAPHQL_URL = "https://api.swan.io/sandbox-partner/graphql"

USER_ACCESS_TOKEN = os.getenv("SWAN_USER_ACCESS_TOKEN")
ACCOUNT_MEMBERSHIP_ID = os.getenv("SWAN_ACCOUNT_MEMBERSHIP_ID")
REDIRECT_URI = os.getenv("SWAN_REDIRECT_URI")  # optionnel

if not USER_ACCESS_TOKEN:
    raise RuntimeError(
        "Missing SWAN_USER_ACCESS_TOKEN in .env\n"
        "Ce token est un USER access token (OAuth Authorization Code), "
        "distinct du project token client_credentials.\n"
        "Obtenez-le via le flow OAuth Swan avec l'utilisateur du compte."
    )

if not ACCOUNT_MEMBERSHIP_ID:
    raise RuntimeError(
        "Missing SWAN_ACCOUNT_MEMBERSHIP_ID in .env\n"
        "Récupérez-le via la query Swan : accountMemberships { edges { node { id } } }"
    )


# Schéma Swan réel : AddCardInput utilise `name` (pas cardName) et pas de champ cardFormat.
# addCard crée une carte virtuelle par défaut.
# consentRedirectUrl est requis pour le flow SCA.
MUTATION = """
mutation AddVirtualCard($input: AddCardInput!) {
  addCard(input: $input) {
    __typename

    ... on AddCardSuccessPayload {
      card {
        id
        statusInfo {
          __typename
          status
          ... on CardConsentPendingStatusInfo {
            consent {
              consentUrl
              status
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


def add_virtual_card(card_name: str = "Anypay Virtual Card") -> dict:
    card_input: dict = {
        "accountMembershipId": ACCOUNT_MEMBERSHIP_ID,
        "name": card_name,
    }

    if REDIRECT_URI:
        card_input["consentRedirectUrl"] = REDIRECT_URI

    variables = {"input": card_input}

    print(f"Envoi de la mutation addCard pour membership {ACCOUNT_MEMBERSHIP_ID}...")
    data = gql(MUTATION, variables)
    result = data["addCard"]

    print("\nRéponse brute Swan:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    result = add_virtual_card()
    typename = result.get("__typename")

    print("\n" + "=" * 40)

    if typename == "AddCardSuccessPayload":
        card = result["card"]
        status_info = card.get("statusInfo", {})
        print("SUCCES")
        print("card_id =", card.get("id"))
        print("status  =", status_info.get("status"))

        consent = status_info.get("consent")
        if consent:
            print("\nSCA requis — ouvrez ce lien pour valider la carte :")
            print("consent_url    =", consent.get("consentUrl"))
            print("consent_status =", consent.get("status"))
        else:
            print("\nAucun consent URL — carte directement active.")
    else:
        print("ECHEC")
        print("type    =", typename)
        print("message =", result.get("message"))
