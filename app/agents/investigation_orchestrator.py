from typing import Any, Dict

from app.agents.specialist_agents import (
    investigate_transaction_fraud,
    perform_compliance_review,
    perform_kyc_review,
)


def run_autonomous_investigation(
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Execute a bounded, deterministic multi-agent investigation.

    The orchestrator owns sequencing and dependencies.
    Specialist tools perform the trusted analysis.
    """

    steps = []

    fraud_output = investigate_transaction_fraud.invoke(
        {"transaction_id": transaction_id}
    )

    steps.append(
        {
            "agent": "fraud",
            "status": (
                "COMPLETED"
                if fraud_output.get("found")
                else "FAILED"
            ),
            "output": fraud_output,
        }
    )

    if not fraud_output.get("found"):
        return {
            "status": "FAILED",
            "transaction_id": transaction_id,
            "steps": steps,
            "error": fraud_output.get(
                "error",
                "Fraud investigation failed.",
            ),
        }

    kyc_output = perform_kyc_review.invoke(
        {"transaction_id": transaction_id}
    )

    steps.append(
        {
            "agent": "kyc",
            "status": (
                "COMPLETED"
                if kyc_output.get("found")
                else "FAILED"
            ),
            "output": kyc_output,
        }
    )

    if not kyc_output.get("found"):
        return {
            "status": "FAILED",
            "transaction_id": transaction_id,
            "steps": steps,
            "error": kyc_output.get(
                "error",
                "KYC investigation failed.",
            ),
        }

    compliance_output = perform_compliance_review.invoke(
        {"transaction_id": transaction_id}
    )

    steps.append(
        {
            "agent": "compliance",
            "status": (
                "COMPLETED"
                if compliance_output.get("found")
                else "FAILED"
            ),
            "output": compliance_output,
        }
    )

    if not compliance_output.get("found"):
        return {
            "status": "FAILED",
            "transaction_id": transaction_id,
            "steps": steps,
            "error": compliance_output.get(
                "error",
                "Compliance review failed.",
            ),
        }

    compliance_result = compliance_output.get(
        "compliance_result",
        {},
    )

    return {
        "status": "COMPLETED",
        "transaction_id": transaction_id,
        "steps": steps,
        "summary": {
            "fraud": fraud_output.get("fraud_result"),
            "kyc": kyc_output.get("kyc_result"),
            "compliance": compliance_result,
            "human_review_required": True,
        },
    }
