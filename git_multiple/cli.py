"""Command-line interface for Git Multiple."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .config import (
    ConfigError,
    Profile,
    ProfileStore,
    read_legacy_profiles,
    resolve_profile,
)
from .git import GitConfig, GitError, Identity


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="git-multiple",
        description="Save Git identities and switch user.name/user.email safely.",
    )
    root.add_argument(
        "--version", action="version", version=f"git-multiple {__version__}"
    )
    commands = root.add_subparsers(dest="command")

    add = commands.add_parser("add", help="save a new identity")
    add.add_argument("--name", help="Git author name")
    add.add_argument("--email", help="Git author email")
    add.add_argument("--id", dest="profile_id", help="short unique profile id")

    commands.add_parser("list", aliases=["ls"], help="list saved identities")

    use = commands.add_parser("use", help="apply a saved identity")
    use.add_argument("profile", help="profile id, exact name, or email")
    use.add_argument("--scope", choices=("global", "local"), default="global")

    current = commands.add_parser("current", help="show the active Git identity")
    current.add_argument("--scope", choices=("global", "local"), default="global")

    remove = commands.add_parser(
        "remove", aliases=["rm"], help="remove a saved identity"
    )
    remove.add_argument("profile", help="profile id, exact name, or email")
    remove.add_argument(
        "--yes", action="store_true", help="do not ask for confirmation"
    )

    migrate = commands.add_parser(
        "import-legacy", help="import a legacy config.env safely"
    )
    migrate.add_argument("path", nargs="?", default="config.env")

    commands.add_parser("config-path", help="print the profile file location")
    commands.add_parser("doctor", help="check Git and configuration")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Preserve the most useful flags from the original Bash script.
    if arguments[:1] in (["-a"], ["--add"]):
        arguments[0] = "add"
    elif arguments[:1] in (["-l"], ["--list"]):
        arguments[0] = "list"
    elif arguments[:1] == ["-v"]:
        arguments[0] = "--version"

    args = parser().parse_args(arguments)
    store = ProfileStore()
    git = GitConfig()
    try:
        if args.command is None:
            return interactive(store, git)
        if args.command == "add":
            name = args.name or _prompt("Git author name: ")
            email = args.email or _prompt("Git author email: ")
            profile = store.add(name, email, args.profile_id)
            print(f"Added {profile.id}: {profile.name} <{profile.email}>")
            return 0
        if args.command in {"list", "ls"}:
            return list_profiles(store, git)
        if args.command == "use":
            profile = resolve_profile(store.load(), args.profile)
            git.set_identity(profile, args.scope)
            print(f"Now using {profile.name} <{profile.email}> ({args.scope})")
            return 0
        if args.command == "current":
            identity = git.get_identity(args.scope)
            print(format_identity(identity))
            return 0 if identity.name or identity.email else 1
        if args.command in {"remove", "rm"}:
            profile = resolve_profile(store.load(), args.profile)
            if not args.yes and not _confirm(f"Remove {profile.id}? [y/N] "):
                print("Cancelled")
                return 0
            store.remove(profile.id)
            print(f"Removed {profile.id}")
            return 0
        if args.command == "import-legacy":
            return import_legacy(store, Path(args.path))
        if args.command == "config-path":
            print(store.path)
            return 0
        if args.command == "doctor":
            git.ensure_available()
            profiles = store.load()
            print("Git: available")
            print(f"Configuration: {store.path} ({len(profiles)} profile(s))")
            return 0
    except (ConfigError, GitError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


def interactive(store: ProfileStore, git: GitConfig) -> int:
    profiles = store.load()
    if not profiles:
        print("No profiles saved. Add one with: git-multiple add")
        return 1
    if not sys.stdin.isatty():
        print(
            "error: choose a profile with 'git-multiple use PROFILE'", file=sys.stderr
        )
        return 2

    current = git.get_identity("global")
    print(f"Current (global): {format_identity(current)}")
    for index, profile in enumerate(profiles, start=1):
        marker = "*" if _matches(current, profile) else " "
        print(f"{index:>2}. {marker} {profile.id}: {profile.name} <{profile.email}>")
    print(" 0. Cancel")
    choice = _prompt("Select a profile: ")
    try:
        selected = int(choice)
    except ValueError:
        raise ConfigError("Selection must be a number")
    if selected == 0:
        return 0
    if selected < 1 or selected > len(profiles):
        raise ConfigError("Selection is outside the displayed range")
    profile = profiles[selected - 1]
    git.set_identity(profile, "global")
    print(f"Now using {profile.name} <{profile.email}> (global)")
    return 0


def list_profiles(store: ProfileStore, git: GitConfig) -> int:
    profiles = store.load()
    if not profiles:
        print("No profiles saved.")
        return 0
    try:
        current = git.get_identity("global")
    except GitError:
        current = Identity(None, None)
    for profile in profiles:
        marker = "*" if _matches(current, profile) else " "
        print(f"{marker} {profile.id}: {profile.name} <{profile.email}>")
    return 0


def import_legacy(store: ProfileStore, path: Path) -> int:
    pairs = read_legacy_profiles(path)
    if not pairs:
        raise ConfigError(f"No complete profiles found in {path}")
    imported = 0
    skipped = 0
    for name, email in pairs:
        try:
            store.add(name, email)
            imported += 1
        except ConfigError as exc:
            if "already exists" not in str(exc):
                raise
            skipped += 1
    print(f"Imported {imported} profile(s); skipped {skipped} duplicate(s).")
    return 0


def format_identity(identity: Identity) -> str:
    if identity.name and identity.email:
        return f"{identity.name} <{identity.email}>"
    if identity.name:
        return f"{identity.name} (email is not set)"
    if identity.email:
        return f"<{identity.email}> (name is not set)"
    return "not configured"


def _matches(identity: Identity, profile: Profile) -> bool:
    return identity.name == profile.name and identity.email == profile.email


def _prompt(message: str) -> str:
    try:
        return input(message).strip()
    except EOFError as exc:
        raise ConfigError("Input ended before a value was provided") from exc


def _confirm(message: str) -> bool:
    return _prompt(message).casefold() in {"y", "yes"}
