"""
activity_log.py

Implements the Activity / Response / Source event log described in the
project spec. Every significant action in the system (registration, login,
submitting a complaint, updating status, etc.) is recorded here so there is
an audit trail of what happened, who did it, and what the system responded
with.
"""

import database
import utils


def log_activity(user_id, complaint_id, activity, response, source):
    """
    Insert a row into activity_log.

    user_id       - id of the user who triggered the event (may be None for
                     system-only events, e.g. before a user is known)
    complaint_id  - id of the related complaint, if any (may be None)
    activity      - short description of what happened
                     (e.g. "Submit Complaint")
    response      - what the system responded with
                     (e.g. "Complaint submitted successfully")
    source        - "User", "Admin", "System", or a combination like
                     "User/System"
    """
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity_log (user_id, complaint_id, activity, response, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, complaint_id, activity, response, source, utils.now_str()),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_logs_for_user(user_id):
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM activity_log WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_logs():
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_log ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Convenience wrappers for the specific events named in the spec.
# Using these keeps the wording of "activity" / "response" consistent
# wherever they're logged from across the app.
# ---------------------------------------------------------------------------

def log_registration(user_id, name):
    log_activity(
        user_id, None,
        "User Registration",
        "Account created successfully for {}".format(name),
        "User",
    )


def log_login(user_id, success, email):
    response = "User dashboard displayed" if success else "Login failed for {}".format(email)
    log_activity(user_id, None, "User Login", response, "User/System")


def log_logout(user_id):
    log_activity(user_id, None, "Logout", "User logged out", "User")


def log_submit_complaint(user_id, complaint_id):
    log_activity(
        user_id, complaint_id,
        "Submit Complaint",
        "Complaint submitted successfully",
        "User",
    )


def log_upload_image(user_id, complaint_id):
    log_activity(
        user_id, complaint_id,
        "Upload Image",
        "Image attached to complaint",
        "User/System",
    )


def log_view_status(user_id, complaint_id, status):
    log_activity(
        user_id, complaint_id,
        "View Complaint Status",
        "Status displayed: {}".format(status),
        "System",
    )


def log_edit_profile(user_id):
    log_activity(
        user_id, None,
        "Edit Profile",
        "Personal information updated",
        "User/System",
    )


def log_view_all_complaints(admin_id, count):
    log_activity(
        admin_id, None,
        "View All Complaints",
        "List of {} complaint(s) displayed".format(count),
        "Admin/System",
    )


def log_update_status(admin_id, complaint_id, new_status):
    log_activity(
        admin_id, complaint_id,
        "Update Complaint Status",
        "Complaint status updated to {}".format(new_status),
        "Admin/System",
    )


def log_manage_complaint(admin_id, complaint_id):
    log_activity(
        admin_id, complaint_id,
        "Manage Complaint",
        "Complaint managed according to its details",
        "Admin/System",
    )


def log_generate_report(admin_id, report_path):
    log_activity(
        admin_id, None,
        "Generate Report",
        "Complaint report generated: {}".format(report_path),
        "Admin/System",
    )
