"""One-time database setup for packaged LinuxLog installs.

Run as root during package installation.  Creates the MariaDB database and
user (if necessary) and stores the password in the application's .env file.
"""
import subprocess
import sys
from pathlib import Path

APP_DIR = Path("/opt/linuxlog")
sys.path.insert(0, str(APP_DIR))
from config_store import (
    blank_settings,
    load_settings,
    update_settings,
    write_env_file,
    ENV_MANAGED_SETTING_KEYS,
)

DEFAULT_DB_PASS = "Linuxlog12#"


def main():
    settings_path = APP_DIR / "settings.cfg"
    env_path = APP_DIR / ".env"

    settings = load_settings(path=settings_path, env_file=env_path, use_env=False)
    db_name = str(settings.get("db-name") or "linuxlog").strip() or "linuxlog"
    db_user = str(settings.get("db-user") or "linuxlog").strip() or "linuxlog"

    # Reuse an existing password if one is already stored.
    try:
        from config_store import read_env_file
        db_pass = read_env_file(path=env_path).get("LINUXLOG_DB_PASS", "").strip()
    except Exception:
        db_pass = ""
    if not db_pass:
        db_pass = DEFAULT_DB_PASS

    # Make sure MariaDB is running.
    subprocess.run(
        ["systemctl", "enable", "--now", "mariadb"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    escaped_pass = db_pass.replace("'", "''")
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
        f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' "
        f"IDENTIFIED BY '{escaped_pass}';\n"
        f"ALTER USER '{db_user}'@'localhost' IDENTIFIED BY '{escaped_pass}';\n"
        f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost';\n"
        f"FLUSH PRIVILEGES;\n"
    )
    subprocess.run(
        ["mariadb", "-u", "root", "-e", sql],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    write_env_file({"LINUXLOG_DB_PASS": db_pass}, path=env_path)
    blank_settings(ENV_MANAGED_SETTING_KEYS, path=settings_path)
    update_settings({"db-name": db_name, "db-user": db_user}, path=settings_path, env_file=env_path)

    # Secure permissions.
    try:
        settings_path.chmod(0o600)
        env_path.chmod(0o600)
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"linuxlog: database setup failed: {error}", file=sys.stderr)
        sys.exit(0)
