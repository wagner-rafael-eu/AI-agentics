"""MQTT-backed coordination for the Manager, GUI, and backend agents.

Each agent is an independent MQTT client. The Manager publishes work requests,
operators exchange messages through the broker, and reports return to the
Manager. No in-process message bus is used.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

ROOT_TOPIC = "ai_agentics"
REPORT_KINDS = {"backend_plan", "backend_feedback", "gui_integrated_plan"}


def _client(client_id: str) -> mqtt.Client:
    return mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )


def _publish(client: Any, topic: str, message: dict[str, Any]) -> None:
    client.publish(topic, json.dumps(message), qos=1)


def process_operator_message(role: str, message: dict[str, Any], client: Any) -> None:
    """Handle one decoded request/feedback message; useful for unit testing."""
    task_id = message.get("task_id")
    if not task_id:
        return

    if role == "gui_operator" and message.get("kind") == "task":
        task = message.get("task", "")
        _publish(
            client,
            f"{ROOT_TOPIC}/requests/backend_operator",
            {
                "kind": "gui_question",
                "task_id": task_id,
                "task": task,
                "question": "What request/response API contract and states should the GUI use?",
            },
        )
    elif role == "gui_operator" and message.get("kind") == "backend_feedback":
        _publish(
            client,
            f"{ROOT_TOPIC}/reports/{task_id}",
            {
                "kind": "gui_integrated_plan",
                "task_id": task_id,
                "text": (
                    "GUI plan: implement the task-facing screens and connect them "
                    f"using the backend contract: {message.get('text', '')}"
                ),
            },
        )
    elif role == "backend_operator" and message.get("kind") == "task":
        _publish(
            client,
            f"{ROOT_TOPIC}/reports/{task_id}",
            {
                "kind": "backend_plan",
                "task_id": task_id,
                "text": f"Backend plan: identify the service, data model, and API work for {message.get('task', '')}",
            },
        )
    elif role == "backend_operator" and message.get("kind") == "gui_question":
        feedback = {
            "kind": "backend_feedback",
            "task_id": task_id,
            "text": "Use a documented request/response API contract with explicit loading, success, and error states.",
        }
        _publish(client, f"{ROOT_TOPIC}/feedback/gui_operator", feedback)
        _publish(client, f"{ROOT_TOPIC}/reports/{task_id}", {
            "kind": "backend_feedback",
            "task_id": task_id,
            "text": f"Backend-to-GUI guidance: {feedback['text']}",
        })


class OperatorAgent:
    """Long-running MQTT client for either operator role."""

    def __init__(self, role: str, host: str, port: int) -> None:
        if role not in {"gui_operator", "backend_operator"}:
            raise ValueError(f"Unsupported operator role: {role}")
        self.role = role
        self.host = host
        self.port = port
        self.client = _client(f"ai-agentics-{role}-{uuid.uuid4().hex[:8]}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any,
                    reason_code: Any, properties: Any) -> None:
        del userdata, flags, reason_code, properties
        client.subscribe(f"{ROOT_TOPIC}/requests/{self.role}", qos=1)
        if self.role == "gui_operator":
            client.subscribe(f"{ROOT_TOPIC}/feedback/gui_operator", qos=1)
        print(f"{self.role} connected to MQTT broker; waiting for work")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if isinstance(payload, dict):
                process_operator_message(self.role, payload, client)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"Ignoring invalid MQTT message on {msg.topic}: {exc}")

    def run(self) -> None:
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_forever()


def run_manager(task: str, host: str, port: int, timeout: float = 30.0) -> str:
    """Publish a task and collect the three expected MQTT reports."""
    if not task.strip():
        raise ValueError("Task must not be empty.")

    task_id = uuid.uuid4().hex
    reports: queue.Queue[dict[str, Any]] = queue.Queue()
    subscribed = threading.Event()
    client = _client(f"ai-agentics-manager-{task_id[:8]}")

    def on_connect(client: mqtt.Client, userdata: Any, flags: Any,
                   reason_code: Any, properties: Any) -> None:
        del userdata, flags, reason_code, properties
        client.subscribe(f"{ROOT_TOPIC}/reports/{task_id}", qos=1)

    def on_subscribe(client: mqtt.Client, userdata: Any, mid: int,
                     reason_code_list: Any, properties: Any) -> None:
        del client, userdata, mid, reason_code_list, properties
        subscribed.set()

    def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del client, userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if isinstance(payload, dict):
                reports.put(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.connect(host, port, keepalive=60)
    client.loop_start()

    collected: dict[str, str] = {}
    try:
        if not subscribed.wait(timeout=min(timeout, 10.0)):
            raise TimeoutError("Timed out subscribing to the MQTT report topic.")

        request = {"kind": "task", "task_id": task_id, "task": task}
        _publish(client, f"{ROOT_TOPIC}/requests/gui_operator", request)
        _publish(client, f"{ROOT_TOPIC}/requests/backend_operator", request)

        deadline = time.monotonic() + timeout
        while set(collected) != REPORT_KINDS:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                missing = ", ".join(sorted(REPORT_KINDS - set(collected)))
                raise TimeoutError(
                    f"Timed out waiting for MQTT reports: {missing}. "
                    "Check that both operator agents are running."
                )
            report = reports.get(timeout=remaining)
            kind = report.get("kind")
            if kind in REPORT_KINDS:
                collected[kind] = str(report.get("text", ""))
    finally:
        client.disconnect()
        client.loop_stop()

    return "\n".join(
        [f"Manager summary for: {task}"]
        + [f"- {collected[kind]}" for kind in sorted(REPORT_KINDS)]
    )


def broker_settings(host: str | None, port: int | None) -> tuple[str, int]:
    """Resolve broker settings from CLI options, then environment, then defaults."""
    return (
        host or os.getenv("MQTT_HOST", "localhost"),
        port or int(os.getenv("MQTT_PORT", "1883")),
    )
