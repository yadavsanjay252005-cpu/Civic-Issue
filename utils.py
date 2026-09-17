"""
utils.py

Common helper functions used across the Complaint Management System:
- Password hashing / verification
- Date & time helpers
- Validation helpers (email, phone, required fields)
- File / image helpers (copying uploaded images into uploads/)
"""

import hashlib
import os
import re
import shutil
import uuid
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def ensure_directories():
    """Make sure uploads/ and reports/ directories exist."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_HASH_ALGO = "sha256"
_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash string for the given plain-text password."""
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        _ITERATIONS, salt.hex(), derived.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plain-text password against a stored PBKDF2 hash string."""
    try:
        algo_tag, iterations_str, salt_hex, hash_hex = stored_hash.split("$")
        if algo_tag != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    derived = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode("utf-8"), salt, iterations)
    return derived == expected


# ---------------------------------------------------------------------------
# Date / time helpers
# ---------------------------------------------------------------------------

def now_str() -> str:
    """Return the current timestamp as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9\- ]{7,15}$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(_EMAIL_RE.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    """Phone is optional in some flows, but if provided it must look valid."""
    if not phone:
        return True
    return bool(_PHONE_RE.match(phone.strip()))


def is_non_empty(value: str) -> bool:
    return value is not None and value.strip() != ""


def passwords_match(password: str, confirm: str) -> bool:
    return password == confirm


# ---------------------------------------------------------------------------
# File / image helpers
# ---------------------------------------------------------------------------

def copy_image_to_uploads(source_path: str) -> str:
    """
    Copy an image selected by the user into the uploads/ directory using a
    unique filename, and return the path (relative to the project root)
    that should be stored in the database.
    """
    ensure_directories()

    if not source_path or not os.path.isfile(source_path):
        raise FileNotFoundError("Selected image file does not exist.")

    _, ext = os.path.splitext(source_path)
    
    # Optional basic verification of extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    if ext.lower() not in valid_extensions:
        raise ValueError(f"Invalid file extension: {ext}. Only JPG, PNG, GIF, and BMP are allowed.")

    unique_name = "{}{}".format(uuid.uuid4().hex, ext.lower())
    destination_path = os.path.join(UPLOADS_DIR, unique_name)

    try:
        shutil.copyfile(source_path, destination_path)
    except Exception as e:
        raise IOError(f"Could not copy image: {e}")

    # Store a path relative to the project root so the DB stays portable.
    return os.path.join("uploads", unique_name)


def resolve_upload_path(relative_path: str) -> str:
    """Turn a path stored in the DB back into an absolute filesystem path."""
    if not relative_path:
        return ""
    # Make sure to handle cross-platform path separators properly
    clean_relative = relative_path.replace("\\", os.sep).replace("/", os.sep)
    return os.path.join(BASE_DIR, clean_relative)