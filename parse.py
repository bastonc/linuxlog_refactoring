# -*- coding: utf-8 -*-
"""Helpers for reading and normalizing ADIF (Amateur Data Interchange
Format) files."""

import datetime
import re
from pathlib import Path


_COLON_TIME_RE = re.compile(
    r"^\s*(\d{1,2})\s*:\s*(\d{1,2})(?:\s*:\s*(\d{1,2})(?:\.\d+)?)?\s*$"
)
_DIGITS_RE = re.compile(r"\D")


def normalize_adi_time(value):
    """Return a valid ADIF time as exactly six digits (``HHMMSS``).

    Real-world ADIF files are not always strict.  This accepts:

    * ``HHMMSS`` and ``HHMM`` / ``HMM`` (seconds default to zero);
    * five-digit values produced by older exports where the leading zero of
      the hour was lost (``92700`` -> ``092700``);
    * ``H:MM`` / ``HH:MM:SS`` (with optional fractional seconds);
    * ``datetime.time`` / ``datetime.datetime`` and ``datetime.timedelta``
      values (MySQL ``TIME`` columns are returned as timedeltas).

    Returns an empty string when the value cannot be interpreted.
    """
    if value is None:
        return ""
    if isinstance(value, datetime.timedelta):
        seconds = int(value.total_seconds()) % 86400
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}{minutes:02d}{seconds:02d}"
    if isinstance(value, datetime.datetime):
        return value.strftime("%H%M%S")
    if isinstance(value, datetime.time):
        return value.strftime("%H%M%S")

    text = str(value).strip()
    if not text:
        return ""
    if ":" not in text and "." in text:
        # Accept values such as ``235959.000`` produced by some exporters.
        text = text.split(".", 1)[0].strip()

    match = _COLON_TIME_RE.match(text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3) or 0)
    elif text.isdigit() and len(text) <= 6:
        if len(text) <= 2:
            hours, minutes, seconds = int(text), 0, 0
        elif len(text) == 3:
            digits = text.zfill(4)
            hours, minutes, seconds = int(digits[:2]), int(digits[2:]), 0
        elif len(text) == 4:
            hours, minutes, seconds = int(text[:2]), int(text[2:]), 0
        elif len(text) == 5:
            # Leading zero of the hour was lost (``92700`` = 09:27:00).
            digits = text.zfill(6)
            hours = int(digits[:2])
            minutes = int(digits[2:4])
            seconds = int(digits[4:])
        else:
            hours = int(text[:2])
            minutes = int(text[2:4])
            seconds = int(text[4:])
    else:
        return ""

    if hours > 23 or minutes > 59 or seconds > 59:
        return ""
    return f"{hours:02d}{minutes:02d}{seconds:02d}"


def normalize_adi_date(value):
    """Return a valid ADIF date as exactly eight digits (``YYYYMMDD``)."""
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y%m%d")

    text = str(value).strip()
    if not text:
        return ""
    # Some exporters append a time to the date; the date is the first part.
    text = text.split()[0]
    digits = _DIGITS_RE.sub("", text)
    if len(digits) != 8:
        return ""
    try:
        datetime.date(int(digits[:4]), int(digits[4:6]), int(digits[6:]))
    except ValueError:
        return ""
    return digits


def _iter_adi_fields(text):
    """Yield ``(name, value)`` pairs from ADIF text.

    ADIF values with a declared length are read by character count, so values
    containing ``<`` or whitespace are not mistaken for the next field.
    Malformed tags are skipped without aborting the rest of the import.
    """
    position = 0
    text_length = len(text)
    while position < text_length:
        start = text.find("<", position)
        if start < 0:
            return
        end = text.find(">", start + 1)
        if end < 0:
            return

        descriptor = text[start + 1:end].strip()
        parts = descriptor.split(":")
        name = parts[0].strip().upper()
        position = end + 1
        if not name:
            continue

        length = None
        if len(parts) > 1 and parts[1].strip().isdigit():
            length = int(parts[1].strip())
        if length is not None:
            value = text[position:position + length]
            position += length
        elif name in {"EOR", "EOH"}:
            value = ""
        else:
            next_tag = text.find("<", position)
            if next_tag < 0:
                value = text[position:].strip()
                position = text_length
            else:
                value = text[position:next_tag].strip()
                position = next_tag

        yield name, value


def adi_normilzer(tags: dict, fields_adi_standart: list, settings_dict):
    """Fill expected ADIF fields while preserving the caller's dictionary."""
    for field in fields_adi_standart:
        if tags.get(field) is not None:
            continue
        tags[field] = settings_dict.get("my-call", "") if field == "OPERATOR" else ""
    return tags


def parseStringAdi(string, adi_fields_standart=None, settings_dict=None):
    """Parse one ADIF record string into a dictionary of uppercase fields."""
    tags = {}
    for name, value in _iter_adi_fields(string):
        if name in {"EOR", "EOH"}:
            continue
        tags[name] = value
    if adi_fields_standart is not None:
        adi_normilzer(tags, adi_fields_standart, settings_dict or {})
    return tags


def getAllRecord(poles, filename, key=""):
    """Read an ADIF file and return its QSO records.

    Parsing is record based rather than line based, as valid ADIF files may
    put several records on one line or wrap a record across multiple lines.
    """
    path = Path(__file__).parent / filename
    with path.open("r", encoding="utf-8", errors="ignore") as adi_file:
        text = adi_file.read()

    records = []
    record = {}
    # ADIF without a header starts directly with a tag. Starting in record
    # mode in this case preserves fields such as BAND that can precede CALL.
    first_content = text.lstrip("\ufeff \t\r\n")
    in_records = first_content.startswith("<")
    for name, value in _iter_adi_fields(text):
        if name == "EOH":
            in_records = True
        elif name == "EOR":
            if in_records and record:
                for field in poles:
                    record.setdefault(field, " ")
                records.append(record)
            record = {}
            in_records = True
        elif in_records or name in {"CALL", "QSO_DATE", "TIME_ON", "FREQ"}:
            in_records = True
            record[name] = value.replace("\n", "")

    return records
