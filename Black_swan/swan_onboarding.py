from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

import os
import sys
import json
from swan_client import gql

REDIRECT_URI = os.getenv("SWAN_REDIRECT_URI", "http://localhost:8501/callback")

_MUTATION = """
mutation CreateIndividualOnboarding($input: CreateIndividualAccountHolderOnboardingInput!) {
  createIndividualAccountHolderOnboarding(input: $input) {
    __typename
    ... on CreateIndividualAccountHolderOnboardingSuccessPayload {
      onboarding {
        id
        onboardingUrl
        statusInfo {
          status
        }
      }
    }
    ... on Rejection {
      message
    }
  }
}
"""

def create_onboarding(
    email: str = "toi+hackathon@example.com",
    first_name: str = "Minh",
    last_name: str = "Tran",
    phone: str = "+33612345678",
    birth_date: str = "1998-01-01",
) -> dict:
    variables = {
        "input": {
            "accountInfo": {
                "country": "FRA",
                "name": "Anypay Sandbox"
            },
            "accountAdmin": {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "mobilePhoneNumber": phone,
                "birthDate": birth_date,
                "nationality": "FRA",
                "employmentStatus": "Employee",
                "preferredLanguage": "fr",
                "monthlyIncome": "Between3000And4500",
                "address": {
                    "addressLine1": "123 avenue de Paris",
                    "city": "Paris",
                    "country": "FRA",
                    "postalCode": "75000",
                }
            },
            "oAuthRedirectParameters": {
                "redirectUri": REDIRECT_URI
            }
        }
    }

    data = gql(_MUTATION, variables)
    result = data["createIndividualAccountHolderOnboarding"]

    print("[swan] Onboarding result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result

def topup_sandbox_account(account_iban: str, amount_eur: float = 10_000.0) -> dict:
    raise NotImplementedError(
        "topup_sandbox_account() sera branché après récupération de SWAN_ACCOUNT_IBAN."
    )

if __name__ == "__main__":
    try:
        result = create_onboarding()
    except Exception as e:
        print("FAIL")
        print("type=Exception")
        print(f"message={e}")
        sys.exit(1)

    typename = result.get("__typename", "")

    if typename == "CreateIndividualAccountHolderOnboardingSuccessPayload":
        ob = result["onboarding"]
        print("SUCCESS")
        print(f"onboarding_id={ob['id']}")
        print(f"onboarding_url={ob.get('onboardingUrl', 'N/A')}")
        print(f"status={ob.get('statusInfo', {}).get('status')}")
        sys.exit(0)

    print("FAIL")
    print(f"type={typename}")
    print(f"message={result.get('message')}")
    sys.exit(1)