"""
user.py

The complete User Dashboard, featuring a modern, white-card UI approach.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import activity_log
import complaint
import models
import utils

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def build_user_dashboard(root, current_user, on_logout):
    UserDashboard(root, current_user, on_logout)


class UserDashboard:
    def __init__(self, root, current_user, on_logout):
        self.root = root
        self.current_user = current_user
        self.on_logout = on_logout
        
        # Configure global ttk style for tables in popups
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=30, font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#ecf0f1", foreground="#2c3e50")
        style.map("Treeview", background=[("selected", "#3498db")], foreground=[("selected", "white")])

        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        # Top Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill="x")
        header.pack_propagate(False) # Keep fixed height

        tk.Label(
            header, text="Complaint Management System", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="white"
        ).pack(side="left", padx=25)

        tk.Button(
            header, text="Logout", width=12, font=("Helvetica", 9, "bold"), bg="#e74c3c", fg="white",
            relief="flat", cursor="hand2", activebackground="#c0392b", activeforeground="white",
            command=self._handle_logout
        ).pack(side="right", padx=25)

        # Welcome Text
        welcome_frame = tk.Frame(self.root, bg="#ecf0f1")
        welcome_frame.pack(fill="x", pady=(30, 10))
        tk.Label(
            welcome_frame, text=f"Welcome back, {self.current_user['name']}!", 
            font=("Helvetica", 16), bg="#ecf0f1", fg="#34495e"
        ).pack(anchor="center")

        # Main Card for Menu
        card = tk.Frame(self.root, bg="white", padx=40, pady=40, relief="flat")
        card.pack(expand=True)

        buttons = [
            ("Submit Complaint", self.open_submit_complaint, "#2980b9"),
            ("My Complaints", self.open_my_complaints, "#2980b9"),
            ("View Complaint Status", self.open_view_status, "#8e44ad"),
            ("Upload/Replace Image", self.open_upload_image, "#f39c12"),
            ("Edit Profile", self.open_edit_profile, "#27ae60"),
        ]

        for i, (label, command, color) in enumerate(buttons):
            row, col = divmod(i, 2)
            # Create styling on the fly for each flat button
            btn = tk.Button(
                card, text=label, width=22, bg=color, fg="white", font=("Helvetica", 11, "bold"),
                relief="flat", cursor="hand2", command=command
            )
            # A little hover effect logic wrapper
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=self._lighten_color(c)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
            
            # Special spanning for odd numbers of buttons
            if i == len(buttons) - 1 and len(buttons) % 2 != 0:
                btn.grid(row=row, column=0, columnspan=2, padx=15, pady=15, ipady=12)
            else:
                btn.grid(row=row, column=col, padx=15, pady=15, ipady=12)

    def _lighten_color(self, hex_color):
        """Helper to slightly lighten a hex color for hover effect."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb_light = tuple(min(255, int(c * 1.2)) for c in rgb)
        return "#{:02x}{:02x}{:02x}".format(*rgb_light)

    def _handle_logout(self):
        self.on_logout()

    # ------------------------------------------------------------------
    # Helper for sleek popups
    # ------------------------------------------------------------------
    def _create_popup(self, title, size):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(size)
        window.configure(bg="#ecf0f1")
        
        header = tk.Frame(window, bg="#34495e", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, font=("Helvetica", 14, "bold"), bg="#34495e", fg="white").pack(side="left", padx=20)
        
        main_frame = tk.Frame(window, bg="#ecf0f1", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        return window, main_frame

    # ------------------------------------------------------------------
    # Submit Complaint
    # ------------------------------------------------------------------
    def open_submit_complaint(self):
        window, main_frame = self._create_popup("Submit a New Complaint", "600x550")
        window.resizable(False, False)

        card = tk.Frame(main_frame, bg="white", padx=30, pady=20, relief="flat")
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Category", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        category_var = tk.StringVar(value=models.COMPLAINT_CATEGORIES[0])
        category_menu = ttk.Combobox(card, textvariable=category_var, values=models.COMPLAINT_CATEGORIES, state="readonly", width=40, font=("Helvetica", 11))
        category_menu.pack(anchor="w", pady=(0, 15))

        tk.Label(card, text="Description", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        description_text = tk.Text(card, height=5, width=50, font=("Helvetica", 11), bg="#f8f9fa", relief="flat", highlightbackground="#bdc3c7", highlightthickness=1)
        description_text.pack(anchor="w", pady=(0, 15))

        tk.Label(card, text="Upload Image (Optional)", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        
        img_panel = tk.Frame(card, bg="white")
        img_panel.pack(fill="x", anchor="w")

        preview_frame = tk.Frame(img_panel, width=100, height=80, bg="#f8f9fa", relief="flat", highlightbackground="#bdc3c7", highlightthickness=1)
        preview_frame.pack_propagate(False)
        preview_frame.pack(side="left", padx=(0, 15))
        
        preview_lbl = tk.Label(preview_frame, text="No Image", bg="#f8f9fa", fg="#7f8c8d", font=("Helvetica", 9))
        preview_lbl.pack(expand=True, fill="both")

        controls_frame = tk.Frame(img_panel, bg="white")
        controls_frame.pack(side="left", fill="y")

        image_path_var = tk.StringVar(value="")
        file_name_lbl = tk.Label(controls_frame, text="None selected", bg="white", fg="#7f8c8d", font=("Helvetica", 9))
        file_name_lbl.pack(anchor="w", pady=(0, 10))

        def choose_image():
            path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
            if path:
                image_path_var.set(path)
                file_name_lbl.config(text=os.path.basename(path), fg="#2c3e50")
                if HAS_PIL:
                    try:
                        img = Image.open(path)
                        img.thumbnail((90, 70))
                        photo = ImageTk.PhotoImage(img)
                        preview_lbl.config(image=photo, text="")
                        preview_lbl.image = photo
                    except Exception:
                        pass

        def remove_image():
            image_path_var.set("")
            file_name_lbl.config(text="None selected", fg="#7f8c8d")
            preview_lbl.config(image="", text="No Image")
            preview_lbl.image = None

        btn_frame = tk.Frame(controls_frame, bg="white")
        btn_frame.pack(anchor="w")
        tk.Button(btn_frame, text="Browse...", font=("Helvetica", 9), bg="#ecf0f1", relief="flat", cursor="hand2", command=choose_image).pack(side="left", padx=(0, 10), ipady=2, ipadx=5)
        tk.Button(btn_frame, text="Remove", font=("Helvetica", 9), bg="#ecf0f1", relief="flat", cursor="hand2", command=remove_image).pack(side="left", ipady=2, ipadx=5)

        def submit():
            try:
                comp_id = complaint.submit_complaint(
                    user_id=self.current_user["id"], category=category_var.get(),
                    description=description_text.get("1.0", "end"), image_source_path=image_path_var.get() or None,
                )
            except complaint.ComplaintError as exc:
                messagebox.showerror("Submission Failed", str(exc))
                return
            messagebox.showinfo("Success", f"Complaint submitted successfully!\nComplaint ID: #{comp_id}")
            window.destroy()

        tk.Button(card, text="Submit Complaint", width=25, bg="#2980b9", fg="white", font=("Helvetica", 11, "bold"), relief="flat", cursor="hand2", command=submit).pack(pady=(20, 0), ipady=8)

    # ------------------------------------------------------------------
    # My Complaints (list view)
    # ------------------------------------------------------------------
    def open_my_complaints(self):
        window, main_frame = self._create_popup("My Complaints", "900x500")

        card = tk.Frame(main_frame, bg="white", padx=15, pady=15, relief="flat")
        card.pack(fill="both", expand=True)

        v_scroll = ttk.Scrollbar(card, orient="vertical")
        h_scroll = ttk.Scrollbar(card, orient="horizontal")

        columns = ("id", "category", "status", "image", "created_at", "remark")
        tree = ttk.Treeview(card, columns=columns, show="headings", height=12, yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.config(command=tree.yview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.config(command=tree.xview)
        h_scroll.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)

        headings = {"id": "ID", "category": "Category", "status": "Status", "image": "Image", "created_at": "Submitted On", "remark": "Admin Remark"}
        widths = {"id": 50, "category": 120, "status": 120, "image": 70, "created_at": 160, "remark": 320}
        
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="center" if col in ("id", "image", "status") else "w")

        my_complaints = complaint.get_user_complaints(self.current_user["id"])
        
        for c in my_complaints:
            has_img = "Yes" if c.get("image_path") else "No"
            tree.insert("", "end", iid=str(c["id"]), values=(c["id"], c["category"], c["status"], has_img, c["created_at"], c["admin_remark"] or ""))

        if not my_complaints:
            tk.Label(card, text="You haven't submitted any complaints yet.", fg="#7f8c8d", bg="white", font=("Helvetica", 11)).pack(pady=40)

        tree.bind("<Double-1>", lambda event: self.view_complaint_details(tree, my_complaints))

    def view_complaint_details(self, tree, my_complaints):
        selected = tree.selection()
        if not selected: return
        c_id = int(selected[0])
        comp = next((c for c in my_complaints if c["id"] == c_id), None)
        if not comp: return
            
        top, mf = self._create_popup(f"Complaint #{c_id} Details", "450x380")
        card = tk.Frame(mf, bg="white", padx=20, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text=f"Category: {comp['category']}", font=("Helvetica", 12, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 5))
        tk.Label(card, text=f"Status: {comp['status']}", font=("Helvetica", 11), bg="white", fg="#e67e22" if comp['status'] == "Pending" else "#27ae60").pack()
        
        tk.Label(card, text="Description", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(15, 5))
        desc = tk.Text(card, height=4, width=45, font=("Helvetica", 10), bg="#f8f9fa", relief="flat")
        desc.insert("1.0", comp["description"])
        desc.config(state="disabled")
        desc.pack()
        
        tk.Label(card, text="Admin Remark", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(15, 5))
        rem = tk.Text(card, height=3, width=45, font=("Helvetica", 10), bg="#f8f9fa", relief="flat")
        rem.insert("1.0", comp["admin_remark"] or "No remarks yet.")
        rem.config(state="disabled")
        rem.pack()

    # ------------------------------------------------------------------
    # View Complaint Status
    # ------------------------------------------------------------------
    def open_view_status(self):
        my_complaints = complaint.get_user_complaints(self.current_user["id"])
        if not my_complaints:
            messagebox.showinfo("No Complaints", "You have no complaints yet.")
            return

        window, main_frame = self._create_popup("Check Status", "450x300")
        card = tk.Frame(main_frame, bg="white", padx=30, pady=30, relief="flat")
        card.pack(fill="both", expand=True)

        labels = [f"#{c['id']} - {c['category']} ({c['created_at']})" for c in my_complaints]
        selection_var = tk.StringVar(value=labels[0])
        
        tk.Label(card, text="Select Complaint:", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        ttk.Combobox(card, textvariable=selection_var, values=labels, state="readonly", width=45, font=("Helvetica", 10)).pack(pady=(0, 20))

        status_label = tk.Label(card, text="", font=("Helvetica", 14, "bold"), bg="white", fg="#2980b9")
        status_label.pack(pady=10)

        def check_status():
            index = labels.index(selection_var.get())
            c_id = my_complaints[index]["id"]
            try:
                status = complaint.get_complaint_status(self.current_user["id"], c_id)
            except complaint.ComplaintError as exc:
                messagebox.showerror("Error", str(exc))
                return
            color = "#27ae60" if status == "Resolved" else "#e67e22" if status == "Pending" else "#2980b9"
            status_label.config(text=f"Current Status: {status}", fg=color)

        tk.Button(card, text="Check Status", width=20, bg="#ecf0f1", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=check_status).pack()

    # ------------------------------------------------------------------
    # Upload Image 
    # ------------------------------------------------------------------
    def open_upload_image(self):
        my_complaints = complaint.get_user_complaints(self.current_user["id"])
        if not my_complaints:
            messagebox.showinfo("No Complaints", "You have no complaints yet. Submit one first.")
            return

        window, main_frame = self._create_popup("Attach Image", "450x300")
        card = tk.Frame(main_frame, bg="white", padx=30, pady=20, relief="flat")
        card.pack(fill="both", expand=True)

        labels = [f"#{c['id']} - {c['category']} ({c['status']})" for c in my_complaints]
        selection_var = tk.StringVar(value=labels[0])
        
        tk.Label(card, text="Select Complaint:", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        ttk.Combobox(card, textvariable=selection_var, values=labels, state="readonly", width=45, font=("Helvetica", 10)).pack(anchor="w", pady=(0, 15))

        image_path_var = tk.StringVar(value="")
        image_label = tk.Label(card, text="No image selected", bg="white", fg="#7f8c8d", font=("Helvetica", 10))
        image_label.pack(pady=(5, 10))

        def choose_image():
            path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
            if path:
                image_path_var.set(path)
                image_label.config(text=os.path.basename(path), fg="#2c3e50")

        tk.Button(card, text="Browse Image...", font=("Helvetica", 10), bg="#ecf0f1", relief="flat", cursor="hand2", command=choose_image).pack()

        def upload():
            if not image_path_var.get():
                messagebox.showerror("No Image", "Please choose an image first.")
                return
            c_id = my_complaints[labels.index(selection_var.get())]["id"]
            try:
                complaint.attach_image(self.current_user["id"], c_id, image_path_var.get())
            except complaint.ComplaintError as exc:
                messagebox.showerror("Upload Failed", str(exc))
                return
            messagebox.showinfo("Success", "Image successfully attached.")
            window.destroy()

        tk.Button(card, text="Upload", width=20, bg="#2980b9", fg="white", font=("Helvetica", 11, "bold"), relief="flat", cursor="hand2", command=upload).pack(pady=(20, 0), ipady=5)

    # ------------------------------------------------------------------
    # Edit Profile
    # ------------------------------------------------------------------
    def open_edit_profile(self):
        window, main_frame = self._create_popup("Edit Profile", "400x350")
        card = tk.Frame(main_frame, bg="white", padx=30, pady=25, relief="flat")
        card.pack(fill="both", expand=True)

        def make_field(label_text, default_val, readonly=False):
            tk.Label(card, text=label_text, font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
            entry = tk.Entry(card, width=35, font=("Helvetica", 11), bg="#f8f9fa", relief="flat")
            entry.insert(0, default_val)
            if readonly:
                entry.config(state="readonly")
            entry.pack(anchor="w", pady=(0, 15), ipady=5)
            return entry

        name_entry = make_field("Full Name", self.current_user["name"])
        phone_entry = make_field("Phone Number", self.current_user.get("phone") or "")
        make_field("Email (Read-Only)", self.current_user["email"], readonly=True)

        def save():
            new_name = name_entry.get().strip()
            new_phone = phone_entry.get().strip()
            if not utils.is_non_empty(new_name):
                messagebox.showerror("Invalid", "Name cannot be empty.")
                return
            if not utils.is_valid_phone(new_phone):
                messagebox.showerror("Invalid", "Please enter a valid phone number.")
                return

            models.update_user_profile(self.current_user["id"], new_name, new_phone)
            self.current_user["name"] = new_name
            self.current_user["phone"] = new_phone
            activity_log.log_edit_profile(self.current_user["id"])
            messagebox.showinfo("Success", "Profile updated successfully.")
            window.destroy()

        tk.Button(card, text="Save Changes", width=20, bg="#27ae60", fg="white", font=("Helvetica", 11, "bold"), relief="flat", cursor="hand2", command=save).pack(pady=(10, 0), ipady=5)