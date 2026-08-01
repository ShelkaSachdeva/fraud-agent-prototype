import asyncio
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.specialist_agents import (
    investigate_transaction_fraud,
    perform_compliance_review,
    perform_kyc_review,
)

router = APIRouter()


class InvestigationRequest(BaseModel):
    transaction_id: str


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@router.post("/api/investigations")
def run_investigation(
    request: InvestigationRequest,
) -> Dict[str, Any]:
    """
    Non-streaming endpoint returning the entire investigation.
    """
    fraud = investigate_transaction_fraud.invoke(
        {"transaction_id": request.transaction_id}
    )

    if not fraud.get("found"):
        return {
            "status": "FAILED",
            "error": fraud.get("error"),
        }

    kyc = perform_kyc_review.invoke(
        {"transaction_id": request.transaction_id}
    )

    if not kyc.get("found"):
        return {
            "status": "FAILED",
            "fraud": fraud,
            "error": kyc.get("error"),
        }

    compliance = perform_compliance_review.invoke(
        {"transaction_id": request.transaction_id}
    )

    return {
        "status": (
            "COMPLETED"
            if compliance.get("found")
            else "FAILED"
        ),
        "transaction_id": request.transaction_id,
        "fraud": fraud,
        "kyc": kyc,
        "compliance": compliance,
        "human_review_required": True,
    }


@router.get("/api/investigations/stream/{transaction_id}")
async def stream_investigation(
    transaction_id: str,
) -> StreamingResponse:
    """
    Stream visible agent progress to the browser using SSE.
    """

    async def event_generator():
        import json

        yield _sse(
            "orchestrator",
            json.dumps(
                {
                    "status": "RUNNING",
                    "message": (
                        "Orchestrator received the investigation "
                        f"request for {transaction_id}."
                    ),
                }
            ),
        )

        await asyncio.sleep(0.5)

        yield _sse(
            "fraud_started",
            json.dumps(
                {
                    "agent": "fraud",
                    "status": "RUNNING",
                    "message": (
                        "Fraud Agent is analyzing transaction "
                        "behavior and risk signals."
                    ),
                }
            ),
        )

        fraud = investigate_transaction_fraud.invoke(
            {"transaction_id": transaction_id}
        )

        yield _sse(
            "fraud_completed",
            json.dumps(
                {
                    "agent": "fraud",
                    "status": (
                        "COMPLETED"
                        if fraud.get("found")
                        else "FAILED"
                    ),
                    "output": fraud,
                }
            ),
        )

        if not fraud.get("found"):
            yield _sse(
                "investigation_failed",
                json.dumps(
                    {
                        "status": "FAILED",
                        "error": fraud.get("error"),
                    }
                ),
            )
            return

        await asyncio.sleep(0.5)

        yield _sse(
            "kyc_started",
            json.dumps(
                {
                    "agent": "kyc",
                    "status": "RUNNING",
                    "message": (
                        "KYC Agent is verifying identity, sanctions "
                        "status, and customer risk."
                    ),
                }
            ),
        )

        kyc = perform_kyc_review.invoke(
            {"transaction_id": transaction_id}
        )

        yield _sse(
            "kyc_completed",
            json.dumps(
                {
                    "agent": "kyc",
                    "status": (
                        "COMPLETED"
                        if kyc.get("found")
                        else "FAILED"
                    ),
                    "output": kyc,
                }
            ),
        )

        if not kyc.get("found"):
            yield _sse(
                "investigation_failed",
                json.dumps(
                    {
                        "status": "FAILED",
                        "error": kyc.get("error"),
                    }
                ),
            )
            return

        await asyncio.sleep(0.5)

        yield _sse(
            "compliance_started",
            json.dumps(
                {
                    "agent": "compliance",
                    "status": "RUNNING",
                    "message": (
                        "Compliance Agent is reviewing the fraud and "
                        "KYC evidence."
                    ),
                }
            ),
        )

        compliance = perform_compliance_review.invoke(
            {"transaction_id": transaction_id}
        )

        yield _sse(
            "compliance_completed",
            json.dumps(
                {
                    "agent": "compliance",
                    "status": (
                        "COMPLETED"
                        if compliance.get("found")
                        else "FAILED"
                    ),
                    "output": compliance,
                }
            ),
        )

        if not compliance.get("found"):
            yield _sse(
                "investigation_failed",
                json.dumps(
                    {
                        "status": "FAILED",
                        "error": compliance.get("error"),
                    }
                ),
            )
            return

        yield _sse(
            "investigation_completed",
            json.dumps(
                {
                    "status": "COMPLETED",
                    "transaction_id": transaction_id,
                    "summary": {
                        "fraud": fraud.get("fraud_result"),
                        "kyc": kyc.get("kyc_result"),
                        "compliance": compliance.get(
                            "compliance_result"
                        ),
                        "human_review_required": True,
                    },
                }
            ),
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
