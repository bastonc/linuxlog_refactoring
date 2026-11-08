#!/usr/bin/env python3
"""Move LinuxLog credentials out of settings.cfg into a 0600 .env file.

The application reads these values from the environment (or from ``.env``) and
never writes them back to ``settings.cfg``.  A backup of the original settings
file is created before anything is changed.

Usage:
    python3 migrate_secrets_to_env.py [--dry-run] [--keep-file-values]
"""

import argparse
import shutil
from pathlib import Path

import config_store


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--settings",
        default=str(config_store.SETTINGS_PATH),
        help="path to settings.cfg",
    )
    parser.add_argument(
        "--env-file",
        default=str(config_store.ENV_FILE),
        help="path to the .env file to create",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would change without writing files",
    )
    parser.add_argument(
        "--keep-file-values",
        action="store_true",
        help="write .env but leave the values in settings.cfg",
    )
    args = parser.parse_args(argv)

    settings_path = Path(args.settings).resolve()
    env_path = Path(args.env_file).resolve()

    if not settings_path.is_file():
        print(f"Settings file not found: {settings_path}")
        return 1

    settings = config_store.load_settings(
        path=settings_path,
        env_file=env_path,
        use_env=False,
    )
    env_values = config_store.env_file_values(settings)
    keys = [
        key
        for env_name, key in config_store.ENV_SETTINGS.items()
        if env_name in env_values
    ]

    if not env_values:
        print("Nothing to migrate: credentials are already empty or absent.")
        return 0

    print("Keys to move into the environment:")
    for key in keys:
        print(f"  {key} -> {config_store.env_var_for(key)}")
    print(f"Environment file: {env_path}")

    if args.dry_run:
        print("Dry run: no files were modified.")
        return 0

    backup_path = settings_path.with_name(settings_path.name + ".bak")
    shutil.copy2(settings_path, backup_path)
    config_store.write_env_file(env_values, path=env_path)

    if not args.keep_file_values:
        config_store.blank_settings(keys, path=settings_path)
        # The backup is for restoring non-secret settings only; credentials
        # already live in .env, so do not leave a second copy on disk.
        config_store.blank_settings(keys, path=backup_path)

    print(f"Backup written to: {backup_path}")
    print(f"Secret values written to: {env_path} (mode 0600)")
    if not args.keep_file_values:
        print("Matching values were removed from settings.cfg and its backup.")
    print("Keep .env private and never commit it to version control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
