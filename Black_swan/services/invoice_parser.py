import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gemini_service


def get_mock_invoice(scenario: str) -> dict:
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "mock_invoice.json",
    )
    with open(data_path) as f:
        invoices = json.load(f)
    return invoices.get(scenario, invoices["exact_match"])


def structure_invoice(raw: dict) -> tuple[dict, str]:
    return gemini_service.structure_invoice(raw)
