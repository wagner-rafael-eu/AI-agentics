# AI-agentics

AI-agentics is a Python 3 project scaffold for building agentic workflows and experiments.

## Features

- Python 3 project structure
- CLI entry point via `python -m ai_agentics`
- Basic test suite setup
- Easy extension for agent logic, APIs, and tooling

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

3. Run the CLI:
   ```bash
   python -m ai_agentics --help
   python -m ai_agentics hello --name "Developer"
   ```

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
│       └── cli.py
└── tests/
    └── test_cli.py
```

## Development

Run tests:

```bash
python -m unittest discover -s tests
```

Or use the included shortcut:

```bash
make test
```
