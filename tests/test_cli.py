import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from git_multiple import cli
from git_multiple.config import ProfileStore
from git_multiple.git import GitError, Identity


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "profiles.json"
        self.environment = mock.patch.dict(
            "os.environ", {"GIT_MULTIPLE_CONFIG": str(self.path)}
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def invoke(self, *arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = cli.main(arguments)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_add_list_remove_flow(self):
        result, output, _ = self.invoke(
            "add", "--name", "Mary", "--email", "mary@example.com"
        )
        self.assertEqual(result, 0)
        self.assertIn("Added mary", output)

        with mock.patch.object(
            cli.GitConfig,
            "get_identity",
            return_value=Identity("Mary", "mary@example.com"),
        ):
            result, output, _ = self.invoke("list")
        self.assertEqual(result, 0)
        self.assertIn("* mary: Mary <mary@example.com>", output)

        result, output, _ = self.invoke("remove", "mary", "--yes")
        self.assertEqual(result, 0)
        self.assertIn("Removed mary", output)
        self.assertEqual(ProfileStore(self.path).load(), [])

    def test_use_applies_selected_scope(self):
        ProfileStore(self.path).add("Mary", "mary@example.com", "work")
        with mock.patch.object(cli.GitConfig, "set_identity") as set_identity:
            result, output, _ = self.invoke("use", "work", "--scope", "local")
        self.assertEqual(result, 0)
        self.assertIn("(local)", output)
        self.assertEqual(set_identity.call_args.args[1], "local")

    def test_errors_are_returned_without_traceback(self):
        with mock.patch.object(
            cli.GitConfig, "ensure_available", side_effect=GitError("missing")
        ):
            result, _, error = self.invoke("doctor")
        self.assertEqual(result, 2)
        self.assertEqual(error, "error: missing\n")

    def test_empty_noninteractive_invocation_is_actionable(self):
        result, output, _ = self.invoke()
        self.assertEqual(result, 1)
        self.assertIn("git-multiple add", output)

    def test_import_legacy_is_idempotent(self):
        legacy = Path(self.temporary.name) / "config.env"
        legacy.write_text("USER_1=Mary\nEMAIL_1=mary@example.com\n", encoding="utf-8")
        first = self.invoke("import-legacy", str(legacy))
        second = self.invoke("import-legacy", str(legacy))
        self.assertIn("Imported 1", first[1])
        self.assertIn("skipped 1", second[1])

    def test_original_long_add_flag_remains_compatible(self):
        result, output, _ = self.invoke(
            "--add", "--name", "Mary", "--email", "mary@example.com"
        )
        self.assertEqual(result, 0)
        self.assertIn("Added mary", output)


if __name__ == "__main__":
    unittest.main()
