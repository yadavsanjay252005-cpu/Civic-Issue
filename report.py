"""
report.py

Generates a CSV report of all complaints and saves it inside reports/.
"""

import csv
import os

import activity_log
import models
import utils

REPORT_HEADERS = [
    "Complaint ID",
    "User Name",
    "Email",
    "Phone",
    "Category",
    "Description",
    "Image Path",
    "Status",
    "Admin Remark",
    "Created At",
    "Updated At",
]


def generate_report(admin_id=None):
    """
    Generate a CSV report of all complaints and save it to reports/.
    Returns the absolute path of the generated file.
    """
    utils.ensure_directories()

    complaints = models.get_all_complaints()

    filename = "complaint_report_{}.csv".format(
        utils.now_str().replace(":", "-").replace(" ", "_")
    )
    filepath = os.path.join(utils.REPORTS_DIR, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(REPORT_HEADERS)

        for complaint in complaints:
            writer.writerow([
                complaint["id"],
                complaint["user_name"],
                complaint["user_email"],
                complaint.get("user_phone", ""),
                complaint["category"],
                complaint["description"],
                complaint["image_path"] or "",
                complaint["status"],
                complaint["admin_remark"] or "",
                complaint["created_at"],
                complaint["updated_at"],
            ])

    activity_log.log_generate_report(admin_id, filepath)
    return filepath