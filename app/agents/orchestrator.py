from app.a2a.discovery import AgentDiscovery
from app.agents.compliance_agent import ComplianceAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.kyc_agent import KYCAgent
from app.agents.registry import AgentRegistry
from app.data.dummy_data import get_transaction
from app.models import InvestigationReport


class OrchestratorAgent:
    """
    Coordinates the fraud, KYC, and compliance agents
    using skill-based discovery.
    """

    def __init__(self) -> None:
        self.registry = AgentRegistry()

        self.registry.register(
            "fraud-investigation",
            FraudAgent(),
        )

        self.registry.register(
            "kyc-verification",
            KYCAgent(),
        )

        self.registry.register(
            "compliance-review",
            ComplianceAgent(),
        )

        self.discovery = AgentDiscovery(self.registry)

    def investigate(self, transaction_id: str) -> InvestigationReport:
        transaction = get_transaction(transaction_id)

        if transaction is None:
            raise ValueError(
                f"Transaction '{transaction_id}' was not found."
            )

        fraud_agent = self.discovery.discover_agent(
            "fraud-investigation"
        )

        kyc_agent = self.discovery.discover_agent(
            "kyc-verification"
        )

        compliance_agent = self.discovery.discover_agent(
            "compliance-review"
        )

        fraud_result = fraud_agent.investigate(transaction)
        kyc_result = kyc_agent.verify(transaction)

        compliance_result = compliance_agent.review(
            transaction=transaction,
            fraud_result=fraud_result,
            kyc_result=kyc_result,
        )

        return InvestigationReport(
            transaction=transaction,
            fraud=fraud_result,
            kyc=kyc_result,
            compliance=compliance_result,
        )