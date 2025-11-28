import threading
import time
from datetime import datetime

class IdleDetector:
    def __init__(self, idle_threshold=60, callback=None):
        self.idle_threshold = idle_threshold
        self.callback = callback
        self.last_activity = datetime.now()
        self.is_idle = False
        self.total_idle_time = 0
        self.idle_start = None
        self.running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.check_thread = None
        self._lock = threading.Lock()
    
    def on_activity(self, *args):
        with self._lock:
            if self.is_idle and self.idle_start:
                idle_duration = (datetime.now() - self.idle_start).total_seconds()
                self.total_idle_time += idle_duration
                self.idle_start = None
            
            self.last_activity = datetime.now()
            self.is_idle = False
    
    def start(self):
        self.running = True
        self.last_activity = datetime.now()
        
        try:
            from pynput import mouse, keyboard
            
            self.mouse_listener = mouse.Listener(
                on_move=self.on_activity,
                on_click=self.on_activity,
                on_scroll=self.on_activity
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_activity
            )
            
            self.mouse_listener.daemon = True
            self.keyboard_listener.daemon = True
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
        except Exception as e:
            print(f"Could not start activity listeners: {e}")
        
        self.check_thread = threading.Thread(target=self._check_idle_loop, daemon=True)
        self.check_thread.start()
    
    def _check_idle_loop(self):
        while self.running:
            time.sleep(5)
            
            if not self.running:
                break
            
            with self._lock:
                idle_seconds = (datetime.now() - self.last_activity).total_seconds()
                
                if idle_seconds >= self.idle_threshold and not self.is_idle:
                    self.is_idle = True
                    self.idle_start = datetime.now()
                    if self.callback:
                        try:
                            self.callback('idle_start')
                        except Exception:
                            pass
    
    def stop(self):
        self.running = False
        
        with self._lock:
            if self.is_idle and self.idle_start:
                idle_duration = (datetime.now() - self.idle_start).total_seconds()
                self.total_idle_time += idle_duration
        
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        except Exception:
            pass
    
    def get_total_idle_time(self):
        with self._lock:
            total = self.total_idle_time
            if self.is_idle and self.idle_start:
                total += (datetime.now() - self.idle_start).total_seconds()
            return int(total)
    
    def reset(self):
        with self._lock:
            self.total_idle_time = 0
            self.idle_start = None
            self.is_idle = False
            self.last_activity = datetime.now()
