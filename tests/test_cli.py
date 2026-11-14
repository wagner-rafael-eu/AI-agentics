import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ai_agentics import agent_team


class TestAuthorizationHelpers(unittest.TestCase):
    def test_default_allowlist_contains_expected_ids(self):
        with patch.dict(os.environ, {}, clear=True):
            ids = agent_team.get_authorized_client_ids()

        self.assertIn("ai-agentics-manager", ids)
        self.assertIn("ai-agentics-gui_operator", ids)
        self.assertIn("ai-agentics-backend_operator", ids)
        self.assertIn("ai-agentics-whitelist_agent", ids)

    def test_allowlist_adds_environment_and_extra_values(self):
        with patch.dict(os.environ, {"MQTT_AUTHORIZED_IDS": "client-a,client-b"}, clear=True):
            ids = agent_team.get_authorized_client_ids("client-c")

        self.assertIn("client-a", ids)
        self.assertIn("client-b", ids)
        self.assertIn("client-c", ids)


class TestProcessOperatorMessage(unittest.TestCase):
    def test_gui_task_is_relayed_to_backend_operator(self):
        client = Mock()
        message = {
            "kind": "task",
            "task_id": "task-1",
            "task": "Build a settings screen",
            "source_id": "ai-agentics-gui_operator",
        }

        agent_team.process_operator_message("gui_operator", message, client)

        self.assertEqual(client.publish.call_count, 1)
        topic, payload, qos = client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/requests/backend_operator")
        self.assertEqual(qos, 1)

        body = json.loads(payload)
        self.assertEqual(body["kind"], "gui_question")
        self.assertEqual(body["source_id"], "ai-agentics-gui_operator")

    def test_unknown_source_is_rejected(self):
        client = Mock()
        message = {
            "kind": "task",
            "task_id": "task-2",
            "task": "Add policy",
            "source_id": "fake-client",
        }

        agent_team.process_operator_message("backend_operator", message, client)

        topic, payload, qos = client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/security/denied")
        self.assertEqual(qos, 1)

        body = json.loads(payload)
        self.assertEqual(body["kind"], "security_denied")
        self.assertEqual(body["reason"], "source_id_not_authorized")

    def test_backend_operator_returns_guidance_to_gui(self):
        client = Mock()
        message = {
            "kind": "gui_question",
            "task_id": "task-3",
            "source_id": "ai-agentics-backend_operator",
        }

        agent_team.process_operator_message("backend_operator", message, client)

        topics = [call.args[0] for call in client.publish.call_args_list]
        self.assertIn("ai_agentics/feedback/gui_operator", topics)
        self.assertIn("ai_agentics/reports/task-3", topics)

        first_payload = json.loads(client.publish.call_args_list[0].args[1])
        self.assertEqual(first_payload["kind"], "backend_feedback")

    def test_gui_operator_integrates_backend_feedback(self):
        client = Mock()
        message = {
            "kind": "backend_feedback",
            "task_id": "task-4",
            "text": "REST API contract",
            "source_id": "ai-agentics-gui_operator",
        }

        agent_team.process_operator_message("gui_operator", message, client)

        topic, payload, qos = client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/reports/task-4")
        self.assertEqual(qos, 1)

        body = json.loads(payload)
        self.assertEqual(body["kind"], "gui_integrated_plan")
        self.assertIn("REST API contract", body["text"])


class TestWhitelistAgent(unittest.TestCase):
    def test_agent_starts_with_default_allowlist(self):
        agent = agent_team.WhitelistAgent("localhost", 1883)
        self.assertIn("ai-agentics-manager", agent.allowed_ids)
        self.assertIn("ai-agentics-gui_operator", agent.allowed_ids)
        self.assertIn("ai-agentics-backend_operator", agent.allowed_ids)

    def test_allowlist_update_updates_internal_state(self):
        agent = agent_team.WhitelistAgent("localhost", 1883)
        agent.client = Mock()

        msg = SimpleNamespace(
            payload=json.dumps({"kind": "allowlist_update", "allowed_ids": ["client-x", "client-y"]}).encode("utf-8")
        )

        agent._on_message(agent.client, None, msg)

        self.assertIn("client-x", agent.allowed_ids)
        self.assertIn("client-y", agent.allowed_ids)
        topic, payload, qos = agent.client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/security/whitelist")
        self.assertEqual(qos, 1)

    def test_validate_message_approves_and_denies(self):
        agent = agent_team.WhitelistAgent("localhost", 1883, {"client-a"})
        agent.client = Mock()

        valid_msg = SimpleNamespace(payload=json.dumps({"kind": "validate", "source_id": "client-a"}).encode("utf-8"))
        invalid_msg = SimpleNamespace(payload=json.dumps({"kind": "validate", "source_id": "bad-client"}).encode("utf-8"))

        agent._on_message(agent.client, None, valid_msg)
        agent._on_message(agent.client, None, invalid_msg)

        topics = [call.args[0] for call in agent.client.publish.call_args_list]
        self.assertIn("ai_agentics/security/approved", topics)
        self.assertIn("ai_agentics/security/denied", topics)


class TestOperatorAgent(unittest.TestCase):
    def test_on_connect_sends_validation_message(self):
        agent = agent_team.OperatorAgent("gui_operator", "localhost", 1883)
        agent.client = Mock()

        agent._on_connect(agent.client, None, None, None, None)

        self.assertEqual(agent.client.subscribe.call_count, 2)
        self.assertEqual(agent.client.publish.call_count, 1)

        topic, payload, qos = agent.client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/security/validate")
        self.assertEqual(qos, 1)

        body = json.loads(payload)
        self.assertEqual(body["source_id"], "ai-agentics-gui_operator")

    def test_untrusted_message_is_rejected(self):
        agent = agent_team.OperatorAgent("backend_operator", "localhost", 1883, {"ai-agentics-backend_operator"})
        agent.client = Mock()
        msg = SimpleNamespace(
            payload=json.dumps({
                "kind": "task",
                "task_id": "task-5",
                "task": "Do something",
                "source_id": "not-authorized",
            }).encode("utf-8")
        )

        agent._on_message(agent.client, None, msg)

        topic, payload, qos = agent.client.publish.call_args.args
        self.assertEqual(topic, "ai_agentics/security/denied")
        self.assertEqual(qos, 1)

        body = json.loads(payload)
        self.assertEqual(body["reason"], "source_id_not_authorized")


class TestManagerAndBroker(unittest.TestCase):
    def test_broker_settings_uses_explicit_values(self):
        self.assertEqual(agent_team.broker_settings("mqtt.example.com", 1884), ("mqtt.example.com", 1884))

    def test_broker_settings_uses_environment_when_present(self):
        with patch.dict(os.environ, {"MQTT_HOST": "broker.example", "MQTT_PORT": "1885"}, clear=True):
            self.assertEqual(agent_team.broker_settings(None, None), ("broker.example", 1885))

    @patch("ai_agentics.agent_team.time.monotonic")
    @patch("ai_agentics.agent_team.threading.Event.wait")
    @patch("ai_agentics.agent_team._client")
    def test_run_manager_collects_reports(self, mock_client_factory, mock_event_wait, mock_monotonic):
        client = Mock()
        mock_client_factory.return_value = client
        mock_event_wait.return_value = True

        queue_values = [
            {"kind": "backend_plan", "text": "Backend plan: service, model, contract"},
            {"kind": "backend_feedback", "text": "Backend-to-GUI guidance: define API contract"},
            {"kind": "gui_integrated_plan", "text": "GUI plan: connect to the API"},
        ]

        mock_monotonic.side_effect = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

        with patch("ai_agentics.agent_team.queue.Queue.get", side_effect=queue_values):
            result = agent_team.run_manager("Build a dashboard", "localhost", 1883, timeout=5.0)

        self.assertIn("Manager summary for: Build a dashboard", result)
        self.assertIn("Backend plan", result)
        self.assertIn("Backend-to-GUI guidance", result)
        self.assertIn("GUI plan", result)


if __name__ == "__main__":
    unittest.main()

