"""A small, decoupled event bus for LinuxLog.

Any component may publish a named event without knowing who (if anyone)
subscribes to it.  Subscribers register a callback for an event name and are
notified when that event is published.

This is the first step toward removing the tight coupling between modules
(main window, cluster, QTH map, settings, ...) that currently rely on global
variables and direct method calls.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from PyQt6.QtCore import QObject, QMetaObject, Qt, pyqtSignal


class EventBus(QObject):
    """Process-wide publish/subscribe event bus.

    Events are identified by a short string name (for example
    ``"callsign.changed"`` or ``"cluster.spot"``).  The payload is an
    arbitrary Python object; subscribers are responsible for validating it.
    """

    _instance: "EventBus | None" = None

    # Emitted for every published event so that Qt slots can react across
    # thread boundaries when needed.
    event_published = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    @classmethod
    def instance(cls) -> "EventBus":
        """Return the shared process-wide event bus (created on demand)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """Register *callback* for *event_name*."""
        self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """Remove a previously registered *callback*."""
        callbacks = self._subscribers.get(event_name)
        if not callbacks:
            return
        try:
            callbacks.remove(callback)
        except ValueError:
            pass

    def publish(self, event_name: str, payload: Any = None) -> None:
        """Notify every subscriber of *event_name*.

        Callbacks are invoked synchronously in the publishing thread.  For
        cross-thread delivery, connect to :attr:`event_published` with a
        queued connection instead.
        """
        self.event_published.emit(event_name, payload)
        for callback in list(self._subscribers.get(event_name, ())):
            try:
                callback(payload)
            except Exception:  # pragma: no cover - defensive
                # Never let one subscriber break the publisher.
                import logging

                logging.getLogger(__name__).exception(
                    "Event subscriber raised for %s", event_name
                )

    def clear(self) -> None:
        """Remove all subscribers (useful for tests)."""
        self._subscribers.clear()


# Convenience module-level helpers.
_bus = EventBus.instance()


def subscribe(event_name: str, callback: Callable[[Any], None]) -> None:
    _bus.subscribe(event_name, callback)


def unsubscribe(event_name: str, callback: Callable[[Any], None]) -> None:
    _bus.unsubscribe(event_name, callback)


def publish(event_name: str, payload: Any = None) -> None:
    _bus.publish(event_name, payload)