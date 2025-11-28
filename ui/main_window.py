import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
from datetime import datetime

from core.supabase_client import SupabaseClient
from core.idle_detector import IdleDetector
from utils.shift_detector import ShiftDetector
from utils.path_parser import PathParser
from ui.tray_icon import TrayIcon

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SCHL TIME TRACKER")
        self.geometry("800x600")
        self.attributes('-topmost', True)
        
        self.supabase = SupabaseClient()
        self.shift_detector = ShiftDetector()
        self.path_parser = PathParser()
        self.idle_detector = None
        
        self.files = []
        self.active_file_index = None
        self.is_minimized = False
        self.client_colors = {}
        self.color_palette = ["#FFFFFF", "#FFB6C1", "#87CEEB", "#98FB98", "#FFD700", "#DDA0DD", "#FFA07A", "#20B2AA"]
        self.color_index = 0
        self.completing_file = False
        self.logged_in_user = None
        self.current_file_pause_count = 0
        self.current_file_idle_time = 0
        
        self.withdraw()
        self.show_login()
    
    def show_login(self):
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow(self, self.supabase, self.on_login_success)
    
    def on_login_success(self, user_data):
        self.logged_in_user = user_data
        self.deiconify()
        self.create_startup_screen()
        self.tray_icon = TrayIcon(self)
        
        self.sync_offline_data()
        
        self.bind('<Alt-Shift-D>', self.complete_current_file)
        self.bind('<Alt-Shift-S>', self.start_next_available_file)
        self.bind('<Alt-Shift-P>', self.toggle_current_pause)
    
    def sync_offline_data(self):
        count = self.supabase.sync_offline_queue()
        if count > 0:
            messagebox.showinfo("Sync Complete", f"Synced {count} offline entries to database")
        
        pending = self.supabase.get_offline_queue_count()
        if pending > 0:
            print(f"{pending} entries still pending sync")
    
    def create_startup_screen(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(self.main_frame, text="SCHL TIME TRACKER", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20)
        
        if self.logged_in_user:
            welcome_text = f"Welcome, {self.logged_in_user.get('username', 'User')}!"
            welcome_label = ctk.CTkLabel(self.main_frame, text=welcome_text,
                                        font=ctk.CTkFont(size=14))
            welcome_label.pack(pady=(0, 20))
        
        worktype_frame = ctk.CTkFrame(self.main_frame)
        worktype_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(worktype_frame, text="Work Type:").pack(side="left", padx=10)
        self.worktype_var = ctk.StringVar(value="Employee")
        self.worktype_combo = ctk.CTkComboBox(worktype_frame,
                                            values=["Employee", "Contractor", "Freelancer"],
                                            variable=self.worktype_var)
        self.worktype_combo.pack(side="left", padx=10, fill="x", expand=True)
        
        shift_frame = ctk.CTkFrame(self.main_frame)
        shift_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(shift_frame, text="Shift:").pack(side="left", padx=10)
        self.shift_var = ctk.StringVar(value=self.shift_detector.get_current_shift())
        self.shift_label = ctk.CTkLabel(shift_frame, textvariable=self.shift_var)
        self.shift_label.pack(side="left", padx=10)
        
        shortcut_frame = ctk.CTkFrame(self.main_frame)
        shortcut_frame.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(shortcut_frame, text="Keyboard Shortcuts:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(shortcut_frame, text="Alt+Shift+S = Start next file").pack(anchor="w", padx=20)
        ctk.CTkLabel(shortcut_frame, text="Alt+Shift+P = Pause/Resume").pack(anchor="w", padx=20)
        ctk.CTkLabel(shortcut_frame, text="Alt+Shift+D = Complete file").pack(anchor="w", padx=20)
        
        self.start_btn = ctk.CTkButton(self.main_frame, text="START WORK", 
                                      command=self.start_work,
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.start_btn.pack(pady=30)
    
    def start_work(self):
        self.main_frame.destroy()
        self.create_work_interface()
        
        self.idle_detector = IdleDetector(idle_threshold=60, callback=self.on_idle_change)
        self.idle_detector.start()
    
    def on_idle_change(self, status):
        if status == 'idle_start':
            if self.active_file_index is not None:
                active_file = self.files[self.active_file_index]
                if active_file['is_active'] and not active_file['is_paused']:
                    self.after(0, lambda: self.auto_pause_for_idle(active_file))
    
    def auto_pause_for_idle(self, file_data):
        if file_data['is_active'] and not file_data['is_paused']:
            self.pause_file(file_data)
            print("Auto-paused due to idle")
    
    def get_employee_name(self):
        if self.logged_in_user:
            return self.logged_in_user.get('username', 'Unknown')
        return 'Unknown'
        
    def get_client_color(self, client_name):
        if client_name not in self.client_colors:
            self.client_colors[client_name] = self.color_palette[self.color_index % len(self.color_palette)]
            self.color_index += 1
        return self.client_colors[client_name]
        
    def create_work_interface(self):
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=10)
        
        info_text = f"{self.get_employee_name()} | {self.worktype_var.get()} | {self.shift_var.get()}"
        info_label = ctk.CTkLabel(header_frame, text=info_text, font=ctk.CTkFont(size=14))
        info_label.pack(side="left", padx=10)
        
        status_frame = ctk.CTkFrame(header_frame)
        status_frame.pack(side="left", padx=20)
        
        self.connection_label = ctk.CTkLabel(status_frame, text="● Online", 
                                            font=ctk.CTkFont(size=10),
                                            text_color="#4CAF50")
        self.connection_label.pack(side="left")
        
        self.offline_count_label = ctk.CTkLabel(status_frame, text="", 
                                               font=ctk.CTkFont(size=10))
        self.offline_count_label.pack(side="left", padx=5)
        
        control_frame = ctk.CTkFrame(header_frame)
        control_frame.pack(side="right", padx=10)
        
        self.add_files_btn = ctk.CTkButton(control_frame, text="+ ADD FILES",
                                          command=self.add_files)
        self.add_files_btn.pack(side="left", padx=5)
        
        self.clean_all_btn = ctk.CTkButton(control_frame, text="CLEAN ALL",
                                          command=self.clean_all_files,
                                          fg_color="#DC143C",
                                          hover_color="#B22222")
        self.clean_all_btn.pack(side="left", padx=5)
        
        self.minimize_btn = ctk.CTkButton(control_frame, text="MINIMIZE",
                                         command=self.minimize_panel)
        self.minimize_btn.pack(side="left", padx=5)
        
        self.files_frame = ctk.CTkFrame(self.main_container)
        self.files_frame.pack(fill="both", expand=True, pady=10)
        
        files_header = ctk.CTkFrame(self.files_frame)
        files_header.pack(fill="x", padx=10, pady=5)
        
        self.total_files_label = ctk.CTkLabel(files_header, text="Files: 0", font=ctk.CTkFont(weight="bold"))
        self.total_files_label.pack(side="left")
        
        self.open_next_btn = ctk.CTkButton(files_header, text="OPEN NEXT", 
                                          command=self.open_next_file,
                                          state="disabled")
        self.open_next_btn.pack(side="right", padx=5)
        
        self.files_container = ctk.CTkScrollableFrame(self.files_frame)
        self.files_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.show_no_files_message()
        
        self.update_connection_status()
    
    def update_connection_status(self):
        if self.supabase.check_connection():
            self.connection_label.configure(text="● Online", text_color="#4CAF50")
            self.sync_offline_data()
        else:
            self.connection_label.configure(text="● Offline", text_color="#FF6B6B")
        
        pending = self.supabase.get_offline_queue_count()
        if pending > 0:
            self.offline_count_label.configure(text=f"({pending} pending)")
        else:
            self.offline_count_label.configure(text="")
        
        self.after(30000, self.update_connection_status)
    
    def show_no_files_message(self):
        for widget in self.files_container.winfo_children():
            widget.destroy()
        
        message_label = ctk.CTkLabel(self.files_container, 
                                   text="No files added yet. Click '+ ADD FILES' to start tracking.",
                                   font=ctk.CTkFont(size=14))
        message_label.pack(pady=50)
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=[("All files", "*.*"), ("Photoshop files", "*.psd"), ("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.webp")]
        )
        
        if files:
            for file_path in files:
                self.add_single_file(file_path)
            
            self.open_next_btn.configure(state="normal")
            self.update_display()
    
    def add_single_file(self, file_path):
        client_name = self.path_parser.extract_client_from_path(file_path)
        filename = os.path.basename(file_path)
        short_filename = filename[:25] + "..." if len(filename) > 25 else filename
        
        file_data = {
            'path': file_path,
            'filename': filename,
            'short_filename': short_filename,
            'client': client_name,
            'display_text': f"{client_name} - {short_filename}",
            'is_active': False,
            'is_paused': False,
            'is_opened': False,
            'elapsed_time': 0,
            'timer_id': None,
            'start_time': None,
            'completed': False,
            'pause_count': 0,
            'idle_time': 0
        }
        
        self.files.append(file_data)
    
    def clean_all_files(self):
        result = messagebox.askyesno("Confirm", "Are you sure you want to remove all files?")
        if result:
            for file_data in self.files:
                if file_data['timer_id']:
                    self.after_cancel(file_data['timer_id'])
            
            self.files = []
            self.active_file_index = None
            self.client_colors = {}
            self.color_index = 0
            
            self.open_next_btn.configure(state="disabled")
            self.update_display()
            
            if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
                self.tray_icon.close_minimized_panel()
    
    def remove_single_file(self, file_data):
        if file_data['timer_id']:
            self.after_cancel(file_data['timer_id'])
        
        idx = self.files.index(file_data)
        self.files.remove(file_data)
        
        if self.active_file_index is not None:
            if self.active_file_index == idx:
                self.active_file_index = None
            elif self.active_file_index > idx:
                self.active_file_index -= 1
        
        self.update_display()
        
        if not self.files:
            self.open_next_btn.configure(state="disabled")
    
    def update_display(self):
        for widget in self.files_container.winfo_children():
            widget.destroy()
        
        if not self.files:
            self.show_no_files_message()
            return
        
        active_files = [f for f in self.files if not f['completed']]
        self.total_files_label.configure(text=f"Files: {len(active_files)}")
        
        for i, file_data in enumerate(self.files):
            if file_data['completed']:
                continue
                
            self.create_file_row(file_data, i)
    
    def create_file_row(self, file_data, index):
        file_frame = ctk.CTkFrame(self.files_container)
        file_frame.pack(fill="x", pady=2, padx=5)
        
        client_color = self.get_client_color(file_data['client'])
        
        order_label = ctk.CTkLabel(file_frame, text=f"{index+1}.", width=30)
        order_label.pack(side="left", padx=5)
        
        name_label = ctk.CTkLabel(file_frame, text=file_data['display_text'], 
                                 anchor="w", width=250, text_color=client_color)
        name_label.pack(side="left", padx=10, fill="x", expand=True)
        
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(side="right", padx=5)
        
        if file_data['is_active']:
            if file_data['is_paused']:
                name_label.configure(text=f"⏸ {file_data['display_text']}", text_color="#FFA500")
            else:
                name_label.configure(text=f"● {file_data['display_text']}", text_color="#2E8B57")
            
            timer_label = ctk.CTkLabel(btn_frame, text="00:00", width=60)
            timer_label.pack(side="left", padx=2)
            file_data['timer_label'] = timer_label
            
            elapsed = file_data['elapsed_time']
            if not file_data['is_paused'] and file_data['start_time']:
                elapsed += (datetime.now() - file_data['start_time']).total_seconds()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            
            pause_text = "RESUME" if file_data['is_paused'] else "PAUSE"
            pause_btn = ctk.CTkButton(btn_frame, text=pause_text, width=70,
                                     command=lambda f=file_data: self.pause_file(f))
            pause_btn.pack(side="left", padx=2)
            file_data['pause_btn'] = pause_btn
            
            done_btn = ctk.CTkButton(btn_frame, text="DONE", width=70,
                                    command=lambda f=file_data: self.complete_file(f))
            done_btn.pack(side="left", padx=2)
            file_data['done_btn'] = done_btn
            
            remove_btn = ctk.CTkButton(btn_frame, text="✕", width=30,
                                      command=lambda f=file_data: self.remove_single_file(f),
                                      fg_color="#DC143C",
                                      hover_color="#B22222")
            remove_btn.pack(side="left", padx=2)
            
            if not file_data['is_paused']:
                self.update_timer(file_data)
                
        else:
            status_text = "✓ Opened" if file_data['is_opened'] else "Not opened"
            status_color = "#4CAF50" if file_data['is_opened'] else "#888888"
            status_label = ctk.CTkLabel(btn_frame, text=status_text, width=70, 
                                       text_color=status_color, font=ctk.CTkFont(size=11))
            status_label.pack(side="left", padx=2)
            
            start_btn = ctk.CTkButton(btn_frame, text="START", width=70,
                                     command=lambda f=file_data: self.start_file(f),
                                     state="normal" if file_data['is_opened'] else "disabled")
            start_btn.pack(side="left", padx=2)
            file_data['start_btn'] = start_btn
            
            remove_btn = ctk.CTkButton(btn_frame, text="✕", width=30,
                                      command=lambda f=file_data: self.remove_single_file(f),
                                      fg_color="#DC143C",
                                      hover_color="#B22222")
            remove_btn.pack(side="left", padx=2)
        
        file_data['frame'] = file_frame
        file_data['name_label'] = name_label
    
    def open_next_file(self):
        for file_data in self.files:
            if not file_data['completed'] and not file_data['is_opened']:
                self.open_file(file_data)
                return
        
        messagebox.showinfo("Info", "All files are already opened")
    
    def open_file(self, file_data):
        try:
            photoshop_paths = [
                "photoshop.exe",
                "C:/Program Files/Adobe/Adobe Photoshop 2024/Photoshop.exe",
                "C:/Program Files/Adobe/Adobe Photoshop 2023/Photoshop.exe", 
                "C:/Program Files/Adobe/Adobe Photoshop 2022/Photoshop.exe",
                "C:/Program Files/Adobe/Adobe Photoshop 2021/Photoshop.exe",
                "C:/Program Files/Adobe/Adobe Photoshop 2020/Photoshop.exe",
            ]
            
            opened = False
            for ps_path in photoshop_paths:
                try:
                    subprocess.Popen([ps_path, file_data['path']])
                    opened = True
                    break
                except:
                    continue
            
            if not opened:
                if os.name == 'nt':
                    os.startfile(file_data['path'])
                else:
                    subprocess.Popen(['xdg-open', file_data['path']])
            
            file_data['is_opened'] = True
            self.update_display()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def start_next_available_file(self, event=None):
        for file_data in self.files:
            if not file_data['completed'] and file_data['is_opened'] and not file_data['is_active']:
                self.start_file(file_data)
                return
        
        for file_data in self.files:
            if not file_data['completed'] and not file_data['is_opened']:
                self.open_file(file_data)
                self.start_file(file_data)
                return
    
    def toggle_current_pause(self, event=None):
        if self.active_file_index is not None:
            active_file = self.files[self.active_file_index]
            if active_file['is_active']:
                self.pause_file(active_file)
    
    def start_file(self, file_data):
        for other_file in self.files:
            if other_file['is_active'] and other_file != file_data:
                if not other_file['is_paused'] and other_file['start_time']:
                    other_file['elapsed_time'] += (datetime.now() - other_file['start_time']).total_seconds()
                
                if other_file['timer_id']:
                    self.after_cancel(other_file['timer_id'])
                    other_file['timer_id'] = None
                
                other_file['is_paused'] = True
                other_file['start_time'] = None
        
        file_data['is_active'] = True
        file_data['is_paused'] = False
        file_data['start_time'] = datetime.now()
        self.active_file_index = self.files.index(file_data)
        
        if self.idle_detector:
            self.idle_detector.reset()
        
        self.update_display()
        
        if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
            self.tray_icon.update_minimized_panel(self.get_active_file_info())
    
    def pause_file(self, file_data):
        if file_data['is_active']:
            if file_data['is_paused']:
                file_data['is_paused'] = False
                file_data['start_time'] = datetime.now()
                if 'pause_btn' in file_data:
                    file_data['pause_btn'].configure(text="PAUSE")
                if 'name_label' in file_data:
                    file_data['name_label'].configure(text=f"● {file_data['display_text']}", text_color="#2E8B57")
                self.update_timer(file_data)
            else:
                if file_data['start_time']:
                    file_data['elapsed_time'] += (datetime.now() - file_data['start_time']).total_seconds()
                
                file_data['is_paused'] = True
                file_data['start_time'] = None
                file_data['pause_count'] += 1
                
                if file_data['timer_id']:
                    self.after_cancel(file_data['timer_id'])
                    file_data['timer_id'] = None
                
                if 'pause_btn' in file_data:
                    file_data['pause_btn'].configure(text="RESUME")
                if 'name_label' in file_data:
                    file_data['name_label'].configure(text=f"⏸ {file_data['display_text']}", text_color="#FFA500")
            
            if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
                self.tray_icon.update_minimized_panel(self.get_active_file_info())
    
    def update_timer(self, file_data):
        if file_data['is_active'] and not file_data['is_paused']:
            elapsed = (datetime.now() - file_data['start_time']).total_seconds() + file_data['elapsed_time']
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            if 'timer_label' in file_data:
                file_data['timer_label'].configure(text=f"{minutes:02d}:{seconds:02d}")
            
            file_data['timer_id'] = self.after(1000, lambda: self.update_timer(file_data))
            
            if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
                self.tray_icon.update_timer_display(f"{minutes:02d}:{seconds:02d}")
    
    def complete_current_file(self, event=None):
        if self.completing_file:
            return
        
        if self.active_file_index is not None:
            active_file = self.files[self.active_file_index]
            if active_file['is_active']:
                self.completing_file = True
                self.complete_file(active_file)
                self.after(100, lambda: setattr(self, 'completing_file', False))
    
    def check_file_modification(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False
            
            current_time = datetime.now().timestamp()
            directory = os.path.dirname(file_path)
            filename_with_ext = os.path.basename(file_path)
            filename_without_ext = os.path.splitext(filename_with_ext)[0]
            
            files_to_check = [file_path]
            
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    file_base_name = os.path.splitext(file)[0]
                    if file_base_name == filename_without_ext:
                        full_path = os.path.join(directory, file)
                        if full_path not in files_to_check and os.path.isfile(full_path):
                            files_to_check.append(full_path)
            
            for check_file in files_to_check:
                try:
                    if os.path.exists(check_file):
                        file_modified_time = os.path.getmtime(check_file)
                        time_diff = current_time - file_modified_time
                        if time_diff <= 60:
                            return True
                except (OSError, PermissionError):
                    continue
            
            return False
                    
        except Exception as e:
            print(f"Error checking file modification: {e}")
            return True
    
    def complete_file(self, file_data):
        if file_data['completed']:
            return
        
        file_path = file_data['path']
        if not self.check_file_modification(file_path):
            result = messagebox.askyesno(
                "File Not Modified", 
                f"Warning: File has not been modified in the last 1 minute!\n\n"
                f"File: {file_data['filename']}\n\n"
                f"Did you save your work?\n\n"
                f"Click 'Yes' to complete anyway\n"
                f"Click 'No' to go back and save",
                icon='warning'
            )
            
            if not result:
                return
        
        total_time = file_data['elapsed_time']
        if file_data['is_active'] and not file_data['is_paused'] and file_data['start_time']:
            total_time += (datetime.now() - file_data['start_time']).total_seconds()
        
        if file_data['timer_id']:
            self.after_cancel(file_data['timer_id'])
        
        idle_time = 0
        if self.idle_detector:
            idle_time = self.idle_detector.get_total_idle_time()
            self.idle_detector.reset()
        
        file_data['idle_time'] = idle_time
        
        self.save_to_supabase(file_data, total_time)
        
        file_data['completed'] = True
        file_data['is_active'] = False
        
        if 'frame' in file_data:
            file_data['frame'].destroy()
        
        self.auto_start_next_file(file_data)
        
        self.update_display()
        
        if self.is_minimized:
            active_info = self.get_active_file_info()
            if active_info:
                self.tray_icon.update_minimized_panel(active_info)
            else:
                self.tray_icon.show_all_files_done()
    
    def auto_start_next_file(self, completed_file):
        current_index = self.files.index(completed_file)
        
        for i in range(current_index + 1, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_opened'] and not file_data['is_active']:
                self.open_file_in_photoshop_and_start(file_data)
                return
        
        for i in range(current_index + 1, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_active'] and file_data['is_paused']:
                self.start_file(file_data)
                return
        
        for i in range(0, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_active'] and file_data['is_paused']:
                self.start_file(file_data)
                return
        
        for i in range(0, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and not file_data['is_active']:
                if not file_data['is_opened']:
                    self.open_file(file_data)
                self.start_file(file_data)
                return
    
    def open_file_in_photoshop_and_start(self, file_data):
        self.open_file(file_data)
        self.start_file(file_data)
    
    def save_to_supabase(self, file_data, total_time):
        try:
            data = {
                'employee_name': self.get_employee_name(),
                'work_type': self.worktype_var.get(),
                'shift': self.shift_var.get(),
                'client_name': file_data['client'],
                'filename': file_data['filename'],
                'file_path': os.path.dirname(file_data['path']),
                'time_spent_seconds': int(total_time),
                'completed_at': datetime.now().isoformat(),
                'pause_count': file_data.get('pause_count', 0),
                'total_idle_seconds': file_data.get('idle_time', 0)
            }
            
            self.supabase.insert_time_entry(data)
            
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
    
    def minimize_panel(self):
        active_info = self.get_active_file_info()
        if active_info:
            self.is_minimized = True
            self.tray_icon.show_minimized_panel(active_info, self)
            self.withdraw()
        else:
            messagebox.showinfo("Info", "No active file to minimize")
    
    def get_active_file_info(self):
        if self.active_file_index is not None:
            file_data = self.files[self.active_file_index]
            if file_data['is_active']:
                elapsed = file_data['elapsed_time']
                if not file_data['is_paused'] and file_data['start_time']:
                    elapsed += (datetime.now() - file_data['start_time']).total_seconds()
                
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                
                return {
                    'filename': file_data['display_text'],
                    'timer_text': f"{minutes:02d}:{seconds:02d}",
                    'is_paused': file_data['is_paused']
                }
        return None
    
    def on_closing(self):
        if self.idle_detector:
            self.idle_detector.stop()
        self.destroy()
