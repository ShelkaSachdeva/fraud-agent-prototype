from typing import Any


class AgentRegistry:
    """
    Simple in-memory registry used to store and discover agents by skill.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}

    def register(self, skill: str, agent: Any) -> None:
        """
        Register an agent for a specific skill.
        """

        normalized_skill = skill.strip().lower()

        if not normalized_skill:
            raise ValueError("Skill name cannot be empty.")

        self._agents[normalized_skill] = agent

    def discover(self, skill: str) -> Any:
        """
        Find an agent by skill.
        """

        normalized_skill = skill.strip().lower()
        agent = self._agents.get(normalized_skill)

        if agent is None:
            raise LookupError(
                f"No agent is registered for skill '{skill}'."
            )

        return agent

    def list_skills(self) -> list[str]:
        """
        Return all registered skills.
        """

        return sorted(self._agents.keys())