# GitHub Copilot Agent with UCP Capabilities

A multi-agent application demonstrating **GitHub Copilot Agent**, **Azure OpenAI**, and **UCP (Unified Control Protocol)** for advanced agent orchestration and capability management.

## Features

- **Multi-Agent Workflows**: Sequential workflows with Azure OpenAI (copywriter) and GitHub Copilot (reviewer)
- **MCP Servers**: Model Context Protocol integration for filesystem and knowledge base access
- **Tool Integration**: Custom tools like weather information
- **UCP Capability Discovery**: Register, discover, and query agent capabilities
- **Permission Management**: Interactive permission prompts for sensitive operations

## Setup

### Prerequisites

1. **Copilot CLI** - Required for running GitHub Copilot agents
   - Install and ensure `copilot` is on your `PATH`, or
   - Set `COPILOT_PATH` in `.env` file

2. **Python 3.8+**

3. **Azure Credentials** (for workflow demo)
   - Configure `AzureCliCredential` via `az login`

### Installation

Create a `.env` file next to `agent.py`:

```bash
COPILOT_PATH=/path/to/copilot
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python agent.py
```

## Architecture

### Agents

1. **Writer Agent** (Azure OpenAI)
   - Capabilities: `copywrite`
   - Generates marketing copy and taglines

2. **Reviewer Agent** (GitHub Copilot)
   - Capabilities: `review_content`
   - Reviews and provides feedback

3. **Copilot Agent** (GitHub Copilot with Tools)
   - Capabilities: `get_weather`, `list_files`, `analysis`
   - Integrates MCP servers and custom tools

### UCP (Unified Control Protocol)

The application includes a capability management system:

```python
from capabilities import capability_registry, CapabilityType

# Register agent capabilities
register_agent_capabilities("agent_name", "agent_id", [capabilities])

# Discover capabilities
registry = capability_registry.discover_capabilities()

# Query specific capabilities
weather_agents = capability_registry.get_all_capabilities_by_type(CapabilityType.WEATHER)

# Find agent for capability
agent_id = capability_registry.find_agent_for_capability("get_weather")
```

### Capability Types

- `WEATHER`: Weather information services
- `FILESYSTEM`: File system operations
- `COPYWRITING`: Content generation
- `REVIEW`: Content review and feedback
- `ANALYSIS`: Data analysis and insights
- `ORCHESTRATION`: Workflow orchestration

## File Structure

```
.
├── agent.py              # Main application with agent demos
├── capabilities.py       # UCP capability management system
├── tools.py             # Custom tools (e.g., weather)
├── requirements.txt     # Python dependencies
├── .env                 # Configuration (COPILOT_PATH, etc.)
└── README.md           # This file
```

## Demos Included

1. **Workflow Demo**: Sequential writer → reviewer workflow
2. **Copilot Tools Demo**: Filesystem listing and weather queries
3. **UCP Discovery Demo**: Capability registry and queries

## Example Usage

```python
from capabilities import Capability, CapabilityType, register_agent_capabilities

# Define capabilities
my_caps = [
    Capability(
        name="my_tool",
        capability_type=CapabilityType.ANALYSIS,
        description="My custom analysis tool",
        parameters={"data": "string"},
        required_permissions=["analysis"],
    )
]

# Register agent
register_agent_capabilities("my_agent", "agent-001", my_caps)

# Query capabilities
agent = capability_registry.get_agent_capabilities("agent-001")
print(agent.to_json())
```

## Environment Variables

### Required for Copilot Agent
- `COPILOT_PATH`: Full path to the copilot executable

### Optional for Azure Workflow Demo
To enable the Azure OpenAI workflow demo, set these environment variables in `.env`:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=<your-deployment-name>
COPILOT_PATH=/path/to/copilot
```

If these are not configured, the workflow demo will be gracefully skipped.

### Optional Additional Variables
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_TENANT_ID`: Azure tenant ID

## Troubleshooting

**Error: `[SKIP] Azure Workflow demo - Missing environment variables`**
- This is expected if you haven't configured Azure OpenAI
- To enable Azure workflow demo, add the required environment variables to `.env`
- Otherwise, the application will run the Copilot and UCP demos

**Error: `copilot executable not found`**
- Ensure GitHub Copilot CLI is installed
- Set `COPILOT_PATH` in `.env` to the full path of the copilot binary

**Error: `Azure OpenAI deployment name is required`**
- Set `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` in your `.env` file
- Also ensure `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` are configured

**Error: MCP server connection issues**
- Ensure `npx` and Node.js are installed for the filesystem MCP server
- Check network connectivity for remote HTTP MCP servers

