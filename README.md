# AI-agentics

AI-agentics is a Python 3 starter project for building agentic workflows and experiments.

## MQTT agent team

The Manager, GUI operator, and backend operator communicate through an MQTT broker (Mosquitto is supported). They use MQTT topics for task requests, GUI/backend coordination, and reports; there is no in-process message bus.

Install the Python package and its MQTT client dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Start a Mosquitto broker separately. The default connection is `localhost:1883`; configure a different broker with `MQTT_HOST` and `MQTT_PORT`, or pass `--mqtt-host` and `--mqtt-port` to a command.

In separate terminals, start both operators:

```bash
python -m ai_agentics agent --role gui_operator
python -m ai_agentics agent --role backend_operator
```

Then submit a task with the Manager:

```bash
python -m ai_agentics team --task "Plan a settings page and its API"
```

The Manager publishes task messages, the GUI operator asks the backend operator for an API contract over MQTT, and the Manager collects the operators' reports. The current agents generate planning suggestions; they do not control a real GUI, modify backend services, or invoke external tools.

## Other commands

```bash
python -m ai_agentics --help
python -m ai_agentics hello --name "Developer"
python -m unittest discover -s tests -v
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
│       ├── agent_team.py
│       └── cli.py
└── tests/
    ├── test_agent_team.py
    └── test_cli.py
```
