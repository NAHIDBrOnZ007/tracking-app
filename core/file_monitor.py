from pynput import keyboard
import threading

class GlobalHotkeyManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.listener = None
    
    def start_listener(self):
        def on_activate():
            # Trigger complete current file in main thread
            self.main_window.after(0, self.main_window.complete_current_file)
        
        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))
        
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+d'),
            on_activate
        )
        
        with keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        ) as self.listener:
            self.listener.join()