"""MQTT-backed coordination for the Manager, GUI, and backend agents.

Each agent is an independent MQTT client. The Manager publishes work requests,
operators exchange messages through the broker, and reports return to the
Manager. Security controls include a dedicated whitelist agent that enforces
an allow-list of authorized MQTT client IDs, which is aligned with the spirit of
European Cyber Resilience Act (CRA) security-by-design expectations for secure
identification, authorization, and auditability. This project provides a control
pattern for secure communications; it is not a legal certification.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

ROOT_TOPIC = "ai_agentics"
REPORT_KINDS = {"backend_plan", "backend_feedback", "gui_integrated_plan"}
DEFAULT_ALLOWED_CLIENT_IDS = {
    "ai-agentics-manager",
    "ai-agentics-gui_operator",
    "ai-agentics-backend_operator",
    "ai-agentics-whitelist_agent",
}


def _client(client_id: str) -> mqtt.Client:
    return mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )


def get_authorized_client_ids(extra_ids: str | None = None) -> set[str]:
    """Return the current allow-list for MQTT clients."""
    authorized = set(DEFAULT_ALLOWED_CLIENT_IDS)
    for raw_value in (extra_ids or "", os.getenv("MQTT_AUTHORIZED_IDS", "")):
        for item in raw_value.split(","):
            normalized = item.strip()
            if normalized:
                authorized.add(normalized)
    return authorized


def _publish(client: Any, topic: str, message: dict[str, Any], source_id: str) -> None:
    payload = dict(message)
    payload["source_id"] = source_id
    client.publish(topic, json.dumps(payload), qos=1)


def _is_authorized(source_id: str | None, allowlist: set[str] | None = None) -> bool:
    if not source_id:
        return False
    return str(source_id).strip() in (allowlist or get_authorized_client_ids())


def _deny_message(client: Any, task_id: str, source_id: str | None, reason: str) -> None:
    if client is None or not hasattr(client, "publish"):
        return
    _publish(
        client,
        f"{ROOT_TOPIC}/security/denied",
        {
            "kind": "security_denied",
            "task_id": task_id,
            "reason": reason,
            "details": f"Unrecognized client ID: {source_id}",
        },
        source_id="ai-agentics-whitelist_agent",
    )


def process_operator_message(
    role: str,
    message: dict[str, Any],
    client: Any,
    allowlist: set[str] | None = None,
) -> None:
    """Handle one decoded request/feedback message and enforce MQTT allow-listing."""
    if allowlist is None:
        allowlist = get_authorized_client_ids()

    task_id = str(message.get("task_id") or "")
    source_id = str(message.get("source_id") or "")
    if not _is_authorized(source_id, allowlist):
        _deny_message(client, task_id, source_id, "source_id_not_authorized")
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
            source_id=source_id,
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
            source_id=source_id,
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
            source_id=source_id,
        )
    elif role == "backend_operator" and message.get("kind") == "gui_question":
        feedback = {
            "kind": "backend_feedback",
            "task_id": task_id,
            "text": "Use a documented request/response API contract with explicit loading, success, and error states.",
        }
        _publish(client, f"{ROOT_TOPIC}/feedback/gui_operator", feedback, source_id=source_id)
        _publish(
            client,
            f"{ROOT_TOPIC}/reports/{task_id}",
            {
                "kind": "backend_feedback",
                "task_id": task_id,
                "text": f"Backend-to-GUI guidance: {feedback['text']}",
            },
            source_id=source_id,
        )


class WhitelistAgent:
    """Runs a dedicated MQTT allow-list manager and records denied traffic."""

    def __init__(
        self,
        host: str,
        port: int,
        authorized_ids: str | set[str] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.allowed_ids = set(get_authorized_client_ids())
        if isinstance(authorized_ids, str):
            self.allowed_ids.update(item.strip() for item in authorized_ids.split(",") if item.strip())
        elif isinstance(authorized_ids, set):
            self.allowed_ids.update(authorized_ids)
        self.client = _client("ai-agentics-whitelist_agent")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del userdata, flags, reason_code, properties
        client.subscribe(f"{ROOT_TOPIC}/security/#", qos=1)
        client.publish(
            f"{ROOT_TOPIC}/security/whitelist",
            json.dumps({"kind": "allowlist_status", "allowed_ids": sorted(self.allowed_ids)}),
            qos=1,
        )
        print("whitelist_agent connected to MQTT broker; allow-list active")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                return
        except (UnicodeDecodeError, json.JSONDecodeError):
            return

        if payload.get("kind") == "allowlist_update":
            extra_ids = payload.get("allowed_ids", [])
            if isinstance(extra_ids, list):
                self.allowed_ids.update(str(item).strip() for item in extra_ids if str(item).strip())
            client.publish(
                f"{ROOT_TOPIC}/security/whitelist",
                json.dumps({"kind": "allowlist_status", "allowed_ids": sorted(self.allowed_ids)}),
                qos=1,
            )
            return

        if payload.get("kind") == "validate" or payload.get("kind") == "security_denied":
            source_id = str(payload.get("source_id") or "")
            if source_id in self.allowed_ids:
                client.publish(
                    f"{ROOT_TOPIC}/security/approved",
                    json.dumps({"kind": "security_approved", "source_id": source_id}),
                    qos=1,
                )
            else:
                client.publish(
                    f"{ROOT_TOPIC}/security/denied",
                    json.dumps({
                        "kind": "security_denied",
                        "task_id": payload.get("task_id", ""),
                        "source_id": source_id,
                        "reason": "source_id_not_authorized",
                    }),
                    qos=1,
                )

    def run(self) -> None:
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_forever()


class OperatorAgent:
    """Long-running MQTT client for either operator role."""

    def __init__(
        self,
        role: str,
        host: str,
        port: int,
        authorized_ids: str | set[str] | None = None,
    ) -> None:
        if role not in {"gui_operator", "backend_operator"}:
            raise ValueError(f"Unsupported operator role: {role}")
        self.role = role
        self.host = host
        self.port = port
        self.authorized_ids = get_authorized_client_ids(authorized_ids if isinstance(authorized_ids, str) else None)
        if isinstance(authorized_ids, set):
            self.authorized_ids.update(authorized_ids)
        self.client_id = f"ai-agentics-{role}"
        self.client = _client(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del userdata, flags, reason_code, properties
        client.subscribe(f"{ROOT_TOPIC}/requests/{self.role}", qos=1)
        if self.role == "gui_operator":
            client.subscribe(f"{ROOT_TOPIC}/feedback/gui_operator", qos=1)
        client.publish(
            f"{ROOT_TOPIC}/security/validate",
            json.dumps({"kind": "validate", "source_id": self.client_id}),
            qos=1,
        )
        print(f"{self.role} connected to MQTT broker; waiting for work")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                return
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"Ignoring invalid MQTT message on {msg.topic}: {exc}")
            return

        source_id = str(payload.get("source_id") or "")
        if not _is_authorized(source_id, self.authorized_ids):
            _deny_message(client, str(payload.get("task_id") or ""), source_id, "source_id_not_authorized")
            return
        process_operator_message(self.role, payload, client, self.authorized_ids)

    def run(self) -> None:
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_forever()


def run_manager(
    task: str,
    host: str,
    port: int,
    timeout: float = 30.0,
    authorized_ids: str | set[str] | None = None,
) -> str:
    """Publish a task and collect the three expected MQTT reports with allow-list validation."""
    if not task.strip():
        raise ValueError("Task must not be empty.")

    task_id = uuid.uuid4().hex
    reports: queue.Queue[dict[str, Any]] = queue.Queue()
    subscribed = threading.Event()
    client = _client("ai-agentics-manager")
    allowlist = get_authorized_client_ids(authorized_ids if isinstance(authorized_ids, str) else None)
    if isinstance(authorized_ids, set):
        allowlist.update(authorized_ids)

    def on_connect(client: mqtt.Client, userdata: Any, flags: Any,
                   reason_code: Any, properties: Any) -> None:
        del userdata, flags, reason_code, properties
        client.subscribe(f"{ROOT_TOPIC}/reports/{task_id}", qos=1)
        client.subscribe(f"{ROOT_TOPIC}/security/denied", qos=1)

    def on_subscribe(client: mqtt.Client, userdata: Any, mid: int,
                     reason_code_list: Any, properties: Any) -> None:
        del client, userdata, mid, reason_code_list, properties
        subscribed.set()

    def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        del client, userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if isinstance(payload, dict):
                if payload.get("kind") == "security_denied":
                    print(f"Security denial: {payload}")
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
        _publish(client, f"{ROOT_TOPIC}/requests/gui_operator", request, source_id="ai-agentics-manager")
        _publish(client, f"{ROOT_TOPIC}/requests/backend_operator", request, source_id="ai-agentics-manager")

        deadline = time.monotonic() + timeout
        while set(collected) != REPORT_KINDS:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                missing = ", ".join(sorted(REPORT_KINDS - set(collected)))
                raise TimeoutError(
                    f"Timed out waiting for MQTT reports: {missing}. "
                    "Check that both operator agents are running and that the allow-list includes all client IDs."
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


__all__ = [
    "WhitelistAgent",
    "OperatorAgent",
    "broker_settings",
    "get_authorized_client_ids",
    "process_operator_message",
    "run_manager",
]


if __name__ == "__main__":
    print("MQTT agent security framework for AI-agentics.")
