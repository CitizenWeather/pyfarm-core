"""Persistence abstraction for the live control context.

The *interface* lives in core so any consumer can persist run state through a
common contract; concrete stores that know the full ``ControlContext`` shape
(``JsonSnapshotStore``, ``SQLiteStore``) live in ``pyfarm-control`` and subclass
:class:`SnapshotStore`.

The default :class:`NullStore` is a no-op, so a runner with no persistence
configured needs no special-casing.
"""

from __future__ import annotations

import abc
from typing import Protocol, runtime_checkable


@runtime_checkable
class SnapshotContext(Protocol):
    """The minimal surface a store needs: an identified run.

    Concrete stores narrow this to the full context they understand; the engine
    only relies on a store accepting whatever context it is given.
    """

    run_id: str


class SnapshotStore(abc.ABC):
    """Write/restore the volatile run state for crash recovery and history."""

    @abc.abstractmethod
    async def write_snapshot(self, ctx: SnapshotContext) -> None:
        """Persist the current state of ``ctx``."""

    @abc.abstractmethod
    def restore(self, ctx: SnapshotContext) -> bool:
        """Rehydrate ``ctx`` in place from the last snapshot.

        Returns ``True`` if a snapshot was found and applied, ``False`` otherwise.
        """


class NullStore(SnapshotStore):
    """Persists nothing. The default when no store is configured."""

    async def write_snapshot(self, ctx: SnapshotContext) -> None:
        return None

    def restore(self, ctx: SnapshotContext) -> bool:
        return False
