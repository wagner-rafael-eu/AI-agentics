# AI-agentics

AI-agentics is a Python 3.11+ starter project demonstrating a small, MQTT-based agent workflow. A Manager publishes a task, a GUI operator and a backend operator exchange planning messages through an MQTT broker, and the Manager collects their reports.

> **Scope:** The agents currently produce example planning text. They do not use an LLM, execute code, control a graphical interface, or change backend services. This repository is a development scaffold, not a production-ready agent platform.

## Agents and message flow

- **Manager** — creates a task ID, publishes the task to both operator request topics, and waits for three report types.
- **GUI operator** — asks the backend operator for API and UI-state guidance, then reports an integrated GUI plan.
- **Backend operator** — reports a backend plan and replies to the GUI operator with suggested API-contract guidance.

Messages are JSON, published with MQTT QoS 1, under the `ai_agentics` topic prefix:

| Topic | Purpose |
| --- | --- |
| `ai_agentics/requests/gui_operator` | Manager task requests for the GUI operator |
| `ai_agentics/requests/backend_operator` | Manager tasks and GUI questions for the backend operator |
| `ai_agentics/feedback/gui_operator` | Backend guidance delivered to the GUI operator |
| `ai_agentics/reports/{task_id}` | Operator reports collected by the Manager |

## Requirements

- Python 3.11 or later
- A running MQTT 3.1.1-compatible broker, such as Mosquitto
- `paho-mqtt` (installed from the project dependencies)

## Install

```bash
git clone https://github.com/wagner-rafael-eu/AI-agentics.git
cd AI-agentics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

On Windows PowerShell, activate the virtual environment with `.venv\\Scripts\\Activate.ps1`.

## Run with Mosquitto

Start Mosquitto in its own terminal using your installation's configuration. For a local development broker, the default connection settings used by the app are `localhost:1883`.

In separate terminals, start the two operator processes:

```bash
python -m ai_agentics agent --role gui_operator
python -m ai_agentics agent --role backend_operator
```

Submit a task from another terminal:

```bash
python -m ai_agentics team --task "Plan a settings page and its API"
```

The Manager waits up to 30 seconds for the operator reports by default. Change the timeout or broker endpoint as needed:

```bash
python -m ai_agentics team \
  --task "Plan a dashboard" \
  --mqtt-host localhost \
  --mqtt-port 1883 \
  --timeout 45
```

The agent commands also accept `--mqtt-host` and `--mqtt-port`. Alternatively, set `MQTT_HOST` and `MQTT_PORT` in the environment. CLI options take precedence; defaults are `localhost` and `1883`.

## CLI reference

```text
python -m ai_agentics --help
python -m ai_agentics status
python -m ai_agentics hello [--name NAME]
python -m ai_agentics agent --role {gui_operator,backend_operator} [--mqtt-host HOST] [--mqtt-port PORT]
python -m ai_agentics team --task TASK [--mqtt-host HOST] [--mqtt-port PORT] [--timeout SECONDS]
```

`status` is a local readiness message; it does not check broker connectivity. The `agent` command runs continuously until stopped.

## Tests

Install the package, then run the test suite:

```bash
python -m unittest discover -s tests -v
```

Or use the Makefile shortcut:

```bash
make test
```

The current tests cover message-routing behavior and basic CLI commands. They do not require a live broker and are not end-to-end MQTT integration tests.

## Security and production considerations

The current code is a basic MQTT demonstration. It does **not** implement MQTT authentication, TLS/MQTTS, broker ACLs, a whitelist agent, message-signature verification, or persistent audit logging. Message fields such as task IDs are routing data, not proof of identity. Do not expose an unauthenticated development broker to an untrusted network or use this example to process sensitive data.

For a real deployment, configure broker-side authentication and topic ACLs, use TLS with certificate validation, protect credentials and keys, define client-specific permissions, and add security monitoring and update procedures. Evaluate applicable obligations—including the EU Cyber Resilience Act—with qualified legal and security professionals; this project makes no claim of CRA compliance or certification.

See [FUTURE_TASKS.md](FUTURE_TASKS.md) for the planned security, operations, testing, and product backlog.

## Project layout

```text
AI-agentics/
├── FUTURE_TASKS.md
├── README.md
├── Makefile
├── pyproject.toml
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
