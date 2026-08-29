import subprocess
import unittest
from unittest import mock

from git_multiple.config import Profile
from git_multiple.git import GitConfig, GitError, Identity


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class GitConfigTests(unittest.TestCase):
    @mock.patch("git_multiple.git.shutil.which", return_value="/usr/bin/git")
    @mock.patch("git_multiple.git.subprocess.run")
    def test_reads_missing_values(self, run, _which):
        run.side_effect = [completed(1), completed(0, "mary@example.com\n")]
        self.assertEqual(
            GitConfig().get_identity("global"), Identity(None, "mary@example.com")
        )

    @mock.patch("git_multiple.git.shutil.which", return_value=None)
    def test_reports_missing_git(self, _which):
        with self.assertRaisesRegex(GitError, "not found"):
            GitConfig().get_identity("global")

    @mock.patch("git_multiple.git.shutil.which", return_value="git")
    @mock.patch("git_multiple.git.subprocess.run")
    def test_uses_argument_arrays_not_a_shell(self, run, _which):
        run.side_effect = [
            completed(0, "Old Name\n"),
            completed(0, "old@example.com\n"),
            completed(),
            completed(),
        ]
        profile = Profile("work", "Name; echo unsafe", "safe@example.com")
        GitConfig().set_identity(profile, "global")
        name_call = run.call_args_list[2]
        self.assertEqual(
            name_call.args[0],
            ["git", "config", "--global", "user.name", "Name; echo unsafe"],
        )
        self.assertFalse(name_call.kwargs.get("shell", False))

    @mock.patch("git_multiple.git.shutil.which", return_value="git")
    @mock.patch("git_multiple.git.subprocess.run")
    def test_rolls_back_if_second_write_fails(self, run, _which):
        run.side_effect = [
            completed(0, "Old Name\n"),
            completed(0, "old@example.com\n"),
            completed(),
            completed(1, stderr="locked"),
            completed(),
            completed(),
        ]
        with self.assertRaisesRegex(GitError, "locked"):
            GitConfig().set_identity(Profile("new", "New", "new@example.com"), "global")
        self.assertEqual(
            run.call_args_list[-2].args[0],
            ["git", "config", "--global", "user.name", "Old Name"],
        )

    def test_rejects_invalid_scope(self):
        with self.assertRaisesRegex(GitError, "Unknown"):
            GitConfig()._scope_flag("system")


if __name__ == "__main__":
    unittest.main()
