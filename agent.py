import asyncio
import os
import shutil
from pathlib import Path
import sys
from typing import cast
from dotenv import load_dotenv
from tools import get_weather
from agent_framework import ChatMessage, Role, SequentialBuilder, WorkflowOutputEvent
from agent_framework.github import GitHubCopilotAgent
from agent_framework.azure import AzureOpenAIChatClient
from copilot.types import PermissionRequest, PermissionRequestResult
from copilot.types import MCPServerConfig
from azure.identity import AzureCliCredential


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


async def demo_workflow():
    """Run a sequential workflow: Azure OpenAI writer -> GitHub Copilot reviewer."""
    print("\n=== Starting Workflow Demo: Writer → Reviewer ===\n")

    try:
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
        print(f"Workflow demo error (Azure credentials may not be configured): {e}")


async def demo_copilot_with_tools():
    """Run the original Copilot agent with MCP servers and weather tools."""
    print("\n=== Starting Copilot Demo: Tools & Filesystem ===\n")

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


async def main():
    # Load .env (if present) so users can set COPILOT_PATH there
    load_env_file()

    ensure_copilot_available()

    # Run both demos
    await demo_workflow()
    await demo_copilot_with_tools()


if __name__ == "__main__":
    asyncio.run(main())
