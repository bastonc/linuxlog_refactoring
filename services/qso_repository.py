"""Repository for QSO persistence.

This module wraps the legacy ``main.Db`` implementation behind a small,
typed interface.  New code should depend on :class:`QsoRepository` instead of
``main.Db`` directly so the storage backend can be replaced later.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import main


class QsoRepository:
    """Thin wrapper around :class:`main.Db`."""

    def __init__(self, settings: Dict[str, Any]):
        self._db = main.Db(settings)

    def record_qso(self, qso: Dict[str, Any], mode: str = "") -> Optional[int]:
        return self._db.record_qso_to_base(qso, mode=mode)

    def search_qso(self, call: str, qso_date: str, time_on: str, band: str, mode: str) -> Any:
        return self._db.search_qso_by_full_data(call, qso_date, time_on, band, mode)

    def search_qso_in_base(self, call: str) -> Any:
        return self._db.search_qso_in_base(call)

    def all_records(self, count: int = 0) -> List[Dict[str, Any]]:
        return self._db.get_all_records(count=count)