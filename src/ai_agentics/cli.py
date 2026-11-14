"""Command-line interface for AI-agentics."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-agentics",
        description="AI-agentics command line interface.",
    )
    subparsers = parser.add_subparsers(dest="command")

    hello_parser = subparsers.add_parser("hello", help="say hello")
    hello_parser.add_argument("--name", default="World", help="name to greet")
    subparsers.add_parser("status", help="show project status")

    team_parser = subparsers.add_parser(
        "team", help="send a task to the MQTT-connected agent team"
    )
    team_parser.add_argument("--task", required=True, help="task for the agent team")
    team_parser.add_argument("--mqtt-host", help="MQTT broker host (or MQTT_HOST)")
    team_parser.add_argument("--mqtt-port", type=int, help="MQTT broker port (or MQTT_PORT)")
    team_parser.add_argument("--timeout", type=float, default=30.0, help="report timeout in seconds")

    agent_parser = subparsers.add_parser("agent", help="run an MQTT operator agent")
    agent_parser.add_argument("--role", required=True, choices=["gui_operator", "backend_operator"])
    agent_parser.add_argument("--mqtt-host", help="MQTT broker host (or MQTT_HOST)")
    agent_parser.add_argument("--mqtt-port", type=int, help="MQTT broker port (or MQTT_PORT)")

    parser.set_defaults(command="status")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "hello":
        print(f"Hello, {args.name}!")
        return 0

    if args.command in {"team", "agent"}:
        from ai_agentics.agent_team import OperatorAgent, broker_settings, run_manager

        host, port = broker_settings(args.mqtt_host, args.mqtt_port)
        try:
            if args.command == "team":
                print(run_manager(args.task, host, port, args.timeout))
            else:
                OperatorAgent(args.role, host, port).run()
        except (OSError, TimeoutError, ValueError) as exc:
            parser.exit(1, f"ai-agentics: {exc}\n")
        return 0

    print("AI-agentics is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
