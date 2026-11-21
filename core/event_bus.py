"""
═══════════════════════════════════════════════════════════════════════════════

 GENESIS HR® // OMNIFACTORY EVO
 GEN-OS Platform
 MODULE
-----------------------------------------------------------------------------
 Event Bus
 FILE
-----------------------------------------------------------------------------
 event_bus.py
 BUILD
-----------------------------------------------------------------------------
 0153
 DESCRIPTION
-----------------------------------------------------------------------------
 Центральная шина событий платформы.
 EventBus позволяет полностью отвязать сервисы друг от друга.
 Вместо:
     Registry -> Graph
 Используется:
     Registry
        │
        ▼
     EventBus
        │
        ▼
     Graph
 Любой сервис может:
     emit()
     subscribe()
     unsubscribe()
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging

from collections import defaultdict
from collections.abc import Callable

LOGGER = logging.getLogger("GEN-OS.EventBus")


class EventBus:
    """
    Enterprise Event Bus.
    """

    # ============================================================
    # LIFECYCLE
    # ============================================================

    def __init__(self):
        self._listeners = defaultdict(list)

    # ============================================================
    # SUBSCRIPTIONS
    # ============================================================

    def subscribe(self, event: str, callback: Callable) -> None:
        """
        Subscribe to event.
        """
        if callback not in self._listeners[event]:
            self._listeners[event].append(
                callback
            )
            LOGGER.info(
                "Subscribed %s -> %s",
                callback.__name__,
                event
            )

    # ------------------------------------------------------------

    def unsubscribe(self, event: str, callback: Callable) -> None:
        """
        Remove subscription.
        """
        if callback in self._listeners[event]:
            self._listeners[event].remove(
                callback
            )

    # ============================================================
    # EVENTS
    # ============================================================

    def emit(self, event: str, *args, **kwargs) -> None:
        """
        Emit event.
        """
        listeners = self._listeners.get(
            event,
            []
        )
        LOGGER.info(
            "Event '%s' -> %s listeners",
            event,
            len(listeners)
        )
        for callback in listeners:
            try:
                callback(
                    *args,
                    **kwargs
                )
            except Exception:
                LOGGER.exception(
                    "Listener failed: %s",
                    callback
                )

    # ============================================================
    # INFORMATION
    # ============================================================

    def listeners(self, event: str) -> list[Callable]:
        return list(
            self._listeners.get(
                event,
                []
            )
        )

    # ------------------------------------------------------------

    def events(self) -> list[str]:
        return list(
            self._listeners.keys()
        )

    # ------------------------------------------------------------

    def listener_count(self, event: str) -> int:
        return len(
            self._listeners.get(
                event,
                []
            )
        )

    # ============================================================
    # MAINTENANCE
    # ============================================================

    def clear(self) -> None:
        self._listeners.clear()

    # ------------------------------------------------------------

    def information(self):
        return {
            event: len(callbacks)
            for event, callbacks
            in self._listeners.items()
        }

    # ============================================================
    # MAGIC
    # ============================================================

    def __len__(self):
        return sum(
            len(callbacks)
            for callbacks
            in self._listeners.values()
        )

    # ------------------------------------------------------------

    def __repr__(self):
        return (
            "<EventBus "
            f"events={len(self.events())} "
            f"listeners={len(self)}>"
        )


# ===============================================================
# GLOBAL EVENT BUS
# ===============================================================

event_bus = EventBus()