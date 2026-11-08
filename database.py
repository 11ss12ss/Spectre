"""Tiny async SQLite wrapper + schema."""
import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER NOT NULL,
    key      TEXT    NOT NULL,
    value    TEXT    NOT NULL,
    PRIMARY KEY (guild_id, key)
);

CREATE TABLE IF NOT EXISTS cases (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id     INTEGER NOT NULL,
    case_number  INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action       TEXT    NOT NULL,
    reason       TEXT,
    duration     INTEGER,
    created_at   INTEGER NOT NULL,
    expires_at   INTEGER,
    active       INTEGER NOT NULL DEFAULT 1,
    dm_sent      INTEGER NOT NULL DEFAULT 0,
    UNIQUE (guild_id, case_number)
);
CREATE INDEX IF NOT EXISTS idx_cases_user   ON cases (guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_cases_expiry ON cases (action, active, expires_at);

CREATE TABLE IF NOT EXISTS tickets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id     INTEGER NOT NULL,
    channel_id   INTEGER NOT NULL UNIQUE,
    user_id      INTEGER NOT NULL,
    category     TEXT,
    status       TEXT    NOT NULL DEFAULT 'open',
    claimed_by   INTEGER,
    created_at   INTEGER NOT NULL,
    closed_at    INTEGER,
    close_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets (guild_id, user_id, status);

CREATE TABLE IF NOT EXISTS premium (
    guild_id   INTEGER PRIMARY KEY,
    tier       TEXT NOT NULL,
    expires_at INTEGER,
    source     TEXT
);

CREATE TABLE IF NOT EXISTS premium_codes (
    code        TEXT PRIMARY KEY,
    tier        TEXT    NOT NULL,
    days        INTEGER,
    created_at  INTEGER NOT NULL,
    redeemed_by INTEGER,
    redeemed_at INTEGER
);

CREATE TABLE IF NOT EXISTS pending_verification (
    guild_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _run(self, sql: str, params=()) -> tuple[int, int]:
        cur = await self._conn.execute(sql, params)
        await self._conn.commit()
        result = (cur.lastrowid, cur.rowcount)
        await cur.close()
        return result

    async def execute(self, sql: str, params=()) -> int:
        """Run a write statement, return lastrowid."""
        return (await self._run(sql, params))[0]

    async def execute_rowcount(self, sql: str, params=()) -> int:
        """Run a write statement, return the number of affected rows."""
        return (await self._run(sql, params))[1]

    async def fetchone(self, sql: str, params=()):
        async with self._conn.execute(sql, params) as cur:
            return await cur.fetchone()

    async def fetchall(self, sql: str, params=()):
        async with self._conn.execute(sql, params) as cur:
            return await cur.fetchall()
