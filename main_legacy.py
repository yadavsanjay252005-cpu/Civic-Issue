"""
main.py

Application entry point for the Complaint Management System.
Enhanced UI with modern flat design, centered card layouts, clean typography,
and robust error/success alerts.
"""

import tkinter as tk
from tkinter import messagebox

import admin
import auth
import database
import user

WINDOW_TITLE = "Complaint Management System"


class App:
    """Owns the single Tk root window and switches between screens."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        # Clean background for the entire app
        self.root.configure(bg="#ecf0f1")
        
        self.current_user = None
        self.show_login_screen()

    def _clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def _resize(self, size):
        self.root.geometry(size)
        self.root.minsize(int(size.split('x')[0]), int(size.split('x')[1]))

    def show_login_screen(self):
        self._clear_root()
        self._resize("600x500")
        self.current_user = None
        LoginScreen(self.root, self)

    def show_register_screen(self):
        self._clear_root()
        self._resize("600x650")
        RegisterScreen(self.root, self)

    def on_login_success(self, logged_in_user):
        self.current_user = logged_in_user
        self._clear_root()

        if auth.is_admin(logged_in_user):
            self._resize("1000x700") 
            admin.build_admin_dashboard(self.root, logged_in_user, self.logout)
        else:
            self._resize("850x600") 
            user.build_user_dashboard(self.root, logged_in_user, self.logout)

    def logout(self):
        if self.current_user is not None:
            auth.logout_user(self.current_user["id"])
        self.show_login_screen()

    def run(self):
        self.root.mainloop()


class LoginScreen:
    """Modern Card-based Login Screen with Form Validation."""

    def __init__(self, parent, app: App):
        self.app = app
        
        # Center card container
        card = tk.Frame(parent, bg="white", padx=50, pady=40, relief="flat")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            card, text="Complaint Management", font=("Helvetica", 18, "bold"), bg="white", fg="#2c3e50"
        ).pack(pady=(0, 5))
        tk.Label(
            card, text="Sign in to continue", font=("Helvetica", 11), bg="white", fg="#7f8c8d"
        ).pack(pady=(0, 30))

        # Email
        tk.Label(card, text="Email Address", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w")
        self.email_entry = tk.Entry(card, width=35, font=("Helvetica", 12), bg="#f8f9fa", relief="flat")
        self.email_entry.pack(pady=(5, 15), ipady=8)

        # Password
        tk.Label(card, text="Password", font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w")
        self.password_entry = tk.Entry(card, width=35, font=("Helvetica", 12), show="*", bg="#f8f9fa", relief="flat")
        self.password_entry.pack(pady=(5, 25), ipady=8)

        # Buttons
        tk.Button(
            card, text="LOGIN", width=32, bg="#2980b9", fg="white", font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2", activebackground="#3498db", activeforeground="white",
            command=self.handle_login
        ).pack(pady=(0, 10), ipady=6)

        tk.Button(
            card, text="Create an Account", width=32, bg="#ecf0f1", fg="#2c3e50", font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2", activebackground="#bdc3c7",
            command=app.show_register_screen
        ).pack(ipady=6)

        tk.Label(
            card, text="Default admin: admin@gmail.com / admin123", fg="#bdc3c7", bg="white", font=("Helvetica", 8)
        ).pack(side="bottom", pady=(25, 0))

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        # Explicit UI Validation 
        if not email or not password:
            messagebox.showerror("Login Error", "Please enter both your email and password.")
            return

        try:
            logged_in_user = auth.login_user(email, password)
        except auth.AuthError as exc:
            messagebox.showerror("Login Failed", str(exc))
            return
        except Exception as e:
            # Catch DB deletion crashes or system errors gracefully
            messagebox.showerror("System Error", f"An unexpected error occurred:\n{e}")
            return

        # Added Login Success Alert
        messagebox.showinfo("Login Successful", f"Welcome back, {logged_in_user['name']}!")
        self.app.on_login_success(logged_in_user)


class RegisterScreen:
    """Modern Card-based Registration Screen with Form Validation."""

    def __init__(self, parent, app: App):
        self.app = app

        card = tk.Frame(parent, bg="white", padx=50, pady=30, relief="flat")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Create an Account", font=("Helvetica", 18, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 20))

        def make_field(label_text, is_password=False):
            tk.Label(card, text=label_text, font=("Helvetica", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w")
            entry = tk.Entry(card, width=35, font=("Helvetica", 11), show="*" if is_password else "", bg="#f8f9fa", relief="flat")
            entry.pack(pady=(5, 12), ipady=6)
            return entry

        self.name_entry = make_field("Full Name")
        self.email_entry = make_field("Email Address")
        self.phone_entry = make_field("Phone Number")
        self.password_entry = make_field("Password", is_password=True)
        self.confirm_entry = make_field("Confirm Password", is_password=True)

        tk.Button(
            card, text="REGISTER", width=32, bg="#27ae60", fg="white", font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2", activebackground="#2ecc71", activeforeground="white",
            command=self.handle_register
        ).pack(pady=(15, 10), ipady=6)

        tk.Button(
            card, text="Back to Login", width=32, bg="#ecf0f1", fg="#2c3e50", font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2", activebackground="#bdc3c7",
            command=app.show_login_screen
        ).pack(ipady=6)

    def handle_register(self):
        # Empty field pre-validation for better UI feedback
        if not self.name_entry.get().strip() or not self.email_entry.get().strip() or not self.password_entry.get():
            messagebox.showerror("Registration Error", "Please fill out all required fields.")
            return
            
        try:
            auth.register_user(
                name=self.name_entry.get(),
                email=self.email_entry.get(),
                phone=self.phone_entry.get(),
                password=self.password_entry.get(),
                confirm_password=self.confirm_entry.get(),
                role="user",
            )
        except auth.AuthError as exc:
            messagebox.showerror("Registration Failed", str(exc))
            return
        except Exception as e:
            # Catch DB deletion crashes or system errors gracefully
            messagebox.showerror("System Error", f"An unexpected error occurred:\n{e}")
            return

        # Registration Success Alert
        messagebox.showinfo("Success", "Account created successfully!\nYou can now log in with your credentials.")
        self.app.show_login_screen()


def main():
    database.init_db()
    app = App()
    app.run()


if __name__ == "__main__":
    main()