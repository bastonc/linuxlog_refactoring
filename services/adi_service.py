"""ADIF import/export helpers.

These functions are intentionally free of Qt dependencies so they can be unit
tested and reused by both the GUI and future command-line tools.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import parse
import std


def normalize_time(value: Any) -> str:
    """Normalize an ADIF/MySQL time value to ``HHMMSS``."""
    return parse.normalize_adi_time(value)


def normalize_date(value: Any) -> str:
    """Normalize an ADIF/MySQL date value to ``YYYYMMDD``."""
    return parse.normalize_adi_date(value)


def export_records(
    records: List[Dict[str, Any]],
    fields: List[Any],
    output_path: str | Path,
    app_version: str,
    settings: Dict[str, Any],
) -> None:
    """Write *records* to an ADIF file at *output_path*.

    Frequencies, dates and times are normalized before writing so that the
    resulting file can be re-imported without conversion errors.
    """
    from main import Adi_file, _format_adi_field  # local import avoids cycles

    writer = Adi_file(app_version, settings, str(output_path))
    writer.record_dict_qso(list(records), list(fields), name_file=str(output_path))