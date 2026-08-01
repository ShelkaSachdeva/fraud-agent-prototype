from app.data.dummy_data import get_customer
from app.models import KYCResult, Transaction


class KYCAgent:
    """
    Dummy KYC agent for learning purposes.

    Simulates:
    - Identity verification
    - Sanctions screening
    - Customer risk assessment
    """

    def verify(self, transaction: Transaction) -> KYCResult:
        customer = get_customer(transaction.customer_id)

        if customer is None:
            return KYCResult(
                identity_verified=False,
                sanctions_match=False,
                customer_risk="UNKNOWN",
            )

        return KYCResult(
            identity_verified=customer["identity_verified"],
            sanctions_match=customer["sanctions_match"],
            customer_risk=customer["customer_risk"],
        )