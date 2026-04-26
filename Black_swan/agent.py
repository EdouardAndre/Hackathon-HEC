from dotenv import load_dotenv
load_dotenv()

import os
import json
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Part,
    Content,
)
from tools import check_policy, swan_pay

vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "anypay-494410"), location="us-central1")

check_policy_decl = FunctionDeclaration(
    name="check_policy",
    description="Check if a payment is within the company policy limits (max 500€)",
    parameters={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Payment amount in EUR"},
            "merchant": {"type": "string", "description": "Merchant name"},
        },
        "required": ["amount", "merchant"],
    },
)

swan_pay_decl = FunctionDeclaration(
    name="swan_pay",
    description="Execute the payment via Swan API using a card",
    parameters={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Payment amount in EUR"},
        },
        "required": ["amount"],
    },
)

tools = Tool(function_declarations=[check_policy_decl, swan_pay_decl])

SYSTEM_PROMPT = (
    "Tu es l'agent Anypay. NE RÉPONDS PAS PAR TEXTE si l'achat est < 500€. "
    "Appelle DIRECTEMENT la fonction swan_pay. "
    "Si l'achat est > 500€, refuse poliment."
)

model = GenerativeModel(
    model_name="gemini-2.5-pro",
    tools=[tools],
    system_instruction=SYSTEM_PROMPT,
)

def run_agent(user_message: str, chat_history: list = None) -> str:
    if chat_history is None:
        chat_history = []

    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_message)

    while True:
        candidate = response.candidates[0]
        parts = candidate.content.parts

        function_calls = [p.function_call for p in parts if p.function_call]
        if not function_calls:
            return response.text

        tool_results = []
        for fc in function_calls:
            name = fc.name
            args = dict(fc.args)

            if name == "check_policy":
                result = check_policy(**args)
            elif name == "swan_pay":
                result = swan_pay(**args)
            else:
                result = {"error": f"Unknown tool: {name}"}

            tool_results.append(
                Part.from_function_response(name=name, response=result)
            )

        response = chat.send_message(tool_results)

    return response.text
