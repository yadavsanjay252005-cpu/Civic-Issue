"""
admin.py

The complete Admin Dashboard. Features modern summary cards, clean typography, 
and heavily styled tables via ttk.Style.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk

import complaint
import models
import report
import utils

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def build_admin_dashboard(root, current_user, on_logout):
    AdminDashboard(root, current_user, on_logout)


class AdminDashboard:
    def __init__(self, root, current_user, on_logout):
        self.root = root
        self.current_user = current_user
        self.on_logout = on_logout
        self.tree = None
        self.complaints_cache = []

        # Configure global ttk style for tables in admin view
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=35, font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#ecf0f1", foreground="#2c3e50")
        style.map("Treeview", background=[("selected", "#3498db")], foreground=[("selected", "white")])

        # Card variables
        self.var_total = tk.StringVar(value="0")
        self.var_pending = tk.StringVar(value="0")
        self.var_inprogress = tk.StringVar(value="0")
        self.var_resolved = tk.StringVar(value="0")
        self.var_rejected = tk.StringVar(value="0")

        self._build_layout()
        self.refresh_complaints()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text=f"Admin Control Panel - {self.current_user['name']}",
            font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="white"
        ).pack(side="left", padx=25)

        tk.Button(
            header, text="Logout", width=12, font=("Helvetica", 9, "bold"), bg="#e74c3c", fg="white",
            relief="flat", cursor="hand2", activebackground="#c0392b", command=self._handle_logout
        ).pack(side="right", padx=25)

        # Main Workspace
        workspace = tk.Frame(self.root, bg="#ecf0f1")
        workspace.pack(fill="both", expand=True, padx=25, pady=20)

        # Summary Cards Panel
        summary_frame = tk.Frame(workspace, bg="#ecf0f1")
        summary_frame.pack(fill="x", pady=(0, 20))

        def make_card(parent, title, text_var, top_color):
            card = tk.Frame(parent, bg="white", width=160, height=80, relief="flat")
            card.pack_propagate(False)
            card.pack(side="left", padx=(0, 15))
            # Colored top border effect
            tk.Frame(card, bg=top_color, height=4).pack(fill="x", side="top")
            tk.Label(card, text=title, font=("Helvetica", 10), bg="white", fg="#7f8c8d").pack(pady=(10, 0))
            tk.Label(card, textvariable=text_var, font=("Helvetica", 18, "bold"), bg="white", fg="#2c3e50").pack()

        make_card(summary_frame, "Total", self.var_total, "#34495e")
        make_card(summary_frame, "Pending", self.var_pending, "#e67e22")
        make_card(summary_frame, "In Progress", self.var_inprogress, "#f1c40f")
        make_card(summary_frame, "Resolved", self.var_resolved, "#2ecc71")
        make_card(summary_frame, "Rejected", self.var_rejected, "#e74c3c")

        # Toolbar
        toolbar = tk.Frame(workspace, bg="#ecf0f1")
        toolbar.pack(fill="x", pady=(0, 15))

        tk.Button(toolbar, text="Refresh Data", width=15, bg="white", font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2", command=self.refresh_complaints).pack(side="left", padx=(0, 10), ipady=4)
        tk.Button(toolbar, text="View Details", width=15, bg="#2980b9", fg="white", font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2", command=self.open_selected_details).pack(side="left", padx=(0, 10), ipady=4)
        tk.Button(toolbar, text="Generate CSV Report", width=20, bg="#27ae60", fg="white", font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2", command=self.handle_generate_report).pack(side="left", padx=(0, 10), ipady=4)

        # Table Frame
        table_container = tk.Frame(workspace, bg="white", padx=2, pady=2, relief="flat")
        table_container.pack(fill="both", expand=True)

        v_scroll = ttk.Scrollbar(table_container, orient="vertical")
        h_scroll = ttk.Scrollbar(table_container, orient="horizontal")

        columns = ("id", "user_name", "category", "image", "status", "created_at")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=15, yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.config(command=self.tree.yview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.config(command=self.tree.xview)
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        headings = {"id": "ID", "user_name": "User Name", "category": "Category", "image": "Has Image", "status": "Status", "created_at": "Date Submitted"}
        widths = {"id": 50, "user_name": 180, "category": 140, "image": 90, "status": 120, "created_at": 180}
        
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center" if col in ("id", "image", "status") else "w")

        self.tree.bind("<Double-1>", lambda event: self.open_selected_details())

    def _handle_logout(self):
        self.on_logout()

    # ------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------
    def refresh_complaints(self):
        self.complaints_cache = complaint.get_all_complaints(admin_id=self.current_user["id"])
        for row in self.tree.get_children(): self.tree.delete(row)

        counts = {"Pending": 0, "In Progress": 0, "Resolved": 0, "Rejected": 0}
        
        for c in self.complaints_cache:
            counts[c["status"]] = counts.get(c["status"], 0) + 1
            has_img = "Yes" if c.get("image_path") else "No"
            self.tree.insert("", "end", iid=str(c["id"]), values=(c["id"], c["user_name"], c["category"], has_img, c["status"], c["created_at"]))

        self.var_total.set(str(len(self.complaints_cache)))
        self.var_pending.set(str(counts['Pending']))
        self.var_inprogress.set(str(counts['In Progress']))
        self.var_resolved.set(str(counts['Resolved']))
        self.var_rejected.set(str(counts['Rejected']))

    # ------------------------------------------------------------------
    # Complaint Details Window
    # ------------------------------------------------------------------
    def open_selected_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a complaint row first.")
            return
        self.open_complaint_details(int(selected[0]))

    def open_complaint_details(self, complaint_id):
        try:
            details = complaint.get_complaint_details(complaint_id)
        except complaint.ComplaintError as exc:
            messagebox.showerror("Error", str(exc))
            return

        window = tk.Toplevel(self.root)
        window.title(f"Manage Complaint #{complaint_id}")
        window.geometry("800x650")
        window.configure(bg="#ecf0f1")
        window.resizable(False, False)

        header = tk.Frame(window, bg="#34495e", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"Complaint #{complaint_id} - {details['category']}", font=("Helvetica", 14, "bold"), bg="#34495e", fg="white").pack(side="left", padx=20)

        main_frame = tk.Frame(window, bg="#ecf0f1", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(main_frame, bg="#ecf0f1")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_col = tk.Frame(main_frame, bg="#ecf0f1")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- LEFT COLUMN (Info & Description) ---
        info_card = tk.Frame(left_col, bg="white", padx=20, pady=20, relief="flat")
        info_card.pack(fill="x", pady=(0, 20))
        tk.Label(info_card, text="Submitter Details", font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        tk.Label(info_card, text=f"Name: {details['user_name']}", font=("Helvetica", 10), bg="white").pack(anchor="w")
        tk.Label(info_card, text=f"Email: {details['user_email']}", font=("Helvetica", 10), bg="white").pack(anchor="w")
        tk.Label(info_card, text=f"Phone: {details.get('user_phone') or 'N/A'}", font=("Helvetica", 10), bg="white").pack(anchor="w")
        tk.Label(info_card, text=f"Date: {details['created_at']}", font=("Helvetica", 10), bg="white", fg="#7f8c8d").pack(anchor="w", pady=(10, 0))

        desc_card = tk.Frame(left_col, bg="white", padx=20, pady=20, relief="flat")
        desc_card.pack(fill="both", expand=True)
        tk.Label(desc_card, text="Complaint Description", font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        desc_box = tk.Text(desc_card, height=6, width=40, font=("Helvetica", 10), bg="#f8f9fa", relief="flat")
        desc_box.insert("1.0", details["description"])
        desc_box.config(state="disabled")
        desc_box.pack(fill="both", expand=True)

        # --- RIGHT COLUMN (Image & Management) ---
        img_card = tk.Frame(right_col, bg="white", padx=20, pady=15, relief="flat")
        img_card.pack(fill="x", pady=(0, 20))
        tk.Label(img_card, text="Attached Image", font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        
        img_container = tk.Frame(img_card, bg="#f8f9fa", width=220, height=140, relief="flat", highlightbackground="#bdc3c7", highlightthickness=1)
        img_container.pack_propagate(False)
        img_container.pack(anchor="w", pady=(0, 10))
        img_lbl = tk.Label(img_container, bg="#f8f9fa")
        img_lbl.pack(expand=True, fill="both")

        has_valid_image = False
        abs_img_path = utils.resolve_upload_path(details.get("image_path"))
        
        if not details.get("image_path"):
            img_lbl.config(text="No image provided", fg="#7f8c8d", font=("Helvetica", 10))
        elif not os.path.exists(abs_img_path):
            img_lbl.config(text="File missing from disk", fg="#e74c3c", font=("Helvetica", 10))
        elif not HAS_PIL:
            img_lbl.config(text="Install Pillow to preview", fg="#f39c12", font=("Helvetica", 10))
            has_valid_image = True
        else:
            try:
                img = Image.open(abs_img_path)
                img.thumbnail((210, 130))
                photo = ImageTk.PhotoImage(img)
                img_lbl.config(image=photo)
                img_lbl.image = photo 
                has_valid_image = True
            except Exception:
                img_lbl.config(text="Corrupt image format", fg="#e74c3c")

        if has_valid_image:
            tk.Button(img_card, text="View Full Image", font=("Helvetica", 9), bg="#ecf0f1", relief="flat", cursor="hand2", command=lambda: self.open_full_image(abs_img_path)).pack(anchor="w", ipady=2, ipadx=5)

        action_card = tk.Frame(right_col, bg="white", padx=20, pady=20, relief="flat")
        action_card.pack(fill="both", expand=True)
        tk.Label(action_card, text="Update Status", font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 5))
        status_var = tk.StringVar(value=details["status"])
        ttk.Combobox(action_card, textvariable=status_var, values=models.COMPLAINT_STATUSES, state="readonly", width=30, font=("Helvetica", 10)).pack(anchor="w", pady=(0, 15))

        tk.Label(action_card, text="Admin Remark", font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 5))
        rem_box = tk.Text(action_card, height=4, width=33, font=("Helvetica", 10), bg="#f8f9fa", relief="flat")
        rem_box.insert("1.0", details["admin_remark"] or "")
        rem_box.pack(anchor="w", pady=(0, 20), fill="x")

        def save_changes():
            try:
                complaint.manage_complaint(
                    admin_id=self.current_user["id"], complaint_id=complaint_id,
                    new_status=status_var.get(), admin_remark=rem_box.get("1.0", "end").strip()
                )
            except complaint.ComplaintError as exc:
                messagebox.showerror("Update Failed", str(exc))
                return
            messagebox.showinfo("Success", "Complaint updated successfully.")
            window.destroy()
            self.refresh_complaints()

        tk.Button(action_card, text="SAVE CHANGES", width=30, bg="#27ae60", fg="white", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=save_changes).pack(anchor="w", ipady=6)

    def open_full_image(self, abs_img_path):
        if not os.path.exists(abs_img_path): return
        top = tk.Toplevel(self.root)
        top.title("Full Image View")
        top.configure(bg="#2c3e50")
        
        if not HAS_PIL:
            try:
                img = tk.PhotoImage(file=abs_img_path)
                lbl = tk.Label(top, image=img, bg="#2c3e50")
                lbl.image = img
                lbl.pack(padx=20, pady=20)
                return
            except tk.TclError:
                messagebox.showerror("Error", "Pillow not installed. Cannot view this file type.")
                top.destroy()
                return

        try:
            img = Image.open(abs_img_path)
            img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(top, image=photo, bg="#2c3e50")
            lbl.image = photo 
            lbl.pack(padx=20, pady=20)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            top.destroy()

    def handle_generate_report(self):
        try:
            filepath = report.generate_report(admin_id=self.current_user["id"])
            messagebox.showinfo("Success", f"CSV Report Generated successfully at:\n\n{filepath}")
        except Exception as exc: 
            messagebox.showerror("Report Failed", str(exc))