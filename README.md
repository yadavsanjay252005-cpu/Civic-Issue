# CivicCare - Complaint Management System

A college-presentation-friendly web version of the original Tkinter Complaint Management System.

## What changed

- Replaced the Tkinter desktop UI with Streamlit.
- Kept the existing authentication, complaint, SQLite, activity-log and CSV-report business logic.
- Redesigned the interface with responsive cards, dashboard metrics, filters and clearer navigation.
- Added visible success/error/info feedback for login, registration, complaint submission, image upload, profile updates, status updates, report generation and logout.
- Removed separate Tkinter/Toplevel image/detail windows. Complaint details and images are rendered on the same browser page.
- Added inline image viewing with Streamlit's built-in image expand control.
- Added deployment files for Streamlit hosting and Render.
- Added a requirements.txt and .streamlit/config.toml.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL printed by Streamlit.

## Demo admin

- Email: `admin@gmail.com`
- Password: `admin123`

## Project files

- `app.py` - Streamlit UI
- `auth.py` - login/registration
- `complaint.py` - complaint operations and validation
- `models.py` - database access
- `database.py` - SQLite schema and connection
- `activity_log.py` - audit/event logging
- `report.py` - CSV report generation
- `utils.py` - validation, hashing and file helpers
- `complaint_system.db` - SQLite database for local demonstration
- `uploads/` - complaint images
- `reports/` - generated reports

## Hosting note

This project uses SQLite and local file storage because that matches the original project. That is convenient for a college demo, but typical cloud deployments use ephemeral/container storage. For a production deployment, move the database to a managed database such as PostgreSQL and uploaded images to object storage.

For a quick college presentation, the included SQLite setup is enough to run the application locally or on a simple VM/container.
