from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

OAUTH_URL = "https://oauth.swan.io/oauth2/token"
GRAPHQL_URL = "https://api.swan.io/sandbox-partner/graphql"

CLIENT_ID = os.getenv("SWAN_CLIENT_ID")
CLIENT_SECRET = os.getenv("SWAN_CLIENT_SECRET")


def get_token() -> str:
    """Fetch a client_credentials OAuth token from Swan."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise EnvironmentError("SWAN_CLIENT_ID / SWAN_CLIENT_SECRET manquants dans .env")

    r = requests.post(
        OAUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=30,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise ValueError(f"Pas d'access_token dans la réponse Swan : {r.text}")
    print("[swan] Token OK")
    return token


def gql(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query/mutation against the Swan sandbox partner API."""
    token = get_token()
    r = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=60,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise Exception(
            "[swan] GraphQL errors:\n" +
            json.dumps(payload["errors"], indent=2, ensure_ascii=False)
        )
    return payload["data"]
