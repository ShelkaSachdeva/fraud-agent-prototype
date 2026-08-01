from app.models import ComplianceResult, FraudResult, KYCResult, Transaction


class ComplianceAgent:
    """
    Dummy compliance agent for learning purposes.

    It reviews fraud and KYC results, then produces an explainable
    recommendation. It does not file a real SAR or make real compliance decisions.
    """

    def review(
        self,
        transaction: Transaction,
        fraud_result: FraudResult,
        kyc_result: KYCResult,
    ) -> ComplianceResult:
        reasons: list[str] = []
        sar_candidate = False

        # Highest-priority rule: sanctions match
        if kyc_result.sanctions_match:
            recommendation = "BLOCK_AND_ESCALATE"
            sar_candidate = True
            reasons.append("Potential sanctions match requires immediate escalation")

        # High fraud risk
        elif fraud_result.risk_level == "HIGH":
            recommendation = "ESCALATE_FOR_MANUAL_REVIEW"
            sar_candidate = True
            reasons.append("Fraud risk score is high")

        # Identity could not be verified
        elif not kyc_result.identity_verified:
            recommendation = "HOLD_FOR_IDENTITY_REVIEW"
            reasons.append("Customer identity could not be verified")

        # Combined medium-risk indicators
        elif (
            fraud_result.risk_level == "MEDIUM"
            and kyc_result.customer_risk in {"MEDIUM", "HIGH"}
        ):
            recommendation = "ENHANCED_DUE_DILIGENCE"
            reasons.append("Combined fraud and customer-risk indicators require review")

        else:
            recommendation = "APPROVE_WITH_MONITORING"
            reasons.append("No critical compliance indicators detected")

        # Additional review context
        if transaction.amount >= 10_000:
            reasons.append("Transaction amount is $10,000 or more")

        if transaction.is_new_device:
            reasons.append("Transaction originated from a new device")

        if kyc_result.customer_risk == "HIGH":
            reasons.append("Customer has a high KYC risk rating")

        summary = (
            f"Transaction {transaction.transaction_id} received compliance action "
            f"{recommendation}. "
            + " ".join(reasons)
        )

        return ComplianceResult(
            recommendation=recommendation,
            sar_candidate=sar_candidate,
            summary=summary,
        )