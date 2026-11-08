import tempfile
import unittest
from pathlib import Path

import config_store


class ConfigStoreEnvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.settings = self.dir / "settings.cfg"
        self.settings.write_text(
            "my-call=OLD\ndb-pass=FILE_SECRET\ndb-user=user\n",
            encoding="utf-8",
        )
        self.env_file = self.dir / ".env"

    def test_process_env_overrides_file(self):
        settings = config_store.load_settings(
            path=self.settings,
            environ={"LINUXLOG_MY_CALL": "NEW", "LINUXLOG_DB_PASS": "ENV_SECRET"},
            env_file=self.env_file,
        )
        self.assertEqual(settings["my-call"], "NEW")
        self.assertEqual(settings["db-pass"], "ENV_SECRET")
        self.assertEqual(settings["db-user"], "user")

    def test_env_file_is_loaded_and_process_env_wins(self):
        self.env_file.write_text("LINUXLOG_DB_PASS=FROM_FILE\n", encoding="utf-8")
        settings = config_store.load_settings(
            path=self.settings, environ={}, env_file=self.env_file
        )
        self.assertEqual(settings["db-pass"], "FROM_FILE")

        settings = config_store.load_settings(
            path=self.settings,
            environ={"LINUXLOG_DB_PASS": "FROM_PROCESS"},
            env_file=self.env_file,
        )
        self.assertEqual(settings["db-pass"], "FROM_PROCESS")

    def test_empty_environment_value_is_ignored(self):
        settings = config_store.load_settings(
            path=self.settings,
            environ={"LINUXLOG_DB_PASS": ""},
            env_file=self.env_file,
        )
        self.assertEqual(settings["db-pass"], "FILE_SECRET")

    def test_update_settings_skips_env_managed_keys(self):
        config_store.update_settings(
            {"db-pass": "NEW_SECRET", "db-user": "newuser"},
            path=self.settings,
            environ={"LINUXLOG_DB_PASS": "ENV_SECRET"},
            env_file=self.env_file,
        )
        text = self.settings.read_text(encoding="utf-8")
        self.assertIn("db-pass=FILE_SECRET", text)
        self.assertIn("db-user=newuser", text)
        self.assertNotIn("NEW_SECRET", text)

    def test_update_settings_routes_credentials_to_env_file(self):
        config_store.update_settings(
            {"db-pass": "NEW_SECRET", "db-user": "newuser"},
            path=self.settings,
            environ={},
            env_file=self.env_file,
        )
        text = self.settings.read_text(encoding="utf-8")
        self.assertIn("db-pass=\n", text)
        self.assertIn("db-user=newuser", text)
        self.assertNotIn("NEW_SECRET", text)

        env_text = self.env_file.read_text(encoding="utf-8")
        self.assertIn("LINUXLOG_DB_PASS=NEW_SECRET", env_text)
        self.assertEqual(self.env_file.stat().st_mode & 0o777, 0o600)

    def test_env_file_values_can_be_edited_from_settings(self):
        self.env_file.write_text("LINUXLOG_DB_PASS=OLD_SECRET\n", encoding="utf-8")
        config_store.update_settings(
            {"db-pass": "Linuxlog12#"},
            path=self.settings,
            environ={},
            env_file=self.env_file,
        )
        text = self.settings.read_text(encoding="utf-8")
        self.assertIn("db-pass=\n", text)
        self.assertNotIn("Linuxlog12#", text)
        self.assertIn(
            "LINUXLOG_DB_PASS=Linuxlog12#",
            self.env_file.read_text(encoding="utf-8"),
        )

    def test_hash_in_password_is_not_treated_as_comment(self):
        self.env_file.write_text(
            "LINUXLOG_DB_PASS=Linuxlog12#\n", encoding="utf-8"
        )
        values = config_store.read_env_file(path=self.env_file)
        self.assertEqual(values["LINUXLOG_DB_PASS"], "Linuxlog12#")

    def test_process_env_managed_keys_ignores_env_file(self):
        self.env_file.write_text("LINUXLOG_DB_PASS=FROM_FILE\n", encoding="utf-8")
        self.assertEqual(
            config_store.process_env_managed_keys(environ={}),
            frozenset(),
        )
        self.assertIn(
            "db-pass",
            config_store.process_env_managed_keys(
                environ={"LINUXLOG_DB_PASS": "FROM_PROCESS"}
            ),
        )

    def test_ensure_settings_does_not_append_env_managed_keys(self):
        config_store.ensure_settings(
            {"db-pass": "NEW_SECRET", "new-key": "value"},
            path=self.settings,
            environ={"LINUXLOG_DB_PASS": "ENV_SECRET"},
            env_file=self.env_file,
        )
        text = self.settings.read_text(encoding="utf-8")
        self.assertNotIn("NEW_SECRET", text)
        self.assertIn("new-key=value", text)

    def test_blank_settings_clears_only_requested_keys(self):
        config_store.blank_settings({"db-pass"}, path=self.settings)
        text = self.settings.read_text(encoding="utf-8")
        self.assertIn("db-pass=\n", text)
        self.assertIn("my-call=OLD", text)

    def test_env_file_values_maps_settings_to_env_names(self):
        values = config_store.env_file_values(
            {"my-call": "UR4LGA", "db-pass": "", "qrz-com-app-key": "key"}
        )
        self.assertEqual(values["LINUXLOG_MY_CALL"], "UR4LGA")
        self.assertEqual(values["LINUXLOG_QRZ_APP_KEY"], "key")
        self.assertNotIn("LINUXLOG_DB_PASS", values)

    def test_write_env_file_sets_private_permissions(self):
        config_store.write_env_file({"LINUXLOG_DB_PASS": "secret"}, path=self.env_file)
        self.assertEqual(self.env_file.stat().st_mode & 0o777, 0o600)
        self.assertIn("LINUXLOG_DB_PASS=secret", self.env_file.read_text(encoding="utf-8"))

    def test_write_env_file_preserves_unrelated_lines(self):
        self.env_file.write_text(
            "# comment\nOTHER=1\nLINUXLOG_DB_PASS=old\n", encoding="utf-8"
        )
        config_store.write_env_file({"LINUXLOG_DB_PASS": "new"}, path=self.env_file)
        text = self.env_file.read_text(encoding="utf-8")
        self.assertIn("# comment", text)
        self.assertIn("OTHER=1", text)
        self.assertIn("LINUXLOG_DB_PASS=new", text)
        self.assertNotIn("LINUXLOG_DB_PASS=old", text)


if __name__ == "__main__":
    unittest.main()
