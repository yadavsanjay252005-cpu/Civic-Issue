"""
Streamlit front-end for the Complaint Management System.

This is the browser-hosted replacement for the old Tkinter UI.
The existing business/data layer is reused:
auth.py, complaint.py, models.py, database.py, utils.py,
activity_log.py and report.py.

Run locally:
    streamlit run app.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

import activity_log
import auth
import complaint
import database
import models
import report
import utils

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CivicCare | Complaint Management",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()
utils.ensure_directories()

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
PRIMARY = "#2563EB"
PRIMARY_DARK = "#1D4ED8"
DARK = "#0F172A"
SLATE = "#334155"
BG = "#F1F5F9"
CARD = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
PURPLE = "#7C3AED"

STATUS_COLORS = {
    "Pending": WARNING,
    "In Progress": PRIMARY,
    "Resolved": SUCCESS,
    "Rejected": DANGER,
}

CUSTOM_CSS = f"""
<style>
    #MainMenu, footer {{ visibility: hidden; }}

    .stApp {{
        background: linear-gradient(180deg, #F8FAFC 0%, {BG} 100%);
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {DARK} 0%, #1E293B 100%);
        border-right: 0;
    }}

    section[data-testid="stSidebar"] * {{
        color: #E2E8F0 !important;
    }}

    .hero {{
        background:
            radial-gradient(circle at top right, rgba(96,165,250,.28), transparent 36%),
            linear-gradient(135deg, {DARK} 0%, #1E3A8A 100%);
        border-radius: 24px;
        padding: 32px 36px;
        color: white;
        box-shadow: 0 14px 35px rgba(15,23,42,.15);
        margin-bottom: 24px;
    }}

    .hero h1 {{
        margin: 0;
        font-size: 2.15rem;
        letter-spacing: -0.02em;
    }}

    .hero p {{
        margin: 8px 0 0 0;
        color: #CBD5E1;
        font-size: 1rem;
    }}

    .metric {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 6px 20px rgba(15,23,42,.04);
        min-height: 108px;
    }}

    .metric .label {{
        color: {MUTED};
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .06em;
        text-transform: uppercase;
    }}

    .metric .value {{
        color: {DARK};
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-top: 8px;
    }}

    .badge {{
        display: inline-block;
        color: white;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: .76rem;
        font-weight: 800;
    }}

    .mini-card {{
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 14px 16px;
        background: #FFFFFF;
        margin-bottom: 10px;
    }}

    .muted {{
        color: {MUTED};
        font-size: .9rem;
    }}

    .auth-shell {{
        max-width: 760px;
        margin: 4rem auto;
    }}

    .auth-note {{
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1E40AF;
        padding: 12px 14px;
        border-radius: 12px;
        font-size: .9rem;
        margin-top: 12px;
    }}

    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        min-height: 42px;
    }}

    div[data-testid="stMetric"] {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 8px;
    }}

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def flash(kind: str, message: str) -> None:
    st.session_state.setdefault("_flash", []).append((kind, message))


def render_flashes() -> None:
    messages = st.session_state.pop("_flash", [])
    for kind, message in messages:
        if kind == "success":
            st.success(message)
        elif kind == "error":
            st.error(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.info(message)


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, MUTED)
    return f'<span class="badge" style="background:{color}">{status}</span>'


def metric_card(label: str, value: int, color: str) -> None:
    st.markdown(
        f"""
        <div class="metric" style="border-top:4px solid {color};">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_download(path: str, filename: str, mime: str = "text/csv") -> None:
    if os.path.exists(path):
        with open(path, "rb") as handle:
            st.download_button(
                "Download",
                data=handle.read(),
                file_name=filename,
                mime=mime,
                use_container_width=True,
            )


def save_uploaded_to_temp(uploaded_file) -> str:
    """Save a Streamlit UploadedFile to a temp file for the existing path-based API."""
    suffix = Path(uploaded_file.name).suffix.lower() or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(uploaded_file.getvalue())
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()


def with_temp_upload(uploaded_file, callback):
    temp_path = save_uploaded_to_temp(uploaded_file)
    try:
        return callback(temp_path)
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def open_image_inline(image_path: str, caption: str = "Complaint image") -> None:
    """
    Show the image inline in the current page.

    This deliberately avoids Tkinter Toplevel windows and browser popups.
    Streamlit's image viewer can still be expanded from the image itself.
    """
    abs_path = utils.resolve_upload_path(image_path)
    if not image_path:
        st.caption("No image attached.")
        return

    if not os.path.exists(abs_path):
        st.warning("The image file is not available on this deployment.")
        return

    st.image(abs_path, caption=caption, use_container_width=True)
    st.caption("Use the image expand icon for a larger view — it stays inside this page.")


# ---------------------------------------------------------------------------
# Session state / authentication
# ---------------------------------------------------------------------------
st.session_state.setdefault("user", None)
st.session_state.setdefault("page", "Dashboard")
st.session_state.setdefault("selected_complaint", None)
st.session_state.setdefault("view_image_path", None)
st.session_state.setdefault("auth_mode", "Login")


def do_logout() -> None:
    """
    Log the current user out and return to the sign-in screen.

    Note: this intentionally does NOT assign directly to
    st.session_state["user_navigation"] / ["admin_navigation"]. Those keys
    belong to the sidebar st.radio widgets, which have already been
    instantiated earlier in this same script run (the Logout button sits
    below the radio in the sidebar). Streamlit forbids setting a widget's
    bound session_state value after that widget has been created in the
    same run and raises a StreamlitAPIException if you try — which is why
    logout previously failed silently. Clearing the keys instead of
    reassigning them is safe, and since the user is about to see the
    sign-in screen (no sidebar radios at all), the keys are simply
    re-initialized to their defaults the next time a dashboard renders.
    """
    user = st.session_state.get("user")
    if user is not None:
        auth.logout_user(user["id"])

    st.session_state.user = None
    st.session_state.page = "Dashboard"
    st.session_state.selected_complaint = None
    st.session_state.view_image_path = None
    st.session_state.pop("user_navigation", None)
    st.session_state.pop("admin_navigation", None)

    flash("info", "You have been logged out.")
    st.rerun()


def render_auth() -> None:
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    hero(
        "CivicCare",
        "A clean, browser-based complaint management portal for citizens and administrators.",
    )
    render_flashes()

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        st.subheader("Welcome back")
        st.caption("Sign in to submit complaints, track updates, and manage your profile.")

        with st.form("login_form"):
            email = st.text_input(
                "Email Address",
                placeholder="you@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                logged_user = auth.login_user(email, password)
            except auth.AuthError as exc:
                st.error(f"Login failed: {exc}")
            except Exception as exc:
                st.error(f"System error while logging in: {exc}")
            else:
                st.session_state.user = logged_user
                st.session_state.page = "Dashboard"
                flash("success", f"Login successful. Welcome back, {logged_user['name']}!")
                st.rerun()

        st.markdown(
            '<div class="auth-note"><b>Demo admin:</b> admin@gmail.com &nbsp; / &nbsp; admin123</div>',
            unsafe_allow_html=True,
        )

    with tab_register:
        st.subheader("Create your account")
        st.caption("Register as a citizen to submit and track complaints.")

        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address", key="register_email")
            phone = st.text_input("Phone Number", placeholder="+91 98765 43210")
            p1, p2 = st.columns(2)
            with p1:
                password = st.text_input("Password", type="password", key="register_password")
            with p2:
                confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="register_confirm",
                )
            submitted = st.form_submit_button(
                "Create Account",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                auth.register_user(
                    name=name,
                    email=email,
                    phone=phone,
                    password=password,
                    confirm_password=confirm,
                    role="user",
                )
            except auth.AuthError as exc:
                st.error(f"Registration failed: {exc}")
            except Exception as exc:
                st.error(f"System error while registering: {exc}")
            else:
                flash(
                    "success",
                    "Registration successful. Your account has been created; please sign in.",
                )
                st.rerun()



# ---------------------------------------------------------------------------
# User interface
# ---------------------------------------------------------------------------
USER_PAGES = [
    "Dashboard",
    "Submit Complaint",
    "My Complaints",
    "Check Status",
    "Upload / Replace Image",
    "Edit Profile",
    "Activity Log",
]


def _go_user_page(page: str) -> None:
    """Update the navigation widget and current page before rerunning."""
    st.session_state.user_navigation = page
    st.session_state.page = page


def render_user_sidebar(user) -> None:
    with st.sidebar:
        st.markdown("## CivicCare")
        st.caption("Citizen Portal")
        st.markdown("---")
        st.markdown(f"### {user['name']}")
        st.caption(user["email"])
        st.markdown("---")

        if "user_navigation" not in st.session_state:
            st.session_state.user_navigation = st.session_state.get("page", "Dashboard")

        page = st.radio(
            "Navigation",
            USER_PAGES,
            key="user_navigation",
            label_visibility="collapsed",
        )
        st.session_state.page = page

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            do_logout()


def user_stats(complaints):
    total = len(complaints)
    pending = sum(c["status"] == "Pending" for c in complaints)
    progress = sum(c["status"] == "In Progress" for c in complaints)
    resolved = sum(c["status"] == "Resolved" for c in complaints)
    rejected = sum(c["status"] == "Rejected" for c in complaints)
    return total, pending, progress, resolved, rejected


def render_user_dashboard(user) -> None:
    render_user_sidebar(user)
    complaints = complaint.get_user_complaints(user["id"])
    total, pending, progress, resolved, rejected = user_stats(complaints)

    hero(
        "Citizen Dashboard",
        f"Welcome back, {user['name']}. Raise an issue and track what happens next.",
    )
    render_flashes()

    if st.session_state.page == "Dashboard":
        st.subheader("Your complaint overview")
        cards = st.columns(5)
        values = [
            ("Total", total, DARK),
            ("Pending", pending, WARNING),
            ("In Progress", progress, PRIMARY),
            ("Resolved", resolved, SUCCESS),
            ("Rejected", rejected, DANGER),
        ]
        for col, (label, value, color) in zip(cards, values):
            with col:
                metric_card(label, value, color)

        st.write("")
        left, right = st.columns([1.25, 1])

        with left:
            st.subheader("Recent complaints")
            recent = complaints[:5]
            if not recent:
                st.info("No complaints yet. Use **Submit Complaint** to get started.")
            else:
                for c in recent:
                    st.markdown(
                        f"""
                        <div class="mini-card">
                            <b>#{c['id']} · {c['category']}</b><br>
                            <span>{status_badge(c['status'])}</span>
                            <span class="muted"> &nbsp; {c['created_at']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with right:
            st.subheader("Quick actions")
            st.button(
                "Submit a Complaint",
                type="primary",
                use_container_width=True,
                on_click=_go_user_page,
                args=("Submit Complaint",),
            )
            st.button(
                "View My Complaints",
                use_container_width=True,
                on_click=_go_user_page,
                args=("My Complaints",),
            )
            st.button(
                "Check a Status",
                use_container_width=True,
                on_click=_go_user_page,
                args=("Check Status",),
            )

    elif st.session_state.page == "Submit Complaint":
        render_submit_complaint(user)

    elif st.session_state.page == "My Complaints":
        render_my_complaints(complaints)

    elif st.session_state.page == "Check Status":
        render_check_status(user, complaints)

    elif st.session_state.page == "Upload / Replace Image":
        render_upload_image(user, complaints)

    elif st.session_state.page == "Edit Profile":
        render_edit_profile(user)

    elif st.session_state.page == "Activity Log":
        render_activity_log(user)


def render_submit_complaint(user) -> None:
    st.subheader("Submit a New Complaint")
    st.caption("Provide enough detail for the issue to be understood and acted upon.")

    with st.form("submit_complaint_form", clear_on_submit=True):
        category = st.selectbox("Complaint Category", models.COMPLAINT_CATEGORIES)
        description = st.text_area(
            "Description",
            height=170,
            placeholder="Example: The street light near the college gate has been off for three days...",
        )
        location = st.text_input(
            "Location / Address *",
            placeholder="Example: Near ABC School, Main Road, Thane",
            help="Type the address or a nearby landmark. No GPS or map picker needed.",
        )
        image_file = st.file_uploader(
            "Attach Image (Optional)",
            type=["png", "jpg", "jpeg", "gif", "bmp"],
            help="Accepted: PNG, JPG, JPEG, GIF, BMP",
        )
        submitted = st.form_submit_button(
            "Submit Complaint",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not utils.is_non_empty(location):
            st.error("Location / Address is required.")
            return

        try:
            if image_file is None:
                complaint_id = complaint.submit_complaint(
                    user_id=user["id"],
                    category=category,
                    description=description,
                    location=location,
                    image_source_path=None,
                )
            else:
                complaint_id = with_temp_upload(
                    image_file,
                    lambda p: complaint.submit_complaint(
                        user_id=user["id"],
                        category=category,
                        description=description,
                        location=location,
                        image_source_path=p,
                    ),
                )
        except complaint.ComplaintError as exc:
            st.error(f"Complaint submission failed: {exc}")
        except Exception as exc:
            st.error(f"Unexpected error while submitting: {exc}")
        else:
            flash(
                "success",
                f"Complaint #{complaint_id} submitted successfully. You can now track its status.",
            )
            st.session_state.page = "My Complaints"
            st.rerun()



def render_my_complaints(complaints) -> None:
    st.subheader(f"My Complaints · {len(complaints)}")

    # Inline full-image viewer. Nothing opens in a separate window.
    selected_image = st.session_state.get("view_image_path")
    if selected_image:
        st.markdown("### Full Image Preview")
        image_col, close_col = st.columns([5, 1])
        with image_col:
            open_image_inline(selected_image, "Full-size complaint preview")
        with close_col:
            st.write("")
            st.write("")
            if st.button("Close Preview", use_container_width=True):
                st.session_state.view_image_path = None
                st.rerun()
        st.markdown("---")

    if not complaints:
        st.info("You haven't submitted any complaints yet.")
        return

    for c in complaints:
        title = f"#{c['id']} · {c['category']} · {c['status']}"
        with st.expander(title):
            left, right = st.columns([1.25, 0.9])

            with left:
                st.markdown(status_badge(c["status"]), unsafe_allow_html=True)
                st.write("")
                st.markdown("**Location / Address**")
                st.write(c.get("location") or "Not provided")
                st.markdown("**Description**")
                st.write(c["description"])
                st.markdown("**Admin Remark**")
                st.info(c["admin_remark"] or "No administrator remark has been added yet.")
                st.caption(
                    f"Submitted: {c['created_at']}  ·  Last updated: {c['updated_at']}"
                )

            with right:
                st.markdown("**Complaint Photo**")
                if c.get("image_path"):
                    abs_path = utils.resolve_upload_path(c["image_path"])
                    if os.path.exists(abs_path):
                        st.image(abs_path, caption="Attached image", use_container_width=True)
                        if st.button(
                            "View Full Image",
                            key=f"user_full_image_{c['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.view_image_path = c["image_path"]
                            st.rerun()
                    else:
                        st.warning("The image file is not available on this deployment.")
                else:
                    st.caption("No image was attached to this complaint.")

                if c.get("resolution_image_path"):
                    st.markdown("**Resolution Photo**")
                    abs_res_path = utils.resolve_upload_path(c["resolution_image_path"])
                    if os.path.exists(abs_res_path):
                        st.image(
                            abs_res_path,
                            caption="Repaired / resolved by admin",
                            use_container_width=True,
                        )
                    else:
                        st.warning("The resolution photo is not available on this deployment.")



def render_check_status(user, complaints) -> None:
    st.subheader("Check Complaint Status")

    if not complaints:
        st.info("You have no complaints yet. Submit one first.")
        return

    labels = [
        f"#{c['id']} · {c['category']} · {c['created_at']}"
        for c in complaints
    ]
    selected = st.selectbox("Select Complaint", labels)
    selected_id = complaints[labels.index(selected)]["id"]

    if st.button("Check Status", type="primary"):
        try:
            status = complaint.get_complaint_status(user["id"], selected_id)
        except complaint.ComplaintError as exc:
            st.error(f"Could not read status: {exc}")
        else:
            st.markdown(
                f"### Current status: {status_badge(status)}",
                unsafe_allow_html=True,
            )
            if status == "Resolved":
                st.success("This complaint has been marked resolved.")
            elif status == "Rejected":
                st.warning("This complaint has been rejected. Check the admin remark in My Complaints.")
            elif status == "In Progress":
                st.info("The complaint is currently being worked on.")
            else:
                st.info("The complaint is waiting for processing.")



def render_upload_image(user, complaints) -> None:
    st.subheader("Upload / Replace Complaint Image")

    if not complaints:
        st.info("You have no complaints yet. Submit one first.")
        return

    labels = [
        f"#{c['id']} · {c['category']} · {c['status']}"
        for c in complaints
    ]

    with st.form("upload_image_form"):
        selected = st.selectbox("Select Complaint", labels)
        image_file = st.file_uploader(
            "Choose Image",
            type=["png", "jpg", "jpeg", "gif", "bmp"],
        )
        submitted = st.form_submit_button(
            "Attach Image",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if image_file is None:
            st.error("Please choose an image first.")
        else:
            complaint_id = complaints[labels.index(selected)]["id"]
            try:
                with_temp_upload(
                    image_file,
                    lambda p: complaint.attach_image(
                        user_id=user["id"],
                        complaint_id=complaint_id,
                        image_source_path=p,
                    ),
                )
            except complaint.ComplaintError as exc:
                st.error(f"Image upload failed: {exc}")
            except Exception as exc:
                st.error(f"Unexpected upload error: {exc}")
            else:
                flash(
                    "success",
                    f"Image for complaint #{complaint_id} was attached successfully.",
                )
                st.session_state.page = "My Complaints"
                st.rerun()



def render_edit_profile(user) -> None:
    st.subheader("Edit Profile")

    with st.form("edit_profile_form"):
        name = st.text_input("Full Name", value=user["name"])
        phone = st.text_input("Phone Number", value=user.get("phone") or "")
        st.text_input("Email Address", value=user["email"], disabled=True)
        submitted = st.form_submit_button(
            "Save Changes",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        new_name = (name or "").strip()
        new_phone = (phone or "").strip()

        if not utils.is_non_empty(new_name):
            st.error("Name cannot be empty.")
        elif not utils.is_valid_phone(new_phone):
            st.error("Please enter a valid phone number.")
        else:
            try:
                updated = models.update_user_profile(
                    user["id"], new_name, new_phone
                )
                if not updated:
                    raise RuntimeError("No profile row was updated.")
                user["name"] = new_name
                user["phone"] = new_phone
                activity_log.log_edit_profile(user["id"])
            except Exception as exc:
                st.error(f"Profile update failed: {exc}")
            else:
                flash("success", "Profile updated successfully.")
                st.rerun()



def render_activity_log(user) -> None:
    st.subheader("Activity Log")
    logs = activity_log.get_logs_for_user(user["id"])

    if not logs:
        st.info("No activity has been recorded yet.")
    else:
        for row in logs[:50]:
            st.markdown(
                f"""
                <div class="mini-card">
                    <b>{row['activity']}</b>
                    <div class="muted">{row['created_at']} · {row['source']}</div>
                    <div>{row['response'] or ''}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Admin interface
# ---------------------------------------------------------------------------
ADMIN_PAGES = ["Overview", "Manage Complaints", "Activity Log"]


def render_admin_sidebar(admin_user) -> None:
    with st.sidebar:
        st.markdown("## CivicCare")
        st.caption("Administrator Console")
        st.markdown("---")
        st.markdown(f"### {admin_user['name']}")
        st.caption(admin_user["email"])
        st.markdown("---")

        if "admin_navigation" not in st.session_state:
            st.session_state.admin_navigation = st.session_state.get("page", "Overview")

        page = st.radio(
            "Navigation",
            ADMIN_PAGES,
            key="admin_navigation",
            label_visibility="collapsed",
        )
        st.session_state.page = page

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            do_logout()


def render_admin_dashboard(admin_user) -> None:
    render_admin_sidebar(admin_user)
    complaints = complaint.get_all_complaints(
        admin_id=admin_user["id"],
        log=False,
    )

    hero(
        "Admin Control Center",
        f"Signed in as {admin_user['name']} · monitor, review, update and report.",
    )
    render_flashes()

    if st.session_state.page == "Overview":
        render_admin_overview(complaints, admin_user)
    elif st.session_state.page == "Manage Complaints":
        render_manage_complaints(complaints, admin_user)
    else:
        render_admin_activity()


def render_admin_overview(complaints, admin_user) -> None:
    counts = {status: 0 for status in models.COMPLAINT_STATUSES}
    for c in complaints:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    cards = st.columns(5)
    values = [
        ("Total", len(complaints), DARK),
        ("Pending", counts["Pending"], WARNING),
        ("In Progress", counts["In Progress"], PRIMARY),
        ("Resolved", counts["Resolved"], SUCCESS),
        ("Rejected", counts["Rejected"], DANGER),
    ]
    for col, (label, value, color) in zip(cards, values):
        with col:
            metric_card(label, value, color)

    st.write("")

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Latest complaints")
        latest = complaints[:8]

        if not latest:
            st.info("No complaints have been submitted yet.")
        else:
            for c in latest:
                row = st.columns([0.55, 1.5, 1.2, 1.15])
                row[0].write(f"#{c['id']}")
                row[1].write(c["user_name"])
                row[2].write(c["category"])
                row[3].markdown(
                    status_badge(c["status"]),
                    unsafe_allow_html=True,
                )

    with right:
        st.subheader("Reports")
        st.write(
            "Create a CSV export of all complaints for demonstrations, evaluation, or documentation."
        )
        if st.button(
            "Generate CSV Report",
            type="primary",
            use_container_width=True,
        ):
            try:
                filepath = report.generate_report(admin_id=admin_user["id"])
            except Exception as exc:
                st.error(f"Report generation failed: {exc}")
            else:
                st.success("CSV report generated successfully.")
                safe_download(
                    filepath,
                    os.path.basename(filepath),
                )


def render_manage_complaints(complaints, admin_user) -> None:
    st.subheader(f"Manage Complaints · {len(complaints)}")

    c1, c2, c3 = st.columns(3)
    with c1:
        status_filter = st.selectbox(
            "Status",
            ["All"] + models.COMPLAINT_STATUSES,
        )
    with c2:
        category_filter = st.selectbox(
            "Category",
            ["All"] + models.COMPLAINT_CATEGORIES,
        )
    with c3:
        search = st.text_input(
            "Search",
            placeholder="User name or category",
        )

    filtered = complaints
    if status_filter != "All":
        filtered = [c for c in filtered if c["status"] == status_filter]
    if category_filter != "All":
        filtered = [c for c in filtered if c["category"] == category_filter]
    if search.strip():
        needle = search.strip().lower()
        filtered = [
            c for c in filtered
            if needle in (c.get("user_name") or "").lower()
            or needle in (c.get("category") or "").lower()
            or needle in (c.get("user_email") or "").lower()
        ]

    if not filtered:
        st.info("No complaints match the selected filters.")
        return

    options = [
        f"#{c['id']} · {c['category']} · {c['user_name']} · {c['status']}"
        for c in filtered
    ]
    default_index = 0
    existing = st.session_state.get("selected_complaint")
    if existing:
        for i, c in enumerate(filtered):
            if c["id"] == existing:
                default_index = i
                break

    selected_label = st.selectbox(
        "Select a complaint to view full details",
        options,
        index=default_index,
    )
    selected = filtered[options.index(selected_label)]
    st.session_state.selected_complaint = selected["id"]

    st.markdown("---")

    left, right = st.columns([1.05, 0.95])

    with left:
        st.markdown(f"### Complaint #{selected['id']} · {selected['category']}")
        st.markdown(status_badge(selected["status"]), unsafe_allow_html=True)
        st.write("")
        st.markdown("**Citizen details**")
        st.write(f"**Name:** {selected['user_name']}")
        st.write(f"**Email:** {selected['user_email']}")
        st.write(f"**Phone:** {selected.get('user_phone') or 'N/A'}")
        st.caption(f"Submitted: {selected['created_at']}")
        st.markdown("**Location / Address**")
        st.write(selected.get("location") or "Not provided")
        st.markdown("**Description**")
        st.write(selected["description"])

    with right:
        st.markdown("### Attached image")
        if selected.get("image_path"):
            abs_path = utils.resolve_upload_path(selected["image_path"])
            if os.path.exists(abs_path):
                st.image(
                    abs_path,
                    caption=f"Complaint #{selected['id']} image",
                    use_container_width=True,
                )
                if st.button(
                    "View Full Image",
                    key=f"admin_full_image_{selected['id']}",
                    use_container_width=True,
                ):
                    st.session_state.view_image_path = selected["image_path"]
                    st.rerun()
            else:
                st.warning("The image file is not available on this deployment.")
        else:
            st.info("No image was attached to this complaint.")

        selected_image = st.session_state.get("view_image_path")
        if selected_image:
            st.markdown("---")
            st.markdown("#### Full Image Preview")
            open_image_inline(selected_image, "Selected image preview")
            if st.button(
                "Close Image Preview",
                key="admin_close_full_image",
                use_container_width=True,
            ):
                st.session_state.view_image_path = None
                st.rerun()

        if selected.get("resolution_image_path"):
            st.markdown("### Resolution photo")
            abs_res_path = utils.resolve_upload_path(selected["resolution_image_path"])
            if os.path.exists(abs_res_path):
                st.image(
                    abs_res_path,
                    caption=f"Complaint #{selected['id']} resolution photo",
                    use_container_width=True,
                )
            else:
                st.warning("The resolution photo is not available on this deployment.")

    st.markdown("---")
    st.subheader("Update complaint")

    status = st.selectbox(
        "New Status",
        models.COMPLAINT_STATUSES,
        index=(
            models.COMPLAINT_STATUSES.index(selected["status"])
            if selected["status"] in models.COMPLAINT_STATUSES
            else 0
        ),
    )
    remark = st.text_area(
        "Admin Remark",
        value=selected.get("admin_remark") or "",
        height=120,
        placeholder="Add a clear update for the citizen...",
    )
    resolution_image_file = st.file_uploader(
        "Resolution / Repaired Photo (shown to the citizen once uploaded)",
        type=["png", "jpg", "jpeg", "gif", "bmp"],
        help="Optional. Upload a photo of the fixed issue, e.g. when marking the complaint Resolved.",
        key=f"resolution_photo_{selected['id']}",
    )

    save_col, refresh_col = st.columns([1.3, 1])
    with save_col:
        if st.button(
            "Save Complaint Update",
            type="primary",
            use_container_width=True,
        ):
            try:
                if resolution_image_file is None:
                    complaint.manage_complaint(
                        admin_id=admin_user["id"],
                        complaint_id=selected["id"],
                        new_status=status,
                        admin_remark=remark.strip(),
                    )
                else:
                    with_temp_upload(
                        resolution_image_file,
                        lambda p: complaint.manage_complaint(
                            admin_id=admin_user["id"],
                            complaint_id=selected["id"],
                            new_status=status,
                            admin_remark=remark.strip(),
                            resolution_image_source_path=p,
                        ),
                    )
            except complaint.ComplaintError as exc:
                st.error(f"Update failed: {exc}")
            except Exception as exc:
                st.error(f"Unexpected update error: {exc}")
            else:
                flash(
                    "success",
                    f"Complaint #{selected['id']} updated successfully.",
                )
                st.rerun()

    with refresh_col:
        if st.button("Refresh Data", use_container_width=True):
            st.rerun()



def render_admin_activity() -> None:
    st.subheader("System Activity Log")

    logs = activity_log.get_all_logs()
    if not logs:
        st.info("No activity has been logged yet.")
    else:
        for row in logs[:100]:
            complaint_text = (
                f" · Complaint #{row['complaint_id']}"
                if row.get("complaint_id")
                else ""
            )
            st.markdown(
                f"""
                <div class="mini-card">
                    <b>{row['activity']}</b>{complaint_text}
                    <div class="muted">{row['created_at']} · {row['source']}</div>
                    <div>{row['response'] or ''}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def main() -> None:
    user = st.session_state.get("user")
    if user is None:
        render_auth()
    elif auth.is_admin(user):
        render_admin_dashboard(user)
    else:
        render_user_dashboard(user)


if __name__ == "__main__":
    main()
