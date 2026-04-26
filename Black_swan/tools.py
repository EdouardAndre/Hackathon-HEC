import os
import requests

def check_policy(amount: float, merchant: str) -> dict:
    MAX_AMOUNT = 500.0
    if amount <= 0:
        return {"approved": False, "reason": "Amount must be positive"}
    if amount > MAX_AMOUNT:
        return {"approved": False, "reason": f"Amount {amount}€ exceeds policy limit of {MAX_AMOUNT}€"}
    return {"approved": True, "reason": f"Payment of {amount}€ to {merchant} is within policy"}

def swan_pay(amount: float) -> dict:
    token = os.environ.get("SWAN_API_TOKEN", "")
    project_id = os.environ.get("SWAN_PROJECT_ID", "mock-project-id")
    url = os.environ.get("SWAN_API_URL", "https://api.swan.io/graphql")

    query = """
    mutation AddCard($input: AddCardInput!) {
      addCard(input: $input) {
        card {
          id
          statusInfo {
            status
          }
        }
      }
    }
    """
    variables = {
        "input": {
            "projectId": project_id,
            "spendingLimit": {
                "amount": str(amount),
                "currency": "EUR",
                "period": "Always"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                return {"success": False, "error": data["errors"][0]["message"]}
            return {"success": True, "data": data.get("data", {}), "amount": amount}
        return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e), "mock": True, "amount": amount}
