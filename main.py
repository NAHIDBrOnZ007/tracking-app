import customtkinter as ctk
from ui.main_window import MainWindow
from core.file_monitor import GlobalHotkeyManager
import threading

def main():
    # Set appearance
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Create main application
    app = MainWindow()
    
    # Start global hotkey listener in separate thread
    hotkey_manager = GlobalHotkeyManager(app)
    hotkey_thread = threading.Thread(target=hotkey_manager.start_listener, daemon=True)
    hotkey_thread.start()
    
    # Start the application
    app.mainloop()

if __name__ == "__main__":
    main()