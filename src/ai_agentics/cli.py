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
        "team", help="ask the Manager, GUI, and backend agents to coordinate on a task"
    )
    team_parser.add_argument("--task", required=True, help="task for the agent team")

    parser.set_defaults(command="status")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "hello":
        print(f"Hello, {args.name}!")
        return 0

    if args.command == "team":
        from ai_agentics.agent_team import ManagerAgent

        print(ManagerAgent().run(args.task))
        return 0

    print("AI-agentics is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
