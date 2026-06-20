"""SQLite-backed storage implementation for pyfarm."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SQLiteBackend:
    """
    Async SQLite backend for pyfarm (using aiosqlite).

    Stores three tables:
    - snapshots: control context snapshots (grow_id, timestamp, data)
    - sensor_readings: time-series readings (timestamp, sensor_id, metric, value, unit)
    - events: audit trail (timestamp, grow_id, event_type, event_kind, message, data)
    """

    def __init__(self, db_path: str | Path = "pyfarm.db"):
        self.db_path = Path(db_path)
        self._db = None

    async def connect(self) -> None:
        """Initialize the database and create tables if needed."""
        try:
            import aiosqlite
        except ImportError:
            raise ImportError(
                "aiosqlite is required for SQLiteBackend. Install with: pip install pyfarm-core[storage]"
            )

        self._db = await aiosqlite.connect(str(self.db_path))
        await self._init_schema()

    async def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        if not self._db:
            return

        # Snapshots table
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grow_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                UNIQUE(grow_id, timestamp)
            )
            """
        )

        # Sensor readings table
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                error TEXT
            )
            """
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON sensor_readings(sensor_id, timestamp)"
        )

        # Events table
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                grow_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_kind TEXT NOT NULL,
                message TEXT,
                data TEXT
            )
            """
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_grow_time ON events(grow_id, timestamp)"
        )

        await self._db.commit()

    async def write_snapshot(self, ctx: Any) -> None:
        """Persist a control context snapshot."""
        if not self._db:
            await self.connect()

        grow_id = getattr(ctx, "grow_id", "default")
        timestamp = datetime.now(timezone.utc).isoformat()

        # Serialize context to JSON (simplified: use to_status_dict if available)
        if hasattr(ctx, "to_status_dict"):
            data = json.dumps(ctx.to_status_dict())
        else:
            data = json.dumps({"context": str(ctx)})

        try:
            await self._db.execute(
                """
                INSERT OR REPLACE INTO snapshots (grow_id, timestamp, data)
                VALUES (?, ?, ?)
                """,
                (grow_id, timestamp, data),
            )
            await self._db.commit()
        except Exception as e:
            logger.error(f"Failed to write snapshot: {e}")

    async def get_latest_snapshot(self, grow_id: str) -> dict | None:
        """Retrieve the most recent snapshot for a grow."""
        if not self._db:
            await self.connect()

        cursor = await self._db.execute(
            """
            SELECT data FROM snapshots
            WHERE grow_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (grow_id,),
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    async def insert_sensor_reading(self, reading: Any) -> None:
        """Record a sensor reading."""
        if not self._db:
            await self.connect()

        timestamp = reading.timestamp.isoformat() if hasattr(reading.timestamp, "isoformat") else str(reading.timestamp)

        try:
            await self._db.execute(
                """
                INSERT INTO sensor_readings (timestamp, sensor_id, metric, value, unit, error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    reading.sensor_id,
                    reading.metric,
                    reading.value,
                    reading.unit,
                    reading.error,
                ),
            )
            await self._db.commit()
        except Exception as e:
            logger.error(f"Failed to insert sensor reading: {e}")

    async def get_readings(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query sensor readings in a time range."""
        if not self._db:
            await self.connect()

        start_iso = start_time.isoformat() if hasattr(start_time, "isoformat") else str(start_time)
        end_iso = end_time.isoformat() if hasattr(end_time, "isoformat") else str(end_time)

        query = """
            SELECT timestamp, sensor_id, metric, value, unit, error
            FROM sensor_readings
            WHERE sensor_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """
        params = [sensor_id, start_iso, end_iso]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()

        return [
            {
                "timestamp": row[0],
                "sensor_id": row[1],
                "metric": row[2],
                "value": row[3],
                "unit": row[4],
                "error": row[5],
            }
            for row in rows
        ]

    async def insert_event(
        self,
        event_type: str,
        event_kind: str,
        message: str,
        timestamp: datetime,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log a control/analytics/commerce event."""
        if not self._db:
            await self.connect()

        grow_id = "default"  # TODO: infer from context if available
        timestamp_iso = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        data_json = json.dumps(data or {})

        try:
            await self._db.execute(
                """
                INSERT INTO events (timestamp, grow_id, event_type, event_kind, message, data)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp_iso, grow_id, event_type, event_kind, message, data_json),
            )
            await self._db.commit()
        except Exception as e:
            logger.error(f"Failed to insert event: {e}")

    async def get_events(
        self,
        grow_id: str,
        start_time: datetime,
        end_time: datetime,
        event_kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query events for a grow in a time range."""
        if not self._db:
            await self.connect()

        start_iso = start_time.isoformat() if hasattr(start_time, "isoformat") else str(start_time)
        end_iso = end_time.isoformat() if hasattr(end_time, "isoformat") else str(end_time)

        query = """
            SELECT timestamp, grow_id, event_type, event_kind, message, data
            FROM events
            WHERE grow_id = ? AND timestamp BETWEEN ? AND ?
        """
        params = [grow_id, start_iso, end_iso]

        if event_kind:
            query += " AND event_kind = ?"
            params.append(event_kind)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()

        return [
            {
                "timestamp": row[0],
                "grow_id": row[1],
                "event_type": row[2],
                "event_kind": row[3],
                "message": row[4],
                "data": json.loads(row[5]) if row[5] else {},
            }
            for row in rows
        ]

    async def close(self) -> None:
        """Release database connection."""
        if self._db:
            await self._db.close()
            self._db = None
