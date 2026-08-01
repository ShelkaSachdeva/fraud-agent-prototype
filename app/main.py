from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agents.orchestrator import OrchestratorAgent
from app.data.dummy_data import get_transaction, transactions
from app.routes.investigation_routes import (
    router as investigation_router,
)


app = FastAPI(
    title="Fraud Investigation Agent",
    description=(
        "Multi-agent fraud, KYC, and compliance investigation API"
    ),
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


# ---------------------------------------------------------
# API routers
# ---------------------------------------------------------

app.include_router(investigation_router)


# ---------------------------------------------------------
# Static frontend
# ---------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# ---------------------------------------------------------
# Existing deterministic orchestrator
# ---------------------------------------------------------

orchestrator = OrchestratorAgent()


# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------

@app.get("/", include_in_schema=False)
def dashboard():
    """
    Display the user-facing autonomous investigation dashboard.
    """
    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Frontend file was not found at "
                f"{index_file}"
            ),
        )

    return FileResponse(index_file)


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "fraud-investigation-agent",
        "frontend": "available",
        "autonomous_agents": "available",
    }


# ---------------------------------------------------------
# Transaction endpoints
# ---------------------------------------------------------

@app.get("/transactions")
def list_transactions():
    return transactions


@app.get("/transactions/{transaction_id}")
def transaction_details(transaction_id: str):
    transaction = get_transaction(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} was not found.",
        )

    return transaction


# ---------------------------------------------------------
# Existing investigation endpoint
# ---------------------------------------------------------

@app.post("/investigate/{transaction_id}")
def investigate_transaction(transaction_id: str):
    """
    Run the existing deterministic orchestrator investigation.
    """
    transaction = get_transaction(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} was not found.",
        )

    try:
        return orchestrator.investigate(transaction_id)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed: {str(exc)}",
        ) from exc