from typing import List, Optional

from pydantic import BaseModel


class AgentCard(BaseModel):
    """
    Simplified A2A-style agent card.

    Each card describes:
    - Agent name
    - Agent purpose
    - Supported skills
    - Agent version
    """

    name: str
    description: str
    skills: List[str]
    version: str = "1.0.0"


FRAUD_AGENT_CARD = AgentCard(
    name="Fraud Agent",
    description=(
        "Analyzes transactions using explainable fraud rules "
        "and returns a fraud risk score and fraud indicators."
    ),
    skills=[
        "fraud-investigation",
        "fraud-risk-scoring",
        "transaction-analysis",
    ],
)


KYC_AGENT_CARD = AgentCard(
    name="KYC Agent",
    description=(
        "Performs simulated customer identity verification, "
        "sanctions screening, and customer risk assessment."
    ),
    skills=[
        "kyc-verification",
        "identity-verification",
        "sanctions-screening",
        "customer-risk-assessment",
    ],
)


COMPLIANCE_AGENT_CARD = AgentCard(
    name="Compliance Agent",
    description=(
        "Reviews fraud and KYC findings and produces "
        "a simulated compliance recommendation."
    ),
    skills=[
        "compliance-review",
        "case-escalation",
        "sar-candidate-assessment",
    ],
)


AGENT_CARDS: List[AgentCard] = [
    FRAUD_AGENT_CARD,
    KYC_AGENT_CARD,
    COMPLIANCE_AGENT_CARD,
]


def list_agent_cards() -> List[AgentCard]:
    """
    Return all available agent cards.
    """

    return AGENT_CARDS


def find_agent_card_by_skill(skill: str) -> Optional[AgentCard]:
    """
    Find an agent card that supports the requested skill.

    Returns None when no agent advertises the skill.
    """

    normalized_skill = skill.strip().lower()

    for agent_card in AGENT_CARDS:
        normalized_skills = [
            agent_skill.strip().lower()
            for agent_skill in agent_card.skills
        ]

        if normalized_skill in normalized_skills:
            return agent_card

    return None