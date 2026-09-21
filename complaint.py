"""
complaint.py

Business logic for complaints: creation, retrieval, status updates, and
image upload handling. This module sits on top of models.py (raw data
access) and adds validation plus activity logging.
"""

import activity_log
import database
import models
import utils


class ComplaintError(Exception):
    """Raised when a complaint operation fails validation."""
    pass


def submit_complaint(user_id, category, description, location, image_source_path=None):
    """
    Create a new complaint for the given user.

    location is the mandatory, free-text address/location of the issue
    (e.g. "Near ABC School, Main Road, Thane") -- no GPS/map data involved.

    image_source_path, if provided, is the path to a file the user picked
    via the file dialog; it gets copied into uploads/ with a unique name.
    """
    category = (category or "").strip()
    description = (description or "").strip()
    location = (location or "").strip()

    if category not in models.COMPLAINT_CATEGORIES:
        raise ComplaintError("Please select a valid complaint category.")

    if not utils.is_non_empty(description):
        raise ComplaintError("Please enter a complaint description.")

    if not utils.is_non_empty(location):
        raise ComplaintError("Location / Address is required.")

    image_path = None
    if image_source_path:
        try:
            image_path = utils.copy_image_to_uploads(image_source_path)
        except (FileNotFoundError, ValueError, IOError) as exc:
            raise ComplaintError(str(exc))

    timestamp = utils.now_str()
    complaint_id = models.create_complaint(
        user_id=user_id,
        category=category,
        description=description,
        location=location,
        image_path=image_path,
        status="Pending",
        created_at=timestamp,
        updated_at=timestamp,
    )

    activity_log.log_submit_complaint(user_id, complaint_id)
    if image_path:
        activity_log.log_upload_image(user_id, complaint_id)

    return complaint_id


def attach_image(user_id, complaint_id, image_source_path):
    """Attach/replace an image on an existing complaint."""
    complaint = models.get_complaint_by_id(complaint_id)
    if complaint is None:
        raise ComplaintError("Complaint not found.")
        
    # SECURITY FIX: Ensure the complaint actually belongs to the logged in user
    if complaint["user_id"] != user_id:
        raise ComplaintError("You do not have permission to modify this complaint.")

    try:
        image_path = utils.copy_image_to_uploads(image_source_path)
    except (FileNotFoundError, ValueError, IOError) as exc:
        raise ComplaintError(str(exc))

    # image_path isn't part of models.update_complaint_status, so do a
    # light-weight direct update here.
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE complaints SET image_path = ? WHERE id = ?",
            (image_path, complaint_id),
        )
        conn.commit()
    finally:
        conn.close()

    activity_log.log_upload_image(user_id, complaint_id)
    return image_path


def get_user_complaints(user_id):
    return models.get_complaints_by_user(user_id)


def get_complaint_status(user_id, complaint_id):
    complaint = models.get_complaint_by_id(complaint_id)
    if complaint is None:
        raise ComplaintError("Complaint not found.")
        
    if complaint["user_id"] != user_id:
        raise ComplaintError("You do not have permission to view this complaint.")
        
    activity_log.log_view_status(user_id, complaint_id, complaint["status"])
    return complaint["status"]


def get_all_complaints(admin_id=None, log=True):
    complaints = models.get_all_complaints()
    if log:
        activity_log.log_view_all_complaints(admin_id, len(complaints))
    return complaints


def get_complaint_details(complaint_id):
    complaint = models.get_complaint_by_id(complaint_id)
    if complaint is None:
        raise ComplaintError("Complaint not found.")
    return complaint


def manage_complaint(admin_id, complaint_id, new_status, admin_remark, resolution_image_source_path=None):
    """
    Admin action: update status and/or remark for a complaint, and log both
    "Update Complaint Status" and "Manage Complaint" events as described in
    the spec.

    resolution_image_source_path, if provided, is the path to a file the
    admin picked (e.g. a photo of the repaired/resolved issue). It is
    stored under uploads/resolutions/ and recorded in the complaint's
    resolution_image_path column, kept separate from the citizen's
    original image_path.
    """
    if new_status not in models.COMPLAINT_STATUSES:
        raise ComplaintError("Please select a valid status.")

    complaint = models.get_complaint_by_id(complaint_id)
    if complaint is None:
        raise ComplaintError("Complaint not found.")

    resolution_image_path = None
    if resolution_image_source_path:
        try:
            resolution_image_path = utils.copy_image_to_uploads(
                resolution_image_source_path, subfolder="resolutions"
            )
        except (FileNotFoundError, ValueError, IOError) as exc:
            raise ComplaintError(str(exc))

    updated = models.update_complaint_status(
        complaint_id,
        status=new_status,
        admin_remark=admin_remark,
        updated_at=utils.now_str(),
        resolution_image_path=resolution_image_path,
    )
    if not updated:
        raise ComplaintError("Could not update the complaint.")

    activity_log.log_update_status(admin_id, complaint_id, new_status)
    activity_log.log_manage_complaint(admin_id, complaint_id)
    if resolution_image_path:
        activity_log.log_upload_resolution_photo(admin_id, complaint_id)
    return True
