import customtkinter as ctk
from ui.main_window import MainWindow
from core.file_monitor import GlobalHotkeyManager
import threading

def main():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = MainWindow()
    
    hotkey_manager = GlobalHotkeyManager(app)
    hotkey_thread = threading.Thread(target=hotkey_manager.start_listener, daemon=True)
    hotkey_thread.start()
    
    def on_closing():
        hotkey_manager.stop()
        app.on_closing()
    
    app.protocol("WM_DELETE_WINDOW", on_closing)
    
    app.mainloop()

if __name__ == "__main__":
    main()
