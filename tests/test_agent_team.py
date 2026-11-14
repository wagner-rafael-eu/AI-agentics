import unittest

from ai_agentics.agent_team import AgentNetwork, ManagerAgent
from ai_agentics.cli import main


class TestAgentTeam(unittest.TestCase):
    def test_manager_coordinates_gui_and_backend_agents(self):
        result = ManagerAgent().run("Build a settings screen")
        self.assertIn("Manager summary", result)
        self.assertIn("Backend plan", result)
        self.assertIn("GUI plan", result)
        self.assertIn("request/response API contract", result)

    def test_network_rejects_unknown_recipients(self):
        network = AgentNetwork({"manager"})
        with self.assertRaises(ValueError):
            network.send("manager", "missing", "hello")

    def test_team_cli(self):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["team", "--task", "Build a dashboard"])
        self.assertEqual(result, 0)
        self.assertIn("GUI plan", output.getvalue())


if __name__ == "__main__":
    unittest.main()
