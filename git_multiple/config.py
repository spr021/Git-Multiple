"""Persistent profile storage for Git Multiple."""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when the profile configuration cannot be used."""


@dataclass(frozen=True)
class Profile:
    id: str
    name: str
    email: str


def config_path() -> Path:
    override = os.environ.get("GIT_MULTIPLE_CONFIG")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys_platform() == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "git-multiple" / "profiles.json"


def sys_platform() -> str:
    # Kept as a small seam so path behavior can be tested on any operating system.
    import sys

    return sys.platform


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()

    def load(self) -> list[Profile]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"Cannot read {self.path}: {exc}") from exc

        if not isinstance(data, dict) or data.get("version") != 1:
            raise ConfigError(f"Unsupported configuration format in {self.path}")
        raw_profiles = data.get("profiles")
        if not isinstance(raw_profiles, list):
            raise ConfigError(f"Invalid profiles list in {self.path}")

        profiles: list[Profile] = []
        try:
            for item in raw_profiles:
                profile = Profile(id=item["id"], name=item["name"], email=item["email"])
                validate_profile(profile)
                profiles.append(profile)
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"Invalid profile in {self.path}: {exc}") from exc
        ids = [profile.id.casefold() for profile in profiles]
        emails = [profile.email.casefold() for profile in profiles]
        if len(ids) != len(set(ids)) or len(emails) != len(set(emails)):
            raise ConfigError(f"Duplicate profile id or email in {self.path}")
        return profiles

    def save(self, profiles: Iterable[Profile]) -> None:
        profile_list = list(profiles)
        for profile in profile_list:
            validate_profile(profile)
        ids = [profile.id.casefold() for profile in profile_list]
        emails = [profile.email.casefold() for profile in profile_list]
        if len(ids) != len(set(ids)):
            raise ConfigError("Profile ids must be unique")
        if len(emails) != len(set(emails)):
            raise ConfigError("Profile email addresses must be unique")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(
                {
                    "version": 1,
                    "profiles": [asdict(profile) for profile in profile_list],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            if os.name != "nt":
                temporary_path.chmod(0o600)
            os.replace(temporary_path, self.path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise ConfigError(f"Cannot write {self.path}: {exc}") from exc

    def add(self, name: str, email: str, profile_id: str | None = None) -> Profile:
        name = name.strip()
        email = email.strip()
        profiles = self.load()
        if any(profile.email.casefold() == email.casefold() for profile in profiles):
            raise ConfigError(f"A profile with email {email!r} already exists")

        base_id = slugify(profile_id or name)
        candidate = base_id
        suffix = 2
        existing_ids = {profile.id.casefold() for profile in profiles}
        while candidate.casefold() in existing_ids:
            candidate = f"{base_id}-{suffix}"
            suffix += 1
        profile = Profile(candidate, name, email)
        validate_profile(profile)
        self.save([*profiles, profile])
        return profile

    def remove(self, selector: str) -> Profile:
        profiles = self.load()
        profile = resolve_profile(profiles, selector)
        self.save(item for item in profiles if item != profile)
        return profile


def validate_profile(profile: Profile) -> None:
    if not profile.id or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", profile.id):
        raise ValueError(
            "profile id must use lowercase letters, numbers, '.', '_' or '-'"
        )
    if not profile.name.strip() or "\n" in profile.name or "\r" in profile.name:
        raise ValueError("name must not be empty or contain a newline")
    if (
        not profile.email.strip()
        or profile.email.count("@") != 1
        or any(character.isspace() for character in profile.email)
        or "\n" in profile.email
        or "\r" in profile.email
    ):
        raise ValueError("email must look like name@example.com")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", value.strip().casefold()).strip("-._")
    if not slug:
        raise ConfigError("Could not create a profile id; pass --id explicitly")
    return slug


def resolve_profile(profiles: Iterable[Profile], selector: str) -> Profile:
    values = list(profiles)
    exact = [
        profile
        for profile in values
        if selector.casefold() in {profile.id.casefold(), profile.email.casefold()}
    ]
    if len(exact) == 1:
        return exact[0]
    by_name = [
        profile for profile in values if profile.name.casefold() == selector.casefold()
    ]
    if len(by_name) == 1:
        return by_name[0]
    if len(by_name) > 1:
        raise ConfigError(f"Profile name {selector!r} is ambiguous; use its id")
    raise ConfigError(f"No profile matches {selector!r}")


def read_legacy_profiles(path: Path) -> list[tuple[str, str]]:
    """Parse legacy config.env without executing it as shell code."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc

    users: dict[int, str] = {}
    emails: dict[int, str] = {}
    pattern = re.compile(r"^(USER|EMAIL)_([1-9][0-9]*)=(.*)$")
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        kind, raw_index, raw_value = match.groups()
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        target = users if kind == "USER" else emails
        target[int(raw_index)] = value

    pairs: list[tuple[str, str]] = []
    for index in sorted(set(users) | set(emails)):
        if not users.get(index) or not emails.get(index):
            raise ConfigError(
                f"Legacy profile {index} needs both USER_{index} and EMAIL_{index}"
            )
        pairs.append((users[index], emails[index]))
    return pairs
