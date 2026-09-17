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
            image_path TEXT,
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
        
    return conn


def init_db():
    """
    Initialize the database directories and trigger the auto-heal check.
    """
    conn = get_connection()
    conn.close()