import asyncio
import os
import shutil
from pathlib import Path
import sys
from typing import cast, List
from dotenv import load_dotenv
from tools import get_weather
from agent_framework import ChatMessage, Role, SequentialBuilder, WorkflowOutputEvent
from agent_framework.github import GitHubCopilotAgent
from agent_framework.azure import AzureOpenAIChatClient
from copilot.types import PermissionRequest, PermissionRequestResult
from copilot.types import MCPServerConfig
from azure.identity import AzureCliCredential
from capabilities import (
    Capability,
    CapabilityType,
    AgentCapabilities,
    capability_registry,
)


def ensure_copilot_available():
    copilot_path = os.environ.get("COPILOT_PATH")
    if copilot_path:
        if os.path.isfile(copilot_path) and os.access(copilot_path, os.X_OK):
            return copilot_path
        raise SystemExit(f"COPILOT_PATH is set but not executable: {copilot_path}")

    path = shutil.which("copilot")
    if path:
        return path

    raise SystemExit(
        "copilot executable not found. Install the Copilot CLI and ensure 'copilot' is on PATH,"
        " or set the COPILOT_PATH environment variable to the copilot binary."
    )


# Use python-dotenv to load environment variables from a .env file if present.
def load_env_file(filename: str = ".env"):
    env_path = Path(__file__).resolve().parent / filename
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


def prompt_permission(
    request: PermissionRequest, context: dict[str, str]
) -> PermissionRequestResult:
    kind = request.get("kind", "unknown")
    print(f"\n[Permission Request: {kind}]")

    response = input("Approve? (y/n): ").strip().lower()
    if response in ("y", "yes"):
        return PermissionRequestResult(kind="approved")
    return PermissionRequestResult(kind="denied-interactively-by-user")


def register_agent_capabilities(
    agent_name: str, agent_id: str, caps: List[Capability]
) -> None:
    """Register an agent's capabilities in the UCP registry."""
    agent_caps = AgentCapabilities(agent_name=agent_name, agent_id=agent_id)
    for cap in caps:
        agent_caps.add_capability(cap)
    capability_registry.register_agent(agent_caps)


def check_azure_config() -> bool:
    """Check if Azure OpenAI is properly configured."""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME",
    ]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(
            f"\n[SKIP] Azure Workflow demo - Missing environment variables: {', '.join(missing)}"
        )
        print("       To enable, set these in your .env or environment:")
        for var in required_vars:
            print(f"       - {var}")
        return False
    return True


async def demo_workflow():
    """Run a sequential workflow: Azure OpenAI writer -> GitHub Copilot reviewer."""
    print("\n=== Starting Workflow Demo: Writer → Reviewer ===\n")

    # Check Azure configuration before attempting to create client
    if not check_azure_config():
        return

    try:
        # Register writer capabilities
        writer_caps = [
            Capability(
                name="copywrite",
                capability_type=CapabilityType.COPYWRITING,
                description="Generate concise marketing copy and taglines",
                parameters={"prompt": "string"},
                required_permissions=["content_generation"],
            )
        ]
        register_agent_capabilities("writer", "agent-writer-001", writer_caps)

        # Register reviewer capabilities
        reviewer_caps = [
            Capability(
                name="review_content",
                capability_type=CapabilityType.REVIEW,
                description="Review and provide feedback on content",
                parameters={"content": "string"},
                required_permissions=["content_review"],
            )
        ]
        register_agent_capabilities("reviewer", "agent-reviewer-001", reviewer_caps)

        # Create an Azure OpenAI agent as a copywriter
        chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

        writer = chat_client.as_agent(
            instructions="You are a concise copywriter. Provide a single, punchy marketing sentence based on the prompt.",
            name="writer",
        )

        # Create a GitHub Copilot agent as a reviewer
        reviewer = GitHubCopilotAgent(
            default_options={
                "instructions": "You are a thoughtful reviewer. Give brief feedback on the previous assistant message."
            },
            name="reviewer",
        )

        # Build a sequential workflow: writer -> reviewer
        workflow = SequentialBuilder().participants([writer, reviewer]).build()

        # Run the workflow with streaming output
        async for event in workflow.run_stream(
            "Write a tagline for a budget-friendly electric bike."
        ):
            if isinstance(event, WorkflowOutputEvent):
                messages = cast(list[ChatMessage], event.data)
                for msg in messages:
                    name = msg.author_name or (
                        "assistant" if msg.role == Role.ASSISTANT else "user"
                    )
                    print(f"[{name}]: {msg.text}\n")
    except Exception as e:
        print(f"[ERROR] Workflow demo failed: {e}")


async def demo_copilot_with_tools():
    """Run the original Copilot agent with MCP servers and weather tools."""
    print("\n=== Starting Copilot Demo: Tools & Filesystem ===\n")

    # Register Copilot agent capabilities
    copilot_caps = [
        Capability(
            name="get_weather",
            capability_type=CapabilityType.WEATHER,
            description="Get weather information for a location",
            parameters={"location": "string"},
            required_permissions=["weather_access"],
        ),
        Capability(
            name="list_files",
            capability_type=CapabilityType.FILESYSTEM,
            description="List files in the filesystem",
            parameters={"directory": "string"},
            required_permissions=["filesystem_access"],
        ),
        Capability(
            name="analysis",
            capability_type=CapabilityType.ANALYSIS,
            description="Analyze and provide insights on data or content",
            parameters={"content": "string"},
            required_permissions=["analysis"],
        ),
    ]
    register_agent_capabilities("copilot", "agent-copilot-001", copilot_caps)

    mcp_servers: dict[str, MCPServerConfig] = {
        # Local stdio server
        "filesystem": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "tools": ["*"],
        },
        # Remote HTTP server
        "microsoft-learn": {
            "type": "http",
            "url": "https://learn.microsoft.com/api/mcp",
            "tools": ["*"],
        },
    }

    agent = GitHubCopilotAgent(
        default_options={
            "instructions": "You are a helpful assistant with weather tools and filesystem access.",
            "on_permission_request": prompt_permission,
            "mcp_servers": mcp_servers,
            "default_mcp_server": "filesystem",
        },
        tools=[get_weather],
    )

    async with agent:
        thread = agent.get_new_thread()

        result = await agent.run(
            "List the Python files in the current directory", thread=thread
        )
        print(result)

        result = await agent.run("What is the weather like in Seattle?", thread=thread)
        print(result)

        result = await agent.run("What about New York?", thread=thread)
        print(result)


async def demo_ucp_discovery():
    """Demonstrate UCP capability discovery and management."""
    print("\n=== UCP Capability Discovery Demo ===\n")

    # Print the registry
    capability_registry.print_registry()

    # Demonstrate capability queries
    print("=== Capability Queries ===\n")

    # Find agents that can provide weather
    weather_agents = capability_registry.get_all_capabilities_by_type(
        CapabilityType.WEATHER
    )
    print(f"Agents providing WEATHER capabilities: {list(weather_agents.keys())}")

    # Find agents that can review
    review_agents = capability_registry.get_all_capabilities_by_type(
        CapabilityType.REVIEW
    )
    print(f"Agents providing REVIEW capabilities: {list(review_agents.keys())}")

    # Check if specific agent can perform capability
    has_weather = capability_registry.can_agent_perform(
        "agent-copilot-001", "get_weather"
    )
    print(f"Can Copilot agent get weather? {has_weather}")

    # Find agent for capability
    reviewer_id = capability_registry.find_agent_for_capability("review_content")
    print(f"Agent that can review content: {reviewer_id}")


async def main():
    # Load .env (if present) so users can set COPILOT_PATH there
    load_env_file()

    ensure_copilot_available()

    # Run demos
    print("\n" + "=" * 60)
    print("MULTI-AGENT APPLICATION WITH UCP CAPABILITIES")
    print("=" * 60)

    await demo_workflow()
    await demo_copilot_with_tools()
    await demo_ucp_discovery()


if __name__ == "__main__":
    asyncio.run(main())
