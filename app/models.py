from typing import List

from pydantic import BaseModel


# -----------------------------------------------------
# Transaction Model
# -----------------------------------------------------

class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    country: str
    merchant: str
    is_new_device: bool
    velocity_last_hour: int


# -----------------------------------------------------
# Fraud Agent Response
# -----------------------------------------------------

class FraudResult(BaseModel):
    risk_score: int
    risk_level: str
    fraud_signals: List[str]


# -----------------------------------------------------
# KYC Agent Response
# -----------------------------------------------------

class KYCResult(BaseModel):
    identity_verified: bool
    sanctions_match: bool
    customer_risk: str


# -----------------------------------------------------
# Compliance Agent Response
# -----------------------------------------------------

class ComplianceResult(BaseModel):
    recommendation: str
    sar_candidate: bool
    summary: str


# -----------------------------------------------------
# Final Investigation Report
# -----------------------------------------------------

class InvestigationReport(BaseModel):
    transaction: Transaction
    fraud: FraudResult
    kyc: KYCResult
    compliance: ComplianceResult