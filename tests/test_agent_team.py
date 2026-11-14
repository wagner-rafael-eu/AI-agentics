import unittest
from unittest.mock import Mock

from ai_agentics.agent_team import process_operator_message


class TestMqttAgentTeam(unittest.TestCase):
    def setUp(self):
        self.client = Mock()

    def test_gui_sends_backend_question_over_mqtt(self):
        process_operator_message(
            "gui_operator",
            {"kind": "task", "task_id": "task-1", "task": "Build a settings screen"},
            self.client,
        )
        args, kwargs = self.client.publish.call_args
        self.assertEqual(args[0], "ai_agentics/requests/backend_operator")
        self.assertEqual(kwargs["qos"], 1)
        self.assertIn("gui_question", args[1])

    def test_backend_replies_to_gui_and_manager_over_mqtt(self):
        process_operator_message(
            "backend_operator",
            {"kind": "gui_question", "task_id": "task-2"},
            self.client,
        )
        topics = [call.args[0] for call in self.client.publish.call_args_list]
        self.assertIn("ai_agentics/feedback/gui_operator", topics)
        self.assertIn("ai_agentics/reports/task-2", topics)

    def test_gui_integrates_backend_feedback(self):
        process_operator_message(
            "gui_operator",
            {"kind": "backend_feedback", "task_id": "task-3", "text": "REST API"},
            self.client,
        )
        args, _ = self.client.publish.call_args
        self.assertEqual(args[0], "ai_agentics/reports/task-3")
        self.assertIn("gui_integrated_plan", args[1])


if __name__ == "__main__":
    unittest.main()
