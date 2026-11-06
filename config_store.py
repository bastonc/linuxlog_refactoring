"""Shared, format-preserving access to LinuxLog's key=value settings file."""

import os
import stat
import tempfile
from pathlib import Path


SETTINGS_PATH = Path(__file__).parent / "settings.cfg"


def load_settings(path=SETTINGS_PATH):
    """Load settings while allowing '=' characters inside values."""
    settings = {}
    with Path(path).open("r", encoding="utf-8") as settings_file:
        for line in settings_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            settings[key.strip()] = value.strip()
    return settings


def _write_lines(settings_path, lines):
    file_mode = stat.S_IMODE(settings_path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{settings_path.name}.", suffix=".tmp", dir=settings_path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as settings_file:
            settings_file.writelines(lines)
            settings_file.flush()
            os.fsync(settings_file.fileno())
        os.chmod(temporary_name, file_mode)
        os.replace(temporary_name, settings_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def update_settings(values, path=SETTINGS_PATH):
    """Update existing keys, preserving comments and unrelated file lines."""
    settings_path = Path(path).resolve()
    with settings_path.open("r", encoding="utf-8", newline="") as settings_file:
        lines = settings_file.readlines()

    normalized_values = {str(key): str(value).replace("\r", " ").replace("\n", " ")
                         for key, value in values.items()}
    for index, line in enumerate(lines):
        content = line.rstrip("\r\n")
        if not content.strip() or content.lstrip().startswith("#") or "=" not in content:
            continue
        key, _value = content.split("=", 1)
        if key in normalized_values:
            lines[index] = f"{key}={normalized_values[key]}\n"

    _write_lines(settings_path, lines)
    return True


def validate_settings(settings, required=None):
    """Return a list of human-readable configuration problems."""
    if required is None:
        required = (
            "db-host",
            "db-user",
            "db-pass",
            "db-name",
            "my-call",
            "telnet-host",
            "telnet-port",
        )
    problems = []
    for key in required:
        if not str(settings.get(key, "")).strip():
            problems.append(f"Missing or empty setting: {key}")
    port = settings.get("telnet-port")
    if port not in (None, ""):
        try:
            int(port)
        except (TypeError, ValueError):
            problems.append(f"telnet-port must be an integer, got {port!r}")
    for opacity_key in ("logWindow-opacity", "clusterWindow-opacity"):
        value = settings.get(opacity_key)
        if value not in (None, ""):
            try:
                opacity = float(value)
            except (TypeError, ValueError):
                problems.append(f"{opacity_key} must be a number, got {value!r}")
                continue
            if not 0.0 <= opacity <= 1.0:
                problems.append(f"{opacity_key} must be between 0 and 1, got {value!r}")
    return problems


def ensure_settings(values, path=SETTINGS_PATH):
    """Append keys that are still missing; existing keys are not touched."""
    settings_path = Path(path).resolve()
    with settings_path.open("r", encoding="utf-8", newline="") as settings_file:
        lines = settings_file.readlines()

    normalized_values = {str(key): str(value).replace("\r", " ").replace("\n", " ")
                         for key, value in values.items()}
    existing_keys = set()
    for line in lines:
        content = line.rstrip("\r\n")
        if not content.strip() or content.lstrip().startswith("#") or "=" not in content:
            continue
        key, _value = content.split("=", 1)
        existing_keys.add(key)

    missing = [
        (key, value)
        for key, value in normalized_values.items()
        if key not in existing_keys
    ]
    if not missing:
        return False

    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] += "\n"
    lines.extend(f"{key}={value}\n" for key, value in missing)

    _write_lines(settings_path, lines)
    return True
