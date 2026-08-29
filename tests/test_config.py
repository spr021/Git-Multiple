import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from git_multiple.config import (
    ConfigError,
    Profile,
    ProfileStore,
    config_path,
    read_legacy_profiles,
    resolve_profile,
    slugify,
)


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "nested" / "profiles.json"
        self.store = ProfileStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_missing_file_is_an_empty_store(self):
        self.assertEqual(self.store.load(), [])

    def test_add_persists_and_generates_unique_ids(self):
        first = self.store.add("Mary Jane", "mary@example.com")
        second = self.store.add("Mary Jane", "other@example.com")
        self.assertEqual(first.id, "mary-jane")
        self.assertEqual(second.id, "mary-jane-2")
        self.assertEqual(self.store.load(), [first, second])
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 1)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.store.add("Mary", "Mary@Example.com")
        with self.assertRaisesRegex(ConfigError, "already exists"):
            self.store.add("Another", "mary@example.COM")

    def test_invalid_profiles_are_rejected(self):
        invalid = [
            Profile("Bad ID", "Name", "name@example.com"),
            Profile("ok", "", "name@example.com"),
            Profile("ok", "Name", "not-an-email"),
        ]
        for profile in invalid:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.store.save([profile])

    def test_remove_and_resolve_by_id_name_or_email(self):
        profile = self.store.add("Mary Jane", "mary@example.com", "work")
        for selector in ("work", "MARY JANE", "MARY@EXAMPLE.COM"):
            self.assertEqual(resolve_profile(self.store.load(), selector), profile)
        self.assertEqual(self.store.remove("work"), profile)
        self.assertEqual(self.store.load(), [])

    def test_malformed_json_has_actionable_error(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ConfigError, "Cannot read"):
            self.store.load()

    def test_duplicate_ids_in_existing_file_are_rejected(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "profiles": [
                        {"id": "work", "name": "One", "email": "one@example.com"},
                        {"id": "work", "name": "Two", "email": "two@example.com"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ConfigError, "Duplicate"):
            self.store.load()


class LegacyImportTests(unittest.TestCase):
    def test_parser_does_not_execute_shell_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "must-not-exist"
            source = Path(temporary) / "config.env"
            source.write_text(
                "# comment\n"
                "USER_2='Mary Jane'\n"
                "EMAIL_2=mary@example.com\n"
                f"EVIL=$(touch {marker})\n",
                encoding="utf-8",
            )
            self.assertEqual(
                read_legacy_profiles(source), [("Mary Jane", "mary@example.com")]
            )
            self.assertFalse(marker.exists())

    def test_incomplete_pair_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "config.env"
            source.write_text("USER_1=Mary\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "needs both"):
                read_legacy_profiles(source)


class PathTests(unittest.TestCase):
    def test_environment_override_wins(self):
        with mock.patch.dict(os.environ, {"GIT_MULTIPLE_CONFIG": "/tmp/custom.json"}):
            self.assertEqual(config_path(), Path("/tmp/custom.json"))

    def test_slugify(self):
        self.assertEqual(slugify("  Work Account! "), "work-account")
        with self.assertRaises(ConfigError):
            slugify("!!!")


if __name__ == "__main__":
    unittest.main()
