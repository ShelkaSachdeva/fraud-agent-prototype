from typing import List, Set

from app.models import FraudResult, Transaction


class FraudAgent:
    """
    Deterministic fraud-risk engine.

    Evaluates a transaction using transparent, explainable rules.
    This class does not use an LLM and does not autonomously take
    actions such as blocking a transaction.
    """

    HIGH_RISK_MERCHANTS: Set[str] = {
        "Crypto Exchange",
        "Online Casino",
        "Wire Transfer Service",
        "Gift Card Marketplace",
    }

    def investigate(self, transaction: Transaction) -> FraudResult:
        """
        Analyze a transaction and return its fraud-risk assessment.

        Args:
            transaction: Transaction to evaluate.

        Returns:
            FraudResult containing:
            - risk score,
            - risk level,
            - detected fraud signals.
        """
        risk_score = 0
        fraud_signals: List[str] = []

        # -------------------------------------------------
        # Rule 1: Transaction amount
        # -------------------------------------------------
        if transaction.amount >= 10_000:
            risk_score += 30
            fraud_signals.append("High-value transaction")

        elif transaction.amount >= 5_000:
            risk_score += 15
            fraud_signals.append(
                "Moderately high transaction amount"
            )

        # -------------------------------------------------
        # Rule 2: Device risk
        # -------------------------------------------------
        if transaction.is_new_device:
            risk_score += 20
            fraud_signals.append(
                "Transaction initiated from a new device"
            )

        # -------------------------------------------------
        # Rule 3: Transaction velocity
        # -------------------------------------------------
        if transaction.velocity_last_hour >= 6:
            risk_score += 30
            fraud_signals.append(
                "Unusually high number of transactions "
                "in the last hour"
            )

        elif transaction.velocity_last_hour >= 3:
            risk_score += 15
            fraud_signals.append(
                "Elevated number of transactions "
                "in the last hour"
            )

        # -------------------------------------------------
        # Rule 4: Merchant risk
        # -------------------------------------------------
        if transaction.merchant in self.HIGH_RISK_MERCHANTS:
            risk_score += 20
            fraud_signals.append(
                "Transaction involves higher-risk merchant: "
                f"{transaction.merchant}"
            )

        # Risk score must remain between 0 and 100.
        risk_score = min(risk_score, 100)

        risk_level = self._determine_risk_level(risk_score)

        if not fraud_signals:
            fraud_signals.append(
                "No significant fraud indicators detected"
            )

        return FraudResult(
            risk_score=risk_score,
            risk_level=risk_level,
            fraud_signals=fraud_signals,
        )

    @staticmethod
    def _determine_risk_level(risk_score: int) -> str:
        """
        Convert the numeric risk score into a risk category.
        """
        if risk_score >= 70:
            return "HIGH"

        if risk_score >= 40:
            return "MEDIUM"

        return "LOW"