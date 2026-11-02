# -*- coding: utf-8 -*-
"""Helpers for reading ADIF (Amateur Data Interchange Format) files."""

from pathlib import Path


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
