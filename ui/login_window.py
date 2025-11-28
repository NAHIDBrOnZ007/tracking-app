import customtkinter as ctk
from tkinter import messagebox

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, supabase_client, on_login_success):
        super().__init__(parent)
        
        self.supabase = supabase_client
        self.on_login_success = on_login_success
        self.logged_in_user = None
        
        self.title("SCHL TIME TRACKER - Login")
        self.geometry("400x450")
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_ui()
        
        self.grab_set()
        self.focus_force()
    
    def create_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(main_frame, text="SCHL TIME TRACKER",
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 5))
        
        subtitle_label = ctk.CTkLabel(main_frame, text="Employee Login",
                                     font=ctk.CTkFont(size=14))
        subtitle_label.pack(pady=(0, 30))
        
        ctk.CTkLabel(main_frame, text="Username:", anchor="w").pack(fill="x", padx=30)
        self.username_entry = ctk.CTkEntry(main_frame, width=300, height=40)
        self.username_entry.pack(padx=30, pady=(5, 15))
        
        ctk.CTkLabel(main_frame, text="Password:", anchor="w").pack(fill="x", padx=30)
        self.password_entry = ctk.CTkEntry(main_frame, width=300, height=40, show="*")
        self.password_entry.pack(padx=30, pady=(5, 20))
        
        self.login_btn = ctk.CTkButton(main_frame, text="LOGIN", width=300, height=45,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      command=self.login)
        self.login_btn.pack(padx=30, pady=10)
        
        or_label = ctk.CTkLabel(main_frame, text="- OR -", font=ctk.CTkFont(size=12))
        or_label.pack(pady=10)
        
        self.register_btn = ctk.CTkButton(main_frame, text="REGISTER NEW ACCOUNT",
                                         width=300, height=40,
                                         fg_color="transparent",
                                         border_width=2,
                                         command=self.register)
        self.register_btn.pack(padx=30, pady=10)
        
        self.status_label = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=10)
        
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.status_label.configure(text="Please enter username and password", text_color="#FF6B6B")
            return
        
        self.login_btn.configure(state="disabled", text="Logging in...")
        self.update()
        
        success, user_data, message = self.supabase.login_user(username, password)
        
        if success:
            self.status_label.configure(text="Login successful!", text_color="#4CAF50")
            self.logged_in_user = user_data
            self.after(500, self.complete_login)
        else:
            self.status_label.configure(text=message, text_color="#FF6B6B")
            self.login_btn.configure(state="normal", text="LOGIN")
    
    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.status_label.configure(text="Please enter username and password to register", text_color="#FF6B6B")
            return
        
        if len(password) < 4:
            self.status_label.configure(text="Password must be at least 4 characters", text_color="#FF6B6B")
            return
        
        self.register_btn.configure(state="disabled", text="Registering...")
        self.update()
        
        success, message = self.supabase.register_user(username, password)
        
        if success:
            self.status_label.configure(text="Registration successful! You can now login.", text_color="#4CAF50")
        else:
            self.status_label.configure(text=message, text_color="#FF6B6B")
        
        self.register_btn.configure(state="normal", text="REGISTER NEW ACCOUNT")
    
    def complete_login(self):
        self.grab_release()
        self.on_login_success(self.logged_in_user)
        self.destroy()
    
    def on_close(self):
        self.grab_release()
        self.master.destroy()
