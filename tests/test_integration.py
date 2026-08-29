import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("git"), "Git is required for integration tests")
class EndToEndTests(unittest.TestCase):
    def test_cli_changes_isolated_global_git_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = os.environ.copy()
            environment["GIT_MULTIPLE_CONFIG"] = str(root / "profiles.json")
            environment["GIT_CONFIG_GLOBAL"] = str(root / "gitconfig")
            environment["PYTHONPATH"] = str(ROOT)

            def command(*arguments):
                return subprocess.run(
                    [sys.executable, "-m", "git_multiple", *arguments],
                    cwd=ROOT,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            added = command(
                "add",
                "--id",
                "work",
                "--name",
                "Mary Jane",
                "--email",
                "mary@example.com",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            switched = command("use", "work")
            self.assertEqual(switched.returncode, 0, switched.stderr)
            current = command("current")
            self.assertEqual(current.returncode, 0, current.stderr)
            self.assertEqual(current.stdout.strip(), "Mary Jane <mary@example.com>")

            name = subprocess.run(
                ["git", "config", "--global", "--get", "user.name"],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(name.stdout.strip(), "Mary Jane")

    def test_local_switch_does_not_change_global_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            environment = os.environ.copy()
            environment["GIT_MULTIPLE_CONFIG"] = str(root / "profiles.json")
            environment["GIT_CONFIG_GLOBAL"] = str(root / "gitconfig")
            environment["PYTHONPATH"] = str(ROOT)
            subprocess.run(
                ["git", "init", "-q", str(repository)], check=True, env=environment
            )
            subprocess.run(
                ["git", "config", "--global", "user.name", "Global User"],
                check=True,
                env=environment,
            )
            subprocess.run(
                ["git", "config", "--global", "user.email", "global@example.com"],
                check=True,
                env=environment,
            )

            def command(*arguments):
                return subprocess.run(
                    [sys.executable, "-m", "git_multiple", *arguments],
                    cwd=repository,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            added = command(
                "add",
                "--id",
                "local",
                "--name",
                "Local User",
                "--email",
                "local@example.com",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            switched = command("use", "local", "--scope", "local")
            self.assertEqual(switched.returncode, 0, switched.stderr)
            self.assertEqual(
                command("current", "--scope", "local").stdout.strip(),
                "Local User <local@example.com>",
            )
            self.assertEqual(
                command("current").stdout.strip(), "Global User <global@example.com>"
            )


if __name__ == "__main__":
    unittest.main()
