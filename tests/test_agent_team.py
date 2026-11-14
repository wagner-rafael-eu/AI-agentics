# AI-agentics

AI-agentics is a Python 3 project that demonstrates a coordinated multi-agent system using MQTT communication, role-based agents, and a dedicated allow-list security agent. The project is designed as an example and learning scaffold for secure message routing in agentic systems.

## What this project contains

- Manager agent: coordinates work and gathers results
- GUI operator: plans the user-facing workflow and integrates the backend contract
- Backend operator: defines backend responsibilities and API contract guidance
- Whitelist agent: enforces an allow-list of authorized MQTT client IDs
- MQTT message flow: tasks are exchanged over broker topics instead of in-memory queues

## Security model

This project follows a deny-by-default pattern for MQTT access control:

- each client must present an authorized identifier
- the whitelist agent validates client IDs
- unknown IDs are rejected with a `security_denied` message
- all messages include a `source_id` when emitted by the service layer
- the architecture is designed to support secure-by-default patterns and audit-friendly behavior

Important note:

This is a technical model for secure architecture and does not constitute a legal certification under the EU Cyber Resilience Act (CRA). For production deployment, confirm the exact regulatory obligations and technical controls required for your product and region.

## MQTT topic model

The current topic structure is simple and explicit:

- `ai_agentics/requests/gui_operator`
- `ai_agentics/requests/backend_operator`
- `ai_agentics/feedback/gui_operator`
- `ai_agentics/reports/{task_id}`
- `ai_agentics/security/validate`
- `ai_agentics/security/approved`
- `ai_agentics/security/denied`
- `ai_agentics/security/whitelist`

This makes it easy to inspect the message flow in a broker like Mosquitto.

## Default authorized MQTT client IDs

The built-in allow-list includes:

- `ai-agentics-manager`
- `ai-agentics-gui_operator`
- `ai-agentics-backend_operator`
- `ai-agentics-whitelist_agent`

You can extend this list via:

- `--mqtt-authorized-ids`
- `MQTT_AUTHORIZED_IDS`

## Quick start

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the project:

   ```bash
   pip install -e .
   ```

3. Start a Mosquitto broker locally:

   ```bash
   mosquitto -v
   ```

   Default broker settings are `localhost:1883`.

4. Start the whitelist agent in one terminal:

   ```bash
   python -m ai_agentics agent --role whitelist_agent
   ```

5. Start the GUI and backend operators in separate terminals:

   ```bash
   python -m ai_agentics agent --role gui_operator
   python -m ai_agentics agent --role backend_operator
   ```

6. Submit a task from the manager:

   ```bash
   python -m ai_agentics team --task "Plan a settings page and its API"
   ```

## CLI reference

### Status

```bash
python -m ai_agentics status
```

### Hello

```bash
python -m ai_agentics hello --name "Developer"
```

### Team task

```bash
python -m ai_agentics team --task "Build a dashboard" --mqtt-host localhost --mqtt-port 1883 --timeout 30
```

### Agent role

```bash
python -m ai_agentics agent --role gui_operator --mqtt-host localhost --mqtt-port 1883
``` 

The whitelist agent can also be started with:

```bash
python -m ai_agentics agent --role whitelist_agent --mqtt-authorized-ids "ai-agentics-manager,ai-agentics-gui_operator,ai-agentics-backend_operator,ai-agentics-whitelist_agent"
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

## Development and testing

Run the full suite:

```bash
python -m unittest discover -s tests -v
```

Or use the Makefile:

```bash
make test
```

## Design notes

The design intentionally keeps the example simple:

- agents connect to MQTT independently
- authorization is enforced before message processing
- security denials are represented as explicit messages
- the team collaborates on task planning rather than real system execution
- the code is a safe starting point for extending into more realistic agent workflows

## Current limitations

This project is a demonstration and not a complete production cyber-resilience solution. Production use should include, at minimum:

- TLS with client authentication
- certificate lifecycle management
- secure secrets handling
- stronger identity and authorization policy enforcement
- robust audit logging and retention
- integration with a full compliance review and product security process

