"""Safe subprocess interface to Git configuration."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .config import Profile


class GitError(RuntimeError):
    """Raised when Git is unavailable or rejects an operation."""


@dataclass(frozen=True)
class Identity:
    name: str | None
    email: str | None


class GitConfig:
    def __init__(self, executable: str = "git") -> None:
        self.executable = executable

    def ensure_available(self) -> None:
        if shutil.which(self.executable) is None:
            raise GitError("Git was not found on PATH. Install Git and try again.")

    def get_identity(self, scope: str) -> Identity:
        self.ensure_available()
        return Identity(self._get("user.name", scope), self._get("user.email", scope))

    def set_identity(self, profile: Profile, scope: str) -> None:
        self.ensure_available()
        previous = self.get_identity(scope)
        self._set("user.name", profile.name, scope)
        try:
            self._set("user.email", profile.email, scope)
        except GitError:
            self._restore("user.name", previous.name, scope)
            self._restore("user.email", previous.email, scope)
            raise

    def _scope_flag(self, scope: str) -> str:
        if scope not in {"global", "local"}:
            raise GitError(f"Unknown Git configuration scope: {scope}")
        return f"--{scope}"

    def _get(self, key: str, scope: str) -> str | None:
        result = subprocess.run(
            [self.executable, "config", self._scope_flag(scope), "--get", key],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 1:
            return None
        if result.returncode != 0:
            raise GitError(
                _error_message(result, f"Could not read Git {scope} configuration")
            )
        return result.stdout.rstrip("\r\n") or None

    def _set(self, key: str, value: str, scope: str) -> None:
        result = subprocess.run(
            [self.executable, "config", self._scope_flag(scope), key, value],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise GitError(
                _error_message(result, f"Could not update Git {scope} configuration")
            )

    def _restore(self, key: str, value: str | None, scope: str) -> None:
        args = [self.executable, "config", self._scope_flag(scope)]
        args.extend([key, value] if value is not None else ["--unset-all", key])
        subprocess.run(args, text=True, capture_output=True, check=False)


def _error_message(result: subprocess.CompletedProcess[str], fallback: str) -> str:
    detail = result.stderr.strip() or result.stdout.strip()
    return f"{fallback}: {detail}" if detail else fallback
