"""
database.py

Everything related to the SQLite connection and schema. 
Features an auto-healing mechanism: if the database file is deleted, 
it will automatically rebuild the tables on the next connection.
"""

import os
import sqlite3

import utils

DB_NAME = os.path.join(utils.BASE_DIR, "complaint_system.db")

DEFAULT_ADMIN_EMAIL = "admin@gmail.com"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "System Administrator"


def _create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            image_path TEXT,
            resolution_image_path TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_remark TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            complaint_id INTEGER,
            activity TEXT NOT NULL,
            response TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        )
        """
    )

    conn.commit()


def _create_default_admin(conn: sqlite3.Connection):
    """Create the default admin account if it does not already exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_ADMIN_EMAIL,))
    existing = cursor.fetchone()
    if existing:
        return

    password_hash = utils.hash_password(DEFAULT_ADMIN_PASSWORD)
    cursor.execute(
        """
        INSERT INTO users (name, email, phone, password_hash, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            DEFAULT_ADMIN_NAME,
            DEFAULT_ADMIN_EMAIL,
            "",
            password_hash,
            "admin",
            utils.now_str(),
        ),
    )
    conn.commit()


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _migrate_schema(conn: sqlite3.Connection):
    """
    Add any columns that were introduced after a database file was first
    created. SQLite's ALTER TABLE ... ADD COLUMN is safe to run on existing
    data and does not touch existing rows other than backfilling the new
    column with its default value.
    """
    cursor = conn.cursor()

    if not _column_exists(conn, "complaints", "location"):
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN location TEXT NOT NULL DEFAULT ''"
        )

    if not _column_exists(conn, "complaints", "resolution_image_path"):
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN resolution_image_path TEXT"
        )

    conn.commit()


def get_connection() -> sqlite3.Connection:
    """
    Return a new SQLite connection with foreign keys enabled.
    Auto-heals the database if the .db file was deleted by the user.
    """
    utils.ensure_directories()
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    
    # Auto-Heal Check: Verify if the core table 'users' exists.
    # If not, it means the database is empty or was just recreated.
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        _create_tables(conn)
        _create_default_admin(conn)
    else:
        # Existing database from before these columns existed: bring it
        # up to date in place instead of touching any other data.
        _migrate_schema(conn)

    return conn


def init_db():
    """
    Initialize the database directories and trigger the auto-heal check.
    """
    conn = get_connection()
    conn.close()
