"""
auth.py

User registration, login, and admin authentication. All password handling
goes through utils.hash_password / utils.verify_password so plain-text
passwords are never stored. Every registration/login attempt is recorded
in the activity log.
"""

import activity_log
import models
import utils


class AuthError(Exception):
    """Raised when registration or login fails validation/credential checks."""
    pass


def register_user(name, email, phone, password, confirm_password, role="user"):
    """
    Validate and create a new user account.
    Returns the newly created user's id on success.
    Raises AuthError with a human-readable message on failure.
    """
    name = (name or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip()

    if not utils.is_non_empty(name):
        raise AuthError("Name is required.")

    if not utils.is_valid_email(email):
        raise AuthError("Please enter a valid email address.")

    if not utils.is_valid_phone(phone):
        raise AuthError("Please enter a valid 10-digit Indian mobile number.")

    if not utils.is_non_empty(password):
        raise AuthError("Password is required.")

    if len(password) < 4:
        raise AuthError("Password must be at least 4 characters long.")

    if not utils.passwords_match(password, confirm_password):
        raise AuthError("Password and Confirm Password do not match.")

    if models.get_user_by_email(email) is not None:
        raise AuthError("An account with this email already exists.")

    password_hash = utils.hash_password(password)
    user_id = models.create_user(
        name=name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role=role,
        created_at=utils.now_str(),
    )

    activity_log.log_registration(user_id, name)
    return user_id


def login_user(email, password):
    """
    Verify credentials. Returns the user dict on success.
    Raises AuthError on failure. Logs both successful and failed attempts.
    """
    email = (email or "").strip().lower()

    if not utils.is_non_empty(email) or not utils.is_non_empty(password):
        raise AuthError("Please enter both email and password.")

    user = models.get_user_by_email(email)
    if user is None or not utils.verify_password(password, user["password_hash"]):
        # We don't know the user's id if the email doesn't exist, so log with
        # user_id=None in that case.
        activity_log.log_login(user["id"] if user else None, False, email)
        raise AuthError("Invalid email or password.")

    activity_log.log_login(user["id"], True, email)
    return user


def logout_user(user_id):
    activity_log.log_logout(user_id)


def is_admin(user) -> bool:
    return bool(user) and user.get("role") == "admin"
