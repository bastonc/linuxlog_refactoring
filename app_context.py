"""Application-wide context.

This object groups the long-lived objects that used to be stored in module
globals.  Passing it explicitly makes dependencies visible and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AppContext:
    settings: Dict[str, Any]
    app: Optional[Any] = None
    log_window: Optional[Any] = None
    log_search: Optional[Any] = None
    internet_search: Optional[Any] = None
    qth_map: Optional[Any] = None
    log_form: Optional[Any] = None
    telnet_cluster: Optional[Any] = None
    db: Optional[Any] = None

    # Convenience alias kept for gradual migration.
    settings_dict: Dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.settings_dict = self.settings