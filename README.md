# GitHub Copilot Agent

This project expects the `copilot` CLI to be available. You can either:

- Install the Copilot CLI and ensure `copilot` is on your `PATH`, or
- Create a `.env` file next to `agent.py` and set `COPILOT_PATH` to the full path of the `copilot` binary.

Example `.env`:

COPILOT_PATH=/usr/local/bin/copilot

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the agent:

```bash
python agent.py
```
