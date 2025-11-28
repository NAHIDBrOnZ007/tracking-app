import customtkinter as ctk

class TrayIcon:
    def __init__(self, main_window):
        self.main_window = main_window
        self.minimized_panel = None
        self.timer_label = None
        self.file_label = None
        self.name_label = None
    
    def show_minimized_panel(self, active_file_info, main_window):
        self.main_window = main_window
        self.minimized_panel = ctk.CTkToplevel(self.main_window)
        self.minimized_panel.title("Time Tracker - Active")
        self.minimized_panel.geometry("350x120")
        self.minimized_panel.attributes('-topmost', True)
        self.minimized_panel.resizable(False, False)
        self.minimized_panel.protocol("WM_DELETE_WINDOW", self.restore_main_window)
        
        if active_file_info:
            filename = active_file_info['filename']
            timer_text = active_file_info['timer_text']
            is_paused = active_file_info['is_paused']
            
            top_frame = ctk.CTkFrame(self.minimized_panel)
            top_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            status_text = "⏸ PAUSED" if is_paused else "● ACTIVE"
            status_color = "#FFA500" if is_paused else "#2E8B57"
            self.file_label = ctk.CTkLabel(top_frame, text=status_text, 
                                          font=ctk.CTkFont(weight="bold", size=12),
                                          text_color=status_color)
            self.file_label.pack(side="left")
            
            self.timer_label = ctk.CTkLabel(top_frame, text=timer_text, 
                                           font=ctk.CTkFont(weight="bold", size=14))
            self.timer_label.pack(side="right")
            
            self.name_label = ctk.CTkLabel(self.minimized_panel, text=filename, 
                                          font=ctk.CTkFont(size=11),
                                          wraplength=330)
            self.name_label.pack(padx=10, pady=5)
            
            btn_frame = ctk.CTkFrame(self.minimized_panel)
            btn_frame.pack(pady=10)
            
            pause_text = "RESUME" if is_paused else "PAUSE"
            self.pause_btn = ctk.CTkButton(btn_frame, text=pause_text, width=80, height=30,
                                          command=self.toggle_pause)
            self.pause_btn.pack(side="left", padx=3)
            
            complete_btn = ctk.CTkButton(btn_frame, text="DONE", width=80, height=30,
                                        command=self.complete_current,
                                        fg_color="#2E8B57", hover_color="#236B4A")
            complete_btn.pack(side="left", padx=3)
            
            full_btn = ctk.CTkButton(btn_frame, text="EXPAND", width=80, height=30,
                                    command=self.restore_main_window)
            full_btn.pack(side="left", padx=3)
    
    def update_timer_display(self, timer_text):
        if self.timer_label:
            self.timer_label.configure(text=timer_text)
    
    def update_minimized_panel(self, active_file_info):
        if self.minimized_panel and active_file_info:
            if self.name_label:
                self.name_label.configure(text=active_file_info['filename'])
            
            if self.timer_label:
                self.timer_label.configure(text=active_file_info['timer_text'])
            
            pause_text = "RESUME" if active_file_info['is_paused'] else "PAUSE"
            if hasattr(self, 'pause_btn'):
                self.pause_btn.configure(text=pause_text)
            
            if self.file_label:
                if active_file_info['is_paused']:
                    self.file_label.configure(text="⏸ PAUSED", text_color="#FFA500")
                else:
                    self.file_label.configure(text="● ACTIVE", text_color="#2E8B57")
    
    def show_all_files_done(self):
        if self.minimized_panel:
            for widget in self.minimized_panel.winfo_children():
                widget.destroy()
            
            done_label = ctk.CTkLabel(self.minimized_panel, 
                                     text="✓ ALL DONE!", 
                                     font=ctk.CTkFont(weight="bold", size=18),
                                     text_color="#2E8B57")
            done_label.pack(pady=20)
            
            message_label = ctk.CTkLabel(self.minimized_panel, 
                                        text="Great job! All files completed.",
                                        font=ctk.CTkFont(size=12))
            message_label.pack(pady=5)
            
            restore_btn = ctk.CTkButton(self.minimized_panel, 
                                       text="RETURN TO MAIN", 
                                       width=150,
                                       command=self.restore_main_window)
            restore_btn.pack(pady=10)
    
    def close_minimized_panel(self):
        if self.minimized_panel:
            self.minimized_panel.destroy()
            self.minimized_panel = None
            self.main_window.is_minimized = False
    
    def toggle_pause(self):
        if hasattr(self.main_window, 'active_file_index') and self.main_window.active_file_index is not None:
            active_file = self.main_window.files[self.main_window.active_file_index]
            self.main_window.pause_file(active_file)
    
    def complete_current(self, event=None):
        if hasattr(self.main_window, 'complete_current_file'):
            self.main_window.complete_current_file()
    
    def restore_main_window(self):
        if self.minimized_panel:
            self.minimized_panel.destroy()
            self.minimized_panel = None
        self.main_window.is_minimized = False
        self.main_window.deiconify()
