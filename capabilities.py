"""UCP (Unified Control Protocol) capabilities for multi-agent coordination."""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
import json


class CapabilityType(str, Enum):
    """Types of capabilities agents can expose."""

    WEATHER = "weather"
    FILESYSTEM = "filesystem"
    COPYWRITING = "copywriting"
    REVIEW = "review"
    ANALYSIS = "analysis"
    ORCHESTRATION = "orchestration"


@dataclass
class Capability:
    """Represents a single capability."""

    name: str
    capability_type: CapabilityType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary."""
        return {
            "name": self.name,
            "type": self.capability_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "required_permissions": self.required_permissions,
        }


@dataclass
class AgentCapabilities:
    """Container for all capabilities of an agent."""

    agent_name: str
    agent_id: str
    capabilities: List[Capability] = field(default_factory=list)
    version: str = "1.0"

    def add_capability(self, capability: Capability) -> None:
        """Add a capability to the agent."""
        self.capabilities.append(capability)

    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name."""
        return next((c for c in self.capabilities if c.name == name), None)

    def get_capabilities_by_type(self, cap_type: CapabilityType) -> List[Capability]:
        """Get all capabilities of a specific type."""
        return [c for c in self.capabilities if c.capability_type == cap_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "version": self.version,
            "capabilities": [c.to_dict() for c in self.capabilities],
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class CapabilityRegistry:
    """Registry for managing agent capabilities across the system."""

    def __init__(self):
        """Initialize the capability registry."""
        self.agents: Dict[str, AgentCapabilities] = {}

    def register_agent(self, agent_capabilities: AgentCapabilities) -> None:
        """Register an agent with its capabilities."""
        self.agents[agent_capabilities.agent_id] = agent_capabilities
        print(
            f"[UCP] Registered agent: {agent_capabilities.agent_name} ({agent_capabilities.agent_id})"
        )

    def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilities]:
        """Get capabilities for a specific agent."""
        return self.agents.get(agent_id)

    def get_all_capabilities_by_type(
        self, cap_type: CapabilityType
    ) -> Dict[str, List[Capability]]:
        """Get all capabilities of a type across all agents."""
        result = {}
        for agent_id, agent_caps in self.agents.items():
            caps = agent_caps.get_capabilities_by_type(cap_type)
            if caps:
                result[agent_id] = caps
        return result

    def discover_capabilities(self) -> Dict[str, Any]:
        """Discover all capabilities in the system."""
        return {
            agent_id: agent_caps.to_dict()
            for agent_id, agent_caps in self.agents.items()
        }

    def can_agent_perform(self, agent_id: str, capability_name: str) -> bool:
        """Check if an agent can perform a specific capability."""
        agent_caps = self.get_agent_capabilities(agent_id)
        if not agent_caps:
            return False
        return agent_caps.get_capability(capability_name) is not None

    def find_agent_for_capability(self, capability_name: str) -> Optional[str]:
        """Find an agent that can perform a specific capability."""
        for agent_id, agent_caps in self.agents.items():
            if agent_caps.get_capability(capability_name):
                return agent_id
        return None

    def print_registry(self) -> None:
        """Print a human-readable registry."""
        print("\n=== UCP Capability Registry ===\n")
        if not self.agents:
            print("No agents registered.")
            return

        for agent_id, agent_caps in self.agents.items():
            print(f"Agent: {agent_caps.agent_name} (ID: {agent_id})")
            print(f"Version: {agent_caps.version}")
            if agent_caps.capabilities:
                print("Capabilities:")
                for cap in agent_caps.capabilities:
                    print(f"  - {cap.name} ({cap.capability_type.value})")
                    print(f"    Description: {cap.description}")
                    if cap.required_permissions:
                        print(f"    Requires: {', '.join(cap.required_permissions)}")
            else:
                print("  No capabilities registered.")
            print()


# Global registry instance
capability_registry = CapabilityRegistry()
