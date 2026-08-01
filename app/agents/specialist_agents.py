from typing import Any, Dict

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama

from app.agents.compliance_agent import ComplianceAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.kyc_agent import KYCAgent
from app.data.dummy_data import get_customer, get_transaction


# ---------------------------------------------------------
# Existing deterministic analysis classes
# ---------------------------------------------------------

fraud_engine = FraudAgent()
kyc_engine = KYCAgent()
compliance_engine = ComplianceAgent()


# ---------------------------------------------------------
# Shared local language model
# ---------------------------------------------------------

llm = ChatOllama(
    model="llama3.1:latest",
    temperature=0,
)


# ---------------------------------------------------------
# Compatibility helper
# ---------------------------------------------------------

def serialize_model(value: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model into a dictionary.

    Supports both Pydantic version 1 and version 2.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    raise TypeError(
        f"Cannot serialize object of type {type(value).__name__}"
    )


# =========================================================
# FRAUD AGENT TOOL
# =========================================================

@tool
def investigate_transaction_fraud(
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Retrieve a transaction and run the complete trusted fraud analysis.

    Returns transaction details, fraud risk score, risk level,
    and detected fraud signals.
    """
    transaction = get_transaction(transaction_id)

    if transaction is None:
        return {
            "found": False,
            "error": f"Transaction {transaction_id} was not found.",
        }

    fraud_result = fraud_engine.investigate(transaction)

    return {
        "found": True,
        "transaction_id": transaction_id,
        "transaction": serialize_model(transaction),
        "fraud_result": serialize_model(fraud_result),
    }


# =========================================================
# KYC AGENT TOOL
# =========================================================

@tool
def perform_kyc_review(
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Retrieve the customer associated with a transaction and run the
    trusted KYC review.

    Returns identity-verification status, sanctions status,
    and customer-risk rating.
    """
    transaction = get_transaction(transaction_id)

    if transaction is None:
        return {
            "found": False,
            "error": f"Transaction {transaction_id} was not found.",
        }

    customer = get_customer(transaction.customer_id)

    if customer is None:
        return {
            "found": False,
            "error": (
                f"Customer {transaction.customer_id} associated with "
                f"transaction {transaction_id} was not found."
            ),
        }

    kyc_result = kyc_engine.verify(transaction)

    return {
        "found": True,
        "transaction_id": transaction_id,
        "customer_id": transaction.customer_id,
        "customer": customer,
        "kyc_result": serialize_model(kyc_result),
    }


# =========================================================
# COMPLIANCE AGENT TOOL
# =========================================================

@tool
def perform_compliance_review(
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Run the complete trusted compliance decision workflow.

    This tool retrieves the transaction, runs fraud analysis,
    runs KYC analysis, and produces a compliance recommendation.

    The result is a recommendation only. This tool does not block a
    transaction, file a SAR, close an account, contact a customer,
    or contact law enforcement.
    """
    transaction = get_transaction(transaction_id)

    if transaction is None:
        return {
            "found": False,
            "error": f"Transaction {transaction_id} was not found.",
        }

    fraud_result = fraud_engine.investigate(transaction)
    kyc_result = kyc_engine.verify(transaction)

    compliance_result = compliance_engine.review(
        transaction=transaction,
        fraud_result=fraud_result,
        kyc_result=kyc_result,
    )

    return {
        "found": True,
        "transaction_id": transaction_id,
        "fraud_result": serialize_model(fraud_result),
        "kyc_result": serialize_model(kyc_result),
        "compliance_result": serialize_model(compliance_result),
    }


# =========================================================
# SPECIALIST LLM AGENTS
# =========================================================

fraud_specialist_agent = create_agent(
    model=llm,
    tools=[investigate_transaction_fraud],
    name="fraud_specialist",
    system_prompt="""
You are a Fraud Investigation Agent.

You must call investigate_transaction_fraud before answering any
request about a transaction.

Do not describe a future action.
Do not say that you will run a tool next.
Actually invoke the tool and wait for the result.

After the tool returns, provide one completed fraud report containing:

- Transaction ID
- Fraud risk score
- Fraud risk level
- Fraud signals
- Brief behavioral-risk explanation

Rules:
1. Use only evidence returned by the tool.
2. Preserve the exact risk score returned by the tool.
3. Preserve the exact risk level returned by the tool.
4. Do not recalculate or alter the fraud result.
5. Do not perform KYC or compliance analysis.
6. Do not claim that fraud is confirmed.
7. Do not claim that a transaction was blocked.
8. Do not invent evidence.
9. Do not return an interim response.
""",
)


kyc_specialist_agent = create_agent(
    model=llm,
    tools=[perform_kyc_review],
    name="kyc_specialist",
    system_prompt="""
You are a KYC and Customer Risk Agent.

You must call perform_kyc_review before answering any request about
a transaction's customer.

Do not describe a future action.
Do not say that you will run a tool next.
Actually invoke the tool and wait for the result.

After the tool returns, provide one completed KYC report containing:

- Transaction ID
- Customer ID
- Identity-verification status
- Sanctions-match status
- Customer-risk rating
- Brief KYC explanation

Rules:
1. Use only evidence returned by the tool.
2. Preserve the exact KYC values returned by the tool.
3. Do not perform fraud scoring.
4. Do not make a final compliance decision.
5. Do not claim that a sanctions match is a confirmed legal violation.
6. State that a sanctions match requires human review.
7. Do not invent evidence.
8. Do not return an interim response.
""",
)


compliance_specialist_agent = create_agent(
    model=llm,
    tools=[perform_compliance_review],
    name="compliance_specialist",
    system_prompt="""
You are a Financial Crime Compliance Agent.

You must call perform_compliance_review before answering any
compliance request about a transaction.

Do not describe a future action.
Do not say that you will run a tool next.
Actually invoke the tool and wait for the result.

After the tool returns, provide one completed compliance report
containing:

- Transaction ID
- Compliance recommendation
- SAR-candidate status
- Supporting fraud evidence
- Supporting KYC evidence
- Required human-review statement

Rules:
1. Use only evidence returned by the tool.
2. Preserve the exact recommendation returned by the tool.
3. Preserve the exact SAR-candidate status returned by the tool.
4. Treat SAR status as a candidate recommendation, not a filed SAR.
5. Never claim to have blocked a transaction.
6. Never claim to have filed a SAR.
7. Never claim to have closed an account.
8. Never claim to have contacted the customer.
9. Never claim to have contacted law enforcement.
10. State that consequential actions require human approval.
11. Do not invent evidence.
12. Do not return an interim response.
""",
)


# =========================================================
# RESPONSE HELPER
# =========================================================

def get_final_text(result: Dict[str, Any]) -> str:
    """
    Extract the final natural-language response from an agent result.
    """
    messages = result.get("messages", [])

    if not messages:
        return "The agent returned no response."

    final_message = messages[-1]

    text = getattr(final_message, "text", "")

    if text:
        return str(text)

    content = getattr(final_message, "content", "")

    if isinstance(content, str):
        return content

    return str(content)


# =========================================================
# AGENT EXECUTION FUNCTIONS
# =========================================================

def run_fraud_agent(transaction_id: str) -> str:
    """
    Ask the Fraud Agent to investigate one transaction.
    """
    result = fraud_specialist_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Complete a fraud-risk investigation for "
                        f"transaction {transaction_id}. "
                        f"Use the available fraud-investigation tool "
                        f"before returning the final report."
                    ),
                }
            ]
        }
    )

    return get_final_text(result)


def run_kyc_agent(transaction_id: str) -> str:
    """
    Ask the KYC Agent to review the transaction's customer.
    """
    result = kyc_specialist_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Complete the KYC and sanctions review for "
                        f"transaction {transaction_id}. "
                        f"Use the available KYC-review tool before "
                        f"returning the final report."
                    ),
                }
            ]
        }
    )

    return get_final_text(result)


def run_compliance_agent(transaction_id: str) -> str:
    """
    Ask the Compliance Agent to provide a recommendation.
    """
    result = compliance_specialist_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Complete a compliance review for transaction "
                        f"{transaction_id}. Use the available compliance "
                        f"tool before returning the final report."
                    ),
                }
            ]
        }
    )

    return get_final_text(result)