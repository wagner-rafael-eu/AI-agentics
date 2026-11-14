import unittest

from ai_agentics.cli import main


class TestCli(unittest.TestCase):
    def test_status_command(self):
        output = self._run_cli(["status"])
        self.assertEqual(output.strip(), "AI-agentics is ready.")

    def test_hello_command(self):
        output = self._run_cli(["hello", "--name", "Developer"])
        self.assertEqual(output.strip(), "Hello, Developer!")

    def _run_cli(self, argv):
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(argv)
        self.assertEqual(result, 0)
        return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
