"""Persistence abstraction for pyfarm."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pyfarm.core.models import SensorReading


@runtime_checkable
class StorageBackend(Protocol):
    """
    Async persistence interface for pyfarm.

    Three orthogonal concerns:
    - Snapshots: full control context for crash recovery
    - Readings: time-series sensor data for analytics
    - Events: audit trail of control/analytics/commerce events
    """

    # ===== Snapshots (crash recovery) =====
    async def write_snapshot(self, ctx: Any) -> None:
        """Persist a control context snapshot from the runner."""
        ...

    async def get_latest_snapshot(self, grow_id: str) -> dict | None:
        """Retrieve the most recent control context snapshot for a grow."""
        ...

    # ===== Time-series readings (analytics input) =====
    async def insert_sensor_reading(self, reading: SensorReading) -> None:
        """Record a sensor reading (temperature, pH, EC, PPFD, etc.)."""
        ...

    async def get_readings(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query sensor readings in a time range."""
        ...

    # ===== Event audit trail (watchdog, analytics, commerce) =====
    async def insert_event(
        self,
        event_type: str,
        event_kind: str,
        message: str,
        timestamp: datetime,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log a control/analytics/commerce event."""
        ...

    async def get_events(
        self,
        grow_id: str,
        start_time: datetime,
        end_time: datetime,
        event_kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query events for a grow in a time range."""
        ...

    async def close(self) -> None:
        """Release connections/resources."""
        ...


class NullBackend:
    """No-op storage (for testing, does nothing)."""

    async def write_snapshot(self, ctx: Any) -> None:
        pass

    async def get_latest_snapshot(self, grow_id: str) -> dict | None:
        return None

    async def insert_sensor_reading(self, reading: Any) -> None:
        pass

    async def get_readings(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return []

    async def insert_event(
        self,
        event_type: str,
        event_kind: str,
        message: str,
        timestamp: datetime,
        data: dict[str, Any] | None = None,
    ) -> None:
        pass

    async def get_events(
        self,
        grow_id: str,
        start_time: datetime,
        end_time: datetime,
        event_kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return []

    async def close(self) -> None:
        pass


def get_backend(
    backend: str | None = None,
    db_path: str | None = None,
) -> StorageBackend:
    """Return a configured :class:`StorageBackend` instance.

    This is the canonical factory for the pyfarm storage layer (consolidated
    into pyfarm-core). Consumers such as pyfarm-analytics and pyfarm-scheduler
    obtain a backend through this function rather than constructing one directly.

    Selection order (highest priority first):

    1. The explicit ``backend`` argument.
    2. The ``PYFARM_STORAGE_BACKEND`` environment variable.
    3. Default: ``"sqlite"``.

    Args:
        backend: ``"sqlite"`` or ``"null"``. If ``None``, read from the
            environment / default.
        db_path: SQLite database path. If ``None``, read from
            ``PYFARM_DB_PATH`` (default ``"pyfarm.db"``). Ignored for ``null``.

    Returns:
        A backend implementing the :class:`StorageBackend` protocol. SQLite
        backends connect lazily on first use, so no ``await`` is required here.
    """
    import os

    choice = (backend or os.environ.get("PYFARM_STORAGE_BACKEND") or "sqlite").lower()

    if choice == "null":
        return NullBackend()
    if choice == "sqlite":
        from pyfarm.core.storage_impl import SQLiteBackend

        path = db_path or os.environ.get("PYFARM_DB_PATH") or "pyfarm.db"
        return SQLiteBackend(path)

    raise ValueError(
        f"Unknown storage backend {choice!r}. Expected 'sqlite' or 'null'."
    )


# Deprecated: kept for back-compat (old repos might reference this type)
class SnapshotStore:
    """Deprecated. Use StorageBackend instead."""
    pass
