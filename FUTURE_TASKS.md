# Future tasks for AI-agentics

## Security and hardening
- Add TLS / MQTTS support with certificate validation
- Implement client certificate authentication for MQTT brokers
- Add per-agent permission roles and authorization policies
- Support dynamic allow-list updates with signed policy changes
- Add persistent audit logging for all MQTT messages and security decisions
- Introduce message signing and integrity verification
- Add secrets management for broker credentials and TLS material

## Operational improvements
- Add retry logic and timeout-aware reconciliation for broker failures
- Add dead-letter handling for rejected or undeliverable messages
- Add health checks and readiness endpoints for each agent
- Add observability metrics for broker traffic, latencies, and denied events
- Add structured JSON logging and error correlation IDs

## Product and compliance
- Review and document alignment with EU Cyber Resilience Act requirements
- Add formal risk assessment and threat model documentation
- Add secure deployment guidance for production environments
- Add compliance checklist for regulated deployments

## Platform features
- Add a GUI or dashboard that subscribes to agent status and reports
- Add persistent state storage for task history and report records
- Add a web API wrapper for task submission and status retrieval
- Add database-backed event retention and analytics
- Add plugin architecture for new agent roles and tool integrations

## Quality and maintainability
- Add end-to-end integration tests for MQTT broker workflows
- Add fuzz testing for invalid MQTT payloads and malformed client IDs
- Add static analysis and linting configuration
- Add CI/CD pipeline for tests and packaging
- Add versioned release workflow and changelog

## Research and extension
- Add LLM-backed reasoning agents with safe tool execution boundaries
- Add multi-tenant agent isolation for different workloads
- Add replay and debugging tools for historical message sequences
- Add simulation mode for offline testing of agent coordination behaviors
