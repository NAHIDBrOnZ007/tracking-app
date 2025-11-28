import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
from datetime import datetime

from core.supabase_client import SupabaseClient
from utils.shift_detector import ShiftDetector
from utils.path_parser import PathParser
from ui.tray_icon import TrayIcon

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SCHL TIME TRACKER")
        self.geometry("800x600")
        self.attributes('-topmost', True)
        
        # Initialize components
        self.supabase = SupabaseClient()
        self.shift_detector = ShiftDetector()
        self.path_parser = PathParser()
        
        # Tracking variables
        self.files = []
        self.active_file_index = None
        self.is_minimized = False
        self.client_colors = {}
        self.color_palette = ["#FFFFFF", "#FFB6C1", "#87CEEB", "#98FB98", "#FFD700", "#DDA0DD", "#FFA07A", "#20B2AA"]
        self.color_index = 0
        self.completing_file = False  # Flag to prevent double completion
        
        # Create UI
        self.create_startup_screen()
        self.tray_icon = TrayIcon(self)
        self.bind('<Control-Shift-D>', self.complete_current_file)
        
    def create_startup_screen(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(self.main_frame, text="SCHL TIME TRACKER", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20)
        
        # Employee selection
        employee_frame = ctk.CTkFrame(self.main_frame)
        employee_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(employee_frame, text="Employee:").pack(side="left", padx=10)
        self.employee_var = ctk.StringVar(value="John Doe")
        self.employee_combo = ctk.CTkComboBox(employee_frame, 
                                            values=["John Doe", "Jane Smith", "Mike Johnson"],
                                            variable=self.employee_var)
        self.employee_combo.pack(side="left", padx=10, fill="x", expand=True)
        
        # Work type selection
        worktype_frame = ctk.CTkFrame(self.main_frame)
        worktype_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(worktype_frame, text="Work Type:").pack(side="left", padx=10)
        self.worktype_var = ctk.StringVar(value="Employee")
        self.worktype_combo = ctk.CTkComboBox(worktype_frame,
                                            values=["Employee", "Contractor", "Freelancer"],
                                            variable=self.worktype_var)
        self.worktype_combo.pack(side="left", padx=10, fill="x", expand=True)
        
        # Shift detection
        shift_frame = ctk.CTkFrame(self.main_frame)
        shift_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(shift_frame, text="Shift:").pack(side="left", padx=10)
        self.shift_var = ctk.StringVar(value=self.shift_detector.get_current_shift())
        self.shift_label = ctk.CTkLabel(shift_frame, textvariable=self.shift_var)
        self.shift_label.pack(side="left", padx=10)
        
        # Start button
        self.start_btn = ctk.CTkButton(self.main_frame, text="START WORK", 
                                      command=self.start_work,
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.start_btn.pack(pady=30)
        
    def start_work(self):
        self.main_frame.destroy()
        self.create_work_interface()
        
    def get_client_color(self, client_name):
        if client_name not in self.client_colors:
            self.client_colors[client_name] = self.color_palette[self.color_index % len(self.color_palette)]
            self.color_index += 1
        return self.client_colors[client_name]
        
    def create_work_interface(self):
        # Main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=10)
        
        # Employee info
        info_text = f"{self.employee_var.get()} | {self.worktype_var.get()} | {self.shift_var.get()}"
        info_label = ctk.CTkLabel(header_frame, text=info_text, font=ctk.CTkFont(size=14))
        info_label.pack(side="left", padx=10)
        
        # Control buttons
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
        
        # Files section
        self.files_frame = ctk.CTkFrame(self.main_container)
        self.files_frame.pack(fill="both", expand=True, pady=10)
        
        # Files header
        files_header = ctk.CTkFrame(self.files_frame)
        files_header.pack(fill="x", padx=10, pady=5)
        
        self.total_files_label = ctk.CTkLabel(files_header, text="Files: 0", font=ctk.CTkFont(weight="bold"))
        self.total_files_label.pack(side="left")
        
        self.open_all_btn = ctk.CTkButton(files_header, text="OPEN ALL", 
                                         command=self.open_all_files,
                                         state="disabled")
        self.open_all_btn.pack(side="right", padx=5)
        
        # Files list container
        self.files_container = ctk.CTkScrollableFrame(self.files_frame)
        self.files_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Show initial message
        self.show_no_files_message()
    
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
            
            self.open_all_btn.configure(state="normal")
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
            'completed': False
        }
        
        self.files.append(file_data)
    
    def clean_all_files(self):
        result = messagebox.askyesno("Confirm", "Are you sure you want to remove all files?")
        if result:
            # Stop all timers
            for file_data in self.files:
                if file_data['timer_id']:
                    self.after_cancel(file_data['timer_id'])
            
            # Clear files
            self.files = []
            self.active_file_index = None
            self.client_colors = {}
            self.color_index = 0
            
            # Update UI
            self.open_all_btn.configure(state="disabled")
            self.update_display()
            
            # Close minimized panel if open
            if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
                self.tray_icon.close_minimized_panel()
    
    def remove_single_file(self, file_data):
        # Stop timer if active
        if file_data['timer_id']:
            self.after_cancel(file_data['timer_id'])
        
        # Remove from list
        self.files.remove(file_data)
        
        # Update active index
        if self.active_file_index is not None and file_data == self.files[self.active_file_index]:
            self.active_file_index = None
        
        # Update display
        self.update_display()
        
        # Check if no files left
        if not self.files:
            self.open_all_btn.configure(state="disabled")
    
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
        
        # Get client color
        client_color = self.get_client_color(file_data['client'])
        
        # File name
        name_label = ctk.CTkLabel(file_frame, text=file_data['display_text'], 
                                 anchor="w", width=250, text_color=client_color)
        name_label.pack(side="left", padx=10, fill="x", expand=True)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(side="right", padx=5)
        
        if file_data['is_active']:
            # Active file - show timer controls
            if file_data['is_paused']:
                name_label.configure(text=f"⏸ {file_data['display_text']}", text_color="#FFA500")
            else:
                name_label.configure(text=f"● {file_data['display_text']}", text_color="#2E8B57")
            
            # Timer label
            timer_label = ctk.CTkLabel(btn_frame, text="00:00", width=60)
            timer_label.pack(side="left", padx=2)
            file_data['timer_label'] = timer_label
            
            # Update timer display with current elapsed time
            elapsed = file_data['elapsed_time']
            if not file_data['is_paused'] and file_data['start_time']:
                elapsed += (datetime.now() - file_data['start_time']).total_seconds()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            
            # Pause button
            pause_text = "RESUME" if file_data['is_paused'] else "PAUSE"
            pause_btn = ctk.CTkButton(btn_frame, text=pause_text, width=70,
                                     command=lambda: self.pause_file(file_data))
            pause_btn.pack(side="left", padx=2)
            file_data['pause_btn'] = pause_btn
            
            # Done button
            done_btn = ctk.CTkButton(btn_frame, text="DONE", width=70,
                                    command=lambda: self.complete_file(file_data))
            done_btn.pack(side="left", padx=2)
            file_data['done_btn'] = done_btn
            
            # Remove button
            remove_btn = ctk.CTkButton(btn_frame, text="✕", width=30,
                                      command=lambda: self.remove_single_file(file_data),
                                      fg_color="#DC143C",
                                      hover_color="#B22222")
            remove_btn.pack(side="left", padx=2)
            
            # Start timer if active and not paused
            if not file_data['is_paused']:
                self.update_timer(file_data)
                
        else:
            # Inactive file - show open/start buttons
            open_btn = ctk.CTkButton(btn_frame, text="OPEN", width=70,
                                    command=lambda: self.open_file(file_data))
            open_btn.pack(side="left", padx=2)
            file_data['open_btn'] = open_btn
            
            start_btn = ctk.CTkButton(btn_frame, text="START", width=70,
                                     command=lambda: self.start_file(file_data),
                                     state="normal" if file_data['is_opened'] else "disabled")
            start_btn.pack(side="left", padx=2)
            file_data['start_btn'] = start_btn
            
            # Remove button
            remove_btn = ctk.CTkButton(btn_frame, text="✕", width=30,
                                      command=lambda: self.remove_single_file(file_data),
                                      fg_color="#DC143C",
                                      hover_color="#B22222")
            remove_btn.pack(side="left", padx=2)
        
        file_data['frame'] = file_frame
        file_data['name_label'] = name_label
    
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
                os.startfile(file_data['path'])
            
            file_data['is_opened'] = True
            if 'start_btn' in file_data:
                file_data['start_btn'].configure(state="normal")
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def open_all_files(self):
        for file_data in self.files:
            if not file_data['completed']:
                self.open_file(file_data)
    
    def start_file(self, file_data):
        # Save elapsed time for all currently active files before switching
        for other_file in self.files:
            if other_file['is_active'] and other_file != file_data:
                # Save current elapsed time
                if not other_file['is_paused'] and other_file['start_time']:
                    other_file['elapsed_time'] += (datetime.now() - other_file['start_time']).total_seconds()
                
                # Cancel timer
                if other_file['timer_id']:
                    self.after_cancel(other_file['timer_id'])
                    other_file['timer_id'] = None
                
                # Mark as paused but keep active status
                other_file['is_paused'] = True
                other_file['start_time'] = None
        
        # Start the new file
        file_data['is_active'] = True
        file_data['is_paused'] = False
        file_data['start_time'] = datetime.now()
        self.active_file_index = self.files.index(file_data)
        
        self.update_display()
        
        # Update minimized panel if open
        if self.is_minimized and hasattr(self.tray_icon, 'minimized_panel'):
            self.tray_icon.update_minimized_panel(self.get_active_file_info())
    
    def pause_file(self, file_data):
        if file_data['is_active']:
            if file_data['is_paused']:
                # Resume
                file_data['is_paused'] = False
                file_data['start_time'] = datetime.now()
                if 'pause_btn' in file_data:
                    file_data['pause_btn'].configure(text="PAUSE")
                if 'name_label' in file_data:
                    file_data['name_label'].configure(text=f"● {file_data['display_text']}", text_color="#2E8B57")
                self.update_timer(file_data)
            else:
                # Pause - save elapsed time
                if file_data['start_time']:
                    file_data['elapsed_time'] += (datetime.now() - file_data['start_time']).total_seconds()
                
                file_data['is_paused'] = True
                file_data['start_time'] = None
                
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
        # Prevent double execution
        if self.completing_file:
            return
        
        if self.active_file_index is not None:
            active_file = self.files[self.active_file_index]
            if active_file['is_active']:
                self.completing_file = True
                self.complete_file(active_file)
                # Reset flag after a short delay
                self.after(100, lambda: setattr(self, 'completing_file', False))
    
    def check_file_modification(self, file_path):
        """
        Check if file or related files (different formats) were modified within last 1 minute (60 seconds)
        Also checks for common backup files and auto-save files
        Returns: True if modified recently, False if not
        """
        try:
            # If file doesn't exist, return False (file was likely moved/deleted)
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            # Get current time
            current_time = datetime.now().timestamp()
            
            # Get directory and base filename without extension
            directory = os.path.dirname(file_path)
            filename_with_ext = os.path.basename(file_path)
            filename_without_ext = os.path.splitext(filename_with_ext)[0]
            file_extension = os.path.splitext(filename_with_ext)[1].lower()
            
            # Files to check for modifications
            files_to_check = []
            
            # Add original file
            files_to_check.append(file_path)
            
            # Common backup file patterns to check
            backup_patterns = [
                f"{filename_without_ext}~",  # Unix backup
                f"{filename_without_ext}.bak",
                f"{filename_without_ext}.tmp",
                f"~{filename_without_ext}.*",  # Temporary files
                f"_{filename_without_ext}.*",  # Some apps use underscore
            ]
            
            # Photoshop-specific files to check
            photoshop_files = [
                f"{filename_without_ext}.psb",  # Large document format
            ]
            
            # Auto-save directories (common in Adobe apps)
            auto_save_dirs = [
                os.path.join(directory, "AutoSave"),
                os.path.join(directory, "autosave"),
                os.path.join(directory, "Adobe Auto-Recover"),
                os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"),
                os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Adobe", "AutoRecover"),
            ]
            
            # Check for files with same base name but different extensions
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    file_base_name = os.path.splitext(file)[0]
                    
                    # Exact match (same base name)
                    if file_base_name == filename_without_ext:
                        full_path = os.path.join(directory, file)
                        if full_path not in files_to_check and os.path.isfile(full_path):
                            files_to_check.append(full_path)
                    
                    # Check for backup patterns
                    for pattern in backup_patterns:
                        if file.startswith(pattern.replace("*", "")):
                            full_path = os.path.join(directory, file)
                            if full_path not in files_to_check and os.path.isfile(full_path):
                                files_to_check.append(full_path)
            
            # Add Photoshop-specific files
            for ps_file in photoshop_files:
                ps_path = os.path.join(directory, ps_file)
                if os.path.exists(ps_path) and ps_path not in files_to_check:
                    files_to_check.append(ps_path)
            
            # Check auto-save directories
            for auto_save_dir in auto_save_dirs:
                if os.path.exists(auto_save_dir):
                    try:
                        for file in os.listdir(auto_save_dir):
                            # Look for files that might be auto-save versions
                            if filename_without_ext in file:
                                full_path = os.path.join(auto_save_dir, file)
                                if full_path not in files_to_check and os.path.isfile(full_path):
                                    files_to_check.append(full_path)
                    except (PermissionError, OSError):
                        continue  # Skip directories we can't access
            
            # Debug: print files being checked
            print(f"Checking {len(files_to_check)} related files for modifications:")
            for check_file in files_to_check:
                print(f"  - {os.path.basename(check_file)}")
            
            # Check modification time for all related files
            recently_modified = False
            for check_file in files_to_check:
                try:
                    if os.path.exists(check_file):
                        file_modified_time = os.path.getmtime(check_file)
                        time_diff = current_time - file_modified_time
                        
                        print(f"  {os.path.basename(check_file)}: modified {time_diff:.1f} seconds ago")
                        
                        # If ANY related file was modified in last 60 seconds, return True
                        if time_diff <= 60:
                            recently_modified = True
                            print(f"  → RECENTLY MODIFIED!")
                            break
                except (OSError, PermissionError) as e:
                    print(f"  Error checking {check_file}: {e}")
                    continue
            
            print(f"Final result: {'MODIFIED' if recently_modified else 'NOT MODIFIED'}")
            return recently_modified
                    
        except Exception as e:
            print(f"Error checking file modification: {e}")
            import traceback
            traceback.print_exc()
            return True  # If error, allow completion (don't block employee)
    
    def complete_file(self, file_data):
        # Additional check to prevent double completion
        if file_data['completed']:
            return
        
        # ✅ NEW: Check if file was modified recently
        file_path = file_data['path']
        if not self.check_file_modification(file_path):
            # File NOT modified in last 1 minute - Show warning
            result = messagebox.askyesno(
                "File Not Modified", 
                f"⚠️ WARNING: File has not been modified in the last 1 minute!\n\n"
                f"File: {file_data['filename']}\n\n"
                f"Did you save your work?\n\n"
                f"Click 'Yes' to complete anyway\n"
                f"Click 'No' to go back and save your work",
                icon='warning'
            )
            
            if not result:
                # Employee chose to go back
                return
        
        # Calculate total time
        total_time = file_data['elapsed_time']
        if file_data['is_active'] and not file_data['is_paused'] and file_data['start_time']:
            total_time += (datetime.now() - file_data['start_time']).total_seconds()
        
        # Stop timer
        if file_data['timer_id']:
            self.after_cancel(file_data['timer_id'])
        
        # Save to Supabase
        self.save_to_supabase(file_data, total_time)
        
        
        # Mark as completed
        file_data['completed'] = True
        file_data['is_active'] = False
        
        # Remove from UI
        if 'frame' in file_data:
            file_data['frame'].destroy()
        
        # Auto-start next file
        self.auto_start_next_file(file_data)
        
        # Update display
        self.update_display()
        
        # Update minimized panel
        if self.is_minimized:
            active_info = self.get_active_file_info()
            if active_info:
                self.tray_icon.update_minimized_panel(active_info)
            else:
                # All files done
                self.tray_icon.show_all_files_done()
    
    def auto_start_next_file(self, completed_file):
        """
        Auto-start logic with correct priority:
        1. Next opened file in sequence (7, 8, 9, 10)
        2. Next paused file in sequence
        3. Loop back - PAUSED files first (1, 2, 3...)
        4. Loop back - OPENED files last
        """
        current_index = self.files.index(completed_file)
        
        # Priority 1: Start next OPENED (but not started) file after current position
        for i in range(current_index + 1, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_opened'] and not file_data['is_active']:
                self.start_file(file_data)
                return
        
        # Priority 2: Resume next PAUSED file after current position
        for i in range(current_index + 1, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_active'] and file_data['is_paused']:
                self.start_file(file_data)
                return
        
        # Priority 3: Loop back - Resume PAUSED files from beginning (BEFORE opened files!)
        for i in range(0, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_active'] and file_data['is_paused']:
                self.start_file(file_data)
                return
        
        # Priority 4: Loop back - Start OPENED files from beginning (LAST resort)
        for i in range(0, len(self.files)):
            file_data = self.files[i]
            if not file_data['completed'] and file_data['is_opened'] and not file_data['is_active']:
                self.start_file(file_data)
                return
    
    def save_to_supabase(self, file_data, total_time):
        try:
            data = {
                'employee_name': self.employee_var.get(),
                'work_type': self.worktype_var.get(),
                'shift': self.shift_var.get(),
                'client_name': file_data['client'],
                'filename': file_data['filename'],
                'file_path': os.path.dirname(file_data['path']),  # ← STORES ONLY DIRECTORY
                'time_spent_seconds': int(total_time),
                'completed_at': datetime.now().isoformat()
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