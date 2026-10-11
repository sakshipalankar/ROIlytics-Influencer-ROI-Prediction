"""Connected Instagram accounts store — encrypted token management via SQLite."""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from ..settings import get_settings

logger = logging.getLogger(__name__)

_conn: sqlite3.Connection | None = None


def _get_fernet() -> Fernet:
    key = get_settings().TOKEN_ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set.  Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def get_conn() -> sqlite3.Connection:
    """Return a module-level SQLite connection (created once)."""
    global _conn
    if _conn is None:
        db_path = get_settings().LIVE_CACHE_DB
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


# ── Schema ────────────────────────────────────────────────────────────────────

def init_tables() -> None:
    """Create connected_accounts table if it doesn't exist."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS connected_accounts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            label           TEXT    NOT NULL UNIQUE,
            username        TEXT,
            encrypted_token TEXT    NOT NULL,
            token_updated_at TEXT  NOT NULL,
            token_expires_at TEXT,
            last_error       TEXT
        )
    """)
    conn.commit()
    logger.info("✅ connected_accounts table ready")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


def add_account(label: str, token: str, username: str | None = None) -> dict[str, Any]:
    """Insert or update a connected account.  Returns the row (without token)."""
    conn = get_conn()
    enc = encrypt_token(token)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO connected_accounts (label, username, encrypted_token, token_updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(label) DO UPDATE SET
            username = COALESCE(excluded.username, connected_accounts.username),
            encrypted_token = excluded.encrypted_token,
            token_updated_at = excluded.token_updated_at,
            last_error = NULL
        """,
        (label, username, enc, now),
    )
    conn.commit()
    return get_account_by_label(label)  # type: ignore[return-value]


def get_account(account_id: int) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, label, username, token_updated_at, token_expires_at, last_error "
        "FROM connected_accounts WHERE id = ?",
        (account_id,),
    ).fetchone()
    return dict(row) if row else None


def get_account_by_label(label: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, label, username, token_updated_at, token_expires_at, last_error "
        "FROM connected_accounts WHERE label = ?",
        (label,),
    ).fetchone()
    return dict(row) if row else None


def get_account_token(account_id: int) -> str:
    """Decrypt and return the token — NEVER expose outside the service layer."""
    conn = get_conn()
    row = conn.execute(
        "SELECT encrypted_token FROM connected_accounts WHERE id = ?",
        (account_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Account {account_id} not found")
    return decrypt_token(row["encrypted_token"])


def list_accounts() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, label, username, token_updated_at, token_expires_at, last_error "
        "FROM connected_accounts ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_account(account_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM connected_accounts WHERE id = ?", (account_id,))
    conn.commit()
    return cur.rowcount > 0


def update_account_username(account_id: int, username: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE connected_accounts SET username = ? WHERE id = ?",
        (username, account_id),
    )
    conn.commit()


def update_account_error(account_id: int, error: str | None) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE connected_accounts SET last_error = ? WHERE id = ?",
        (error, account_id),
    )
    conn.commit()


def update_account_token(account_id: int, new_token: str) -> None:
    """Re-encrypt and store a refreshed token."""
    conn = get_conn()
    enc = encrypt_token(new_token)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE connected_accounts SET encrypted_token = ?, token_updated_at = ?, last_error = NULL WHERE id = ?",
        (enc, now, account_id),
    )
    conn.commit()


def get_all_account_ids_with_tokens() -> list[tuple[int, str]]:
    """Return (id, decrypted_token) for every account. Used by background refresh."""
    conn = get_conn()
    rows = conn.execute("SELECT id, encrypted_token FROM connected_accounts").fetchall()
    result = []
    for r in rows:
        try:
            token = decrypt_token(r["encrypted_token"])
            result.append((r["id"], token))
        except InvalidToken:
            logger.warning("Could not decrypt token for account %s", r["id"])
    return result


# ── Seed from environment ─────────────────────────────────────────────────────

def seed_from_env() -> int:
    """Read IG_TOKEN_<LABEL> env vars and upsert into connected_accounts.
    Returns the number of accounts seeded.
    """
    count = 0
    for key, value in os.environ.items():
        if key.startswith("IG_TOKEN_") and value:
            label = key[len("IG_TOKEN_"):]
            if not label:
                continue
            try:
                add_account(label=label, token=value)
                count += 1
                logger.info("Seeded account from env: %s", label)
            except Exception as exc:
                logger.warning("Failed to seed account %s: %s", label, exc)
    return count
