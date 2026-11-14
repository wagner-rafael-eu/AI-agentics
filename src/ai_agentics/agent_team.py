import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from ai_agentics.cli import main


class TestCli(unittest.TestCase):
    def test_status_command(self):
        output = self._run_cli(["status"])
        self.assertEqual(output.strip(), "AI-agentics is ready.")

    def test_hello_command(self):
        output = self._run_cli(["hello", "--name", "Developer"])
        self.assertEqual(output.strip(), "Hello, Developer!")

    @patch("ai_agentics.agent_team.broker_settings", return_value=("localhost", 1883))
    @patch("ai_agentics.agent_team.run_manager", return_value="Manager summary for: Build a dashboard")
    def test_team_command_routes_to_manager(self, mock_run_manager, mock_broker_settings):
        del mock_broker_settings
        output = self._run_cli(["team", "--task", "Build a dashboard"])
        self.assertEqual(output.strip(), "Manager summary for: Build a dashboard")
        mock_run_manager.assert_called_once_with("Build a dashboard", "localhost", 1883, 30.0, None)

    @patch("ai_agentics.agent_team.broker_settings", return_value=("localhost", 1883))
    @patch("ai_agentics.agent_team.WhitelistAgent")
    def test_agent_command_routes_to_whitelist_agent(self, mock_whitelist_agent, mock_broker_settings):
        del mock_broker_settings
        instance = mock_whitelist_agent.return_value
        result = main(["agent", "--role", "whitelist_agent"])
        self.assertEqual(result, 0)
        instance.run.assert_called_once()

    @patch("ai_agentics.agent_team.broker_settings", return_value=("localhost", 1883))
    @patch("ai_agentics.agent_team.OperatorAgent")
    def test_agent_command_routes_to_operator_agent(self, mock_operator_agent, mock_broker_settings):
        del mock_broker_settings
        instance = mock_operator_agent.return_value
        result = main(["agent", "--role", "backend_operator"])
        self.assertEqual(result, 0)
        instance.run.assert_called_once()

    def _run_cli(self, argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(argv)
        self.assertEqual(result, 0)
        return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()

