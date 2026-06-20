"""Persistence abstraction for pyfarm."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SnapshotStore:
    """Stores and retrieves control context snapshots."""

    @abstractmethod
    def save_snapshot(self, grow_id: str, context: Any) -> None:
        """Save a control context snapshot."""
        pass

    @abstractmethod
    def load_snapshot(self, grow_id: str) -> Optional[Any]:
        """Load the latest snapshot for a grow."""
        pass

    @abstractmethod
    def delete_snapshot(self, grow_id: str) -> None:
        """Delete snapshots for a grow."""
        pass


class NullStore(SnapshotStore):
    """No-op storage (for testing)."""

    def save_snapshot(self, grow_id: str, context: Any) -> None:
        pass

    def load_snapshot(self, grow_id: str) -> Optional[Any]:
        return None

    def delete_snapshot(self, grow_id: str) -> None:
        pass
