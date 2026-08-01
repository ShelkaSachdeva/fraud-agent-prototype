from app.a2a.agent_cards import AgentCard, find_agent_card_by_skill
from app.agents.registry import AgentRegistry


class AgentDiscovery:
    """
    Simplified A2A-style agent discovery service.

    It uses agent cards to identify which agent supports a skill,
    then retrieves the actual agent instance from the registry.
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def discover_card(self, skill: str) -> AgentCard:
        """
        Find the metadata card for an agent that supports the skill.
        """

        agent_card = find_agent_card_by_skill(skill)

        if agent_card is None:
            raise LookupError(
                f"No agent card was found for skill '{skill}'."
            )

        return agent_card

    def discover_agent(self, skill: str):
        """
        Find the actual registered agent instance for the skill.
        """

        # First confirm that an agent card advertises this skill.
        self.discover_card(skill)

        # Then retrieve the working agent from the registry.
        return self.registry.discover(skill)