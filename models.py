"""
models.py

Data-access layer. This module knows how to read and write user and
complaint rows in the database, and returns them as plain dictionaries so
the rest of the app doesn't need to deal with sqlite3.Row objects directly.
"""

import database

COMPLAINT_CATEGORIES = [
    "Road",
    "Water",
    "Electricity",
    "Garbage",
    "Street Light",
    "Public Safety",
    "Other",
]

COMPLAINT_STATUSES = [
    "Pending",
    "In Progress",
    "Resolved",
    "Rejected",
]


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def create_user(name, email, phone, password_hash, role, created_at):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, phone, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, password_hash, role, created_at),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return _row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return _row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_user_profile(user_id, name, phone):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name = ?, phone = ? WHERE id = ?",
            (name, phone, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_user_password(user_id, new_password_hash):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password_hash, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Complaint operations
# ---------------------------------------------------------------------------

def create_complaint(user_id, category, description, image_path, status, created_at, updated_at):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO complaints
                (user_id, category, description, image_path, status, admin_remark, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, category, description, image_path, status, None, created_at, updated_at),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_complaint_by_id(complaint_id):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT complaints.*, users.name AS user_name, users.email AS user_email, users.phone AS user_phone
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            WHERE complaints.id = ?
            """,
            (complaint_id,),
        )
        return _row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_complaints_by_user(user_id):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM complaints WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_complaints():
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT complaints.*, users.name AS user_name, users.email AS user_email, users.phone AS user_phone
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            ORDER BY complaints.created_at DESC
            """
        )
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_complaint_status(complaint_id, status, admin_remark, updated_at):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE complaints
            SET status = ?, admin_remark = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, admin_remark, updated_at, complaint_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()