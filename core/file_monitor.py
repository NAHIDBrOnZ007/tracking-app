import threading
import time

class GlobalHotkeyManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.listener = None
        self.running = False
        self.alt_pressed = False
        self.shift_pressed = False
        self.last_action_time = 0
    
    def start_listener(self):
        self.running = True
        
        try:
            from pynput import keyboard
            
            def on_press(key):
                if not self.running:
                    return False
                
                try:
                    if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                        self.alt_pressed = True
                    elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                        self.shift_pressed = True
                    elif hasattr(key, 'char') and key.char:
                        char = key.char.lower()
                        current_time = time.time()
                        
                        if self.alt_pressed and self.shift_pressed and (current_time - self.last_action_time) > 0.5:
                            if char == 'd':
                                self.last_action_time = current_time
                                self.main_window.after(0, self.main_window.complete_current_file)
                            elif char == 's':
                                self.last_action_time = current_time
                                self.main_window.after(0, self.main_window.start_next_available_file)
                            elif char == 'p':
                                self.last_action_time = current_time
                                self.main_window.after(0, self.main_window.toggle_current_pause)
                except Exception:
                    pass
            
            def on_release(key):
                if not self.running:
                    return False
                
                try:
                    if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                        self.alt_pressed = False
                    elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                        self.shift_pressed = False
                except Exception:
                    pass
            
            with keyboard.Listener(on_press=on_press, on_release=on_release) as self.listener:
                self.listener.join()
                
        except Exception as e:
            print(f"Hotkey listener error: {e}")
    
    def stop(self):
        self.running = False
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
