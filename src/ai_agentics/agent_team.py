"""A small in-process team of cooperating AI-agentics role agents.

These agents demonstrate message routing and orchestration. The GUI and backend
operators produce plans and coordination notes; they do not control a real GUI,
run code, or call external services.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    """A message exchanged between named agents."""

    sender: str
    recipient: str
    content: str


class AgentNetwork:
    """In-memory message bus shared by the team agents."""

    def __init__(self, agent_names: set[str]) -> None:
        self._agent_names = agent_names
        self._inboxes: dict[str, list[Message]] = defaultdict(list)
        self.history: list[Message] = []

    def send(self, sender: str, recipient: str, content: str) -> None:
        if sender not in self._agent_names:
            raise ValueError(f"Unknown sender: {sender}")
        if recipient not in self._agent_names:
            raise ValueError(f"Unknown recipient: {recipient}")
        message = Message(sender=sender, recipient=recipient, content=content)
        self.history.append(message)
        self._inboxes[recipient].append(message)

    def receive(self, recipient: str) -> list[Message]:
        if recipient not in self._agent_names:
            raise ValueError(f"Unknown recipient: {recipient}")
        messages = self._inboxes[recipient]
        self._inboxes[recipient] = []
        return messages


class ManagerAgent:
    """Delegates a task, coordinates operator feedback, and reports a summary."""

    name = "manager"

    def run(self, task: str) -> str:
        if not task.strip():
            raise ValueError("Task must not be empty.")

        network = AgentNetwork({self.name, "gui_operator", "backend_operator"})
        network.send(self.name, "gui_operator", f"Plan the GUI work for: {task}")
        network.send(self.name, "backend_operator", f"Plan the backend work for: {task}")

        GuiOperatorAgent().prepare(network)
        BackendOperatorAgent().respond(network)
        GuiOperatorAgent().finalize(network)

        reports = network.receive(self.name)
        report_text = "\n".join(f"- {message.content}" for message in reports)
        return f"Manager summary for: {task}\n{report_text}"


class GuiOperatorAgent:
    """Plans UI work and consults the backend operator about integration."""

    name = "gui_operator"

    def prepare(self, network: AgentNetwork) -> None:
        requests = network.receive(self.name)
        for message in requests:
            network.send(
                self.name,
                "backend_operator",
                f"For the GUI task, suggest the backend contract needed. Context: {message.content}",
            )

    def finalize(self, network: AgentNetwork) -> None:
        for message in network.receive(self.name):
            if message.sender == "backend_operator":
                network.send(
                    self.name,
                    "manager",
                    f"GUI plan: {message.content}",
                )


class BackendOperatorAgent:
    """Plans backend work and replies to GUI integration questions."""

    name = "backend_operator"

    def respond(self, network: AgentNetwork) -> None:
        for message in network.receive(self.name):
            if message.sender == "manager":
                network.send(
                    self.name,
                    "manager",
                    f"Backend plan: identify the service, data model, and API work for {message.content.removeprefix('Plan the backend work for: ')}",
                )
            elif message.sender == "gui_operator":
                network.send(
                    self.name,
                    "gui_operator",
                    "Suggested integration: define a documented request/response API contract and explicit loading, success, and error states. This is a planning suggestion, not an implemented API.",
                )
