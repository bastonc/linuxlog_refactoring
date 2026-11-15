"""Shared, format-preserving access to LinuxLog's settings and secrets.

Settings live in ``settings.cfg``.  The operator callsign and service
credentials may also be supplied through environment variables (or a local
``.env`` file with mode 0600).  Environment values take precedence and are
never written back to ``settings.cfg``.
"""

import os
import re
import stat
import tempfile
from pathlib import Path


SETTINGS_PATH = Path(__file__).parent / "settings.cfg"
ENV_FILE = Path(__file__).parent / ".env"

# Environment variable -> settings.cfg key.
ENV_SETTINGS = {
    "LINUXLOG_MY_CALL": "my-call",
    "LINUXLOG_DB_PASS": "db-pass",
    "LINUXLOG_EQSL_PASSWORD": "eqsl_password",
    "LINUXLOG_CLUBLOG_PASS": "pass-clublog",
    "LINUXLOG_QRZ_PASSWORD": "qrz-com-password",
    "LINUXLOG_QRZ_APP_KEY": "qrz-com-app-key",
}

SECRET_KEYS = frozenset({
    "db-pass",
    "eqsl_password",
    "pass-clublog",
    "qrz-com-password",
    "qrz-com-app-key",
})

ENV_MANAGED_SETTING_KEYS = frozenset(ENV_SETTINGS.values())

_ENV_LINE_RE = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
)


def _parse_env_value(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    # Drop an unquoted trailing comment.
    if " #" in raw:
        raw = raw.split(" #", 1)[0].rstrip()
    return raw


def read_env_file(path=ENV_FILE):
    """Return key/value pairs from a ``.env`` file (empty when absent)."""
    env_path = Path(path)
    if not env_path.is_file():
        return {}
    values = {}
    with env_path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            match = _ENV_LINE_RE.match(line)
            if not match:
                continue
            values[match.group(1)] = _parse_env_value(match.group(2))
    return values


def env_overrides(environ=None, env_file=ENV_FILE):
    """Return settings supplied by environment variables or ``.env``.

    Process environment variables win over values from the file.  Empty
    values are ignored so an accidentally exported empty variable does not
    wipe a working configuration.
    """
    environ = os.environ if environ is None else environ
    overrides = {}

    for name, value in read_env_file(env_file).items():
        key = ENV_SETTINGS.get(name)
        if key is not None and value.strip() != "":
            overrides[key] = value

    for name, key in ENV_SETTINGS.items():
        if name in environ:
            value = str(environ[name])
            if value.strip() != "":
                overrides[key] = value
    return overrides


def process_env_overrides(environ=None):
    """Return settings supplied by real process environment variables only."""
    environ = os.environ if environ is None else environ
    overrides = {}
    for name, key in ENV_SETTINGS.items():
        if name in environ:
            value = str(environ[name])
            if value.strip() != "":
                overrides[key] = value
    return overrides


def process_env_managed_keys(environ=None):
    """Return keys controlled by exported variables (not by ``.env``)."""
    return frozenset(process_env_overrides(environ=environ))


def env_managed_keys(environ=None, env_file=ENV_FILE):
    """Return settings keys that currently come from the environment."""
    return frozenset(env_overrides(environ=environ, env_file=env_file))


def is_process_env_managed(key, environ=None):
    return key in process_env_managed_keys(environ=environ)


def env_var_for(key):
    """Return the environment variable name that supplies *key*, if any."""
    for name, mapped_key in ENV_SETTINGS.items():
        if mapped_key == key:
            return name
    return None


def is_env_managed(key, environ=None, env_file=ENV_FILE):
    return key in env_managed_keys(environ=environ, env_file=env_file)


def env_file_values(settings):
    """Map known settings keys to their environment variable names."""
    return {
        env_name: str(settings[key])
        for env_name, key in ENV_SETTINGS.items()
        if str(settings.get(key, "")).strip() != ""
    }


def write_env_file(values, path=ENV_FILE):
    """Create or update a 0600 ``.env`` file, preserving unrelated lines."""
    env_path = Path(path)
    normalized = {
        str(key): str(value).replace("\r", " ").replace("\n", " ")
        for key, value in values.items()
    }
    lines = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    seen = set()
    for index, line in enumerate(lines):
        match = _ENV_LINE_RE.match(line)
        if not match or match.group(1) not in normalized:
            continue
        name = match.group(1)
        lines[index] = f"{name}={normalized[name]}\n"
        seen.add(name)

    missing = [name for name in normalized if name not in seen]
    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] += "\n"
    lines.extend(f"{name}={normalized[name]}\n" for name in missing)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{env_path.name}.", suffix=".tmp", dir=env_path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as env_file:
            env_file.writelines(lines)
            env_file.flush()
            os.fsync(env_file.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, env_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return True


def blank_settings(keys, path=SETTINGS_PATH):
    """Blank *keys* in settings.cfg while preserving comments and other lines."""
    settings_path = Path(path).resolve()
    keys = {str(key) for key in keys}
    with settings_path.open("r", encoding="utf-8", newline="") as settings_file:
        lines = settings_file.readlines()

    for index, line in enumerate(lines):
        content = line.rstrip("\r\n")
        if not content.strip() or content.lstrip().startswith("#") or "=" not in content:
            continue
        key, _value = content.split("=", 1)
        if key in keys:
            lines[index] = f"{key}=\n"

    _write_lines(settings_path, lines)
    return True


def load_settings(path=SETTINGS_PATH, environ=None, env_file=ENV_FILE, use_env=True):
    """Load settings while allowing '=' characters inside values.

    Values from the process environment (and from ``.env``) override the file,
    so credentials can stay out of ``settings.cfg``.
    """
    settings = {}
    with Path(path).open("r", encoding="utf-8") as settings_file:
        for line in settings_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            settings[key.strip()] = value.strip()
    if use_env:
        settings.update(env_overrides(environ=environ, env_file=env_file))
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


def update_settings(values, path=SETTINGS_PATH, environ=None, env_file=ENV_FILE):
    """Update existing keys, preserving comments and unrelated file lines.

    Keys exported in the process environment are skipped because they cannot
    be changed from the GUI.  Credential keys stored in ``.env`` can still be
    edited: new values are written back to the 0600 ``.env`` file and left
    blank in ``settings.cfg`` so secrets never end up in the settings file.
    """
    settings_path = Path(path).resolve()
    managed = process_env_managed_keys(environ=environ)
    with settings_path.open("r", encoding="utf-8", newline="") as settings_file:
        lines = settings_file.readlines()

    env_values = {}
    normalized_values = {}
    for raw_key, raw_value in values.items():
        key = str(raw_key)
        if key in managed:
            continue
        value = str(raw_value).replace("\r", " ").replace("\n", " ")
        if key in ENV_MANAGED_SETTING_KEYS:
            env_name = env_var_for(key)
            if env_name is not None:
                env_values[env_name] = value
            normalized_values[key] = ""
        else:
            normalized_values[key] = value

    if env_values:
        write_env_file(env_values, path=env_file)

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


def ensure_settings(values, path=SETTINGS_PATH, environ=None, env_file=ENV_FILE):
    """Append keys that are still missing; existing keys are not touched.

    Environment-managed keys are never appended, which keeps secrets out of
    ``settings.cfg``.
    """
    settings_path = Path(path).resolve()
    managed = env_managed_keys(environ=environ, env_file=env_file)
    with settings_path.open("r", encoding="utf-8", newline="") as settings_file:
        lines = settings_file.readlines()

    normalized_values = {
        str(key): str(value).replace("\r", " ").replace("\n", " ")
        for key, value in values.items()
        if str(key) not in managed and str(key) not in ENV_MANAGED_SETTING_KEYS
    }
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
