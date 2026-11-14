import unittest
from unittest.mock import Mock

from ai_agentics.agent_team import WhitelistAgent, get_authorized_client_ids, process_operator_message


class TestMqttAgentTeam(unittest.TestCase):
    def setUp(self):
        self.client = Mock()

    def test_gui_sends_backend_question_over_mqtt(self):
        process_operator_message(
            "gui_operator",
            {
                "kind": "task",
                "task_id": "task-1",
                "task": "Build a settings screen",
                "source_id": "ai-agentics-gui_operator",
            },
            self.client,
        )
        args, kwargs = self.client.publish.call_args
        self.assertEqual(args[0], "ai_agentics/requests/backend_operator")
        self.assertEqual(kwargs["qos"], 1)
        self.assertIn("gui_question", args[1])

    def test_backend_replies_to_gui_and_manager_over_mqtt(self):
        process_operator_message(
            "backend_operator",
            {"kind": "gui_question", "task_id": "task-2", "source_id": "ai-agentics-backend_operator"},
            self.client,
        )
        topics = [call.args[0] for call in self.client.publish.call_args_list]
        self.assertIn("ai_agentics/feedback/gui_operator", topics)
        self.assertIn("ai_agentics/reports/task-2", topics)

    def test_gui_integrates_backend_feedback(self):
        process_operator_message(
            "gui_operator",
            {"kind": "backend_feedback", "task_id": "task-3", "text": "REST API", "source_id": "ai-agentics-gui_operator"},
            self.client,
        )
        args, _ = self.client.publish.call_args
        self.assertEqual(args[0], "ai_agentics/reports/task-3")
        self.assertIn("gui_integrated_plan", args[1])

    def test_unknown_source_id_is_rejected(self):
        process_operator_message(
            "backend_operator",
            {"kind": "task", "task_id": "task-4", "task": "Add policy", "source_id": "untrusted-client"},
            self.client,
        )
        args, _ = self.client.publish.call_args
        self.assertEqual(args[0], "ai_agentics/security/denied")
        self.assertIn("source_id_not_authorized", args[1])

    def test_whitelist_agent_accepts_known_ids(self):
        agent = WhitelistAgent("localhost", 1883, {"ai-agentics-manager"})
        self.assertIn("ai-agentics-manager", agent.allowed_ids)
        self.assertIn("ai-agentics-gui_operator", get_authorized_client_ids())


if __name__ == "__main__":
    unittest.main()
