from datetime import datetime

class ShiftDetector:
    def __init__(self):
        self.shift_schedule = {
            'Morning': (6, 14),    # 6 AM - 2 PM
            'Afternoon': (14, 22), # 2 PM - 10 PM  
            'Night': (22, 6)       # 10 PM - 6 AM
        }
    
    def get_current_shift(self):
        current_hour = datetime.now().hour
        
        for shift, (start, end) in self.shift_schedule.items():
            if start < end:
                if start <= current_hour < end:
                    return shift
            else:
                # Overnight shift
                if current_hour >= start or current_hour < end:
                    return shift
        
        return 'Morning'  # Default fallback