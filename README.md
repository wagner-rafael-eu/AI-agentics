# AI-agentics

AI-agentics is a Python 3 starter project for building agentic workflows and experiments.

## Features

- Python 3 project structure
- CLI entry point via `python -m ai_agentics`
- In-process three-agent team: Manager, GUI operator, and backend operator
- Basic test suite setup

## Quick start

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the project in editable mode:
   ```bash
   pip install -e .
   ```

3. Try the CLI and agent team:
   ```bash
   python -m ai_agentics --help
   python -m ai_agentics hello --name "Developer"
   python -m ai_agentics team --task "Plan a settings page and its API"
   ```

The team communicates through an in-memory message bus. The Manager delegates the task, the GUI operator asks the backend operator about integration, and the Manager collects their plans. These are coordination examples only: the operators do not control a real GUI, execute backend changes, or invoke external services.

## Project layout

```text
AI-agentics/
├── README.md
├── pyproject.toml
├── Makefile
├── src/
│   └── ai_agentics/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agent_team.py
│       └── cli.py
└── tests/
    ├── test_agent_team.py
    └── test_cli.py
```

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

Or use the included shortcut:

```bash
make test
```
