# SCHL Time Tracker

Desktop application for tracking employee work time on Photoshop files.

## Overview

This is a Python desktop GUI application built with CustomTkinter for tracking time spent on files by employees. The app sends tracking data to a Supabase database.

## Features

### Core Features
- Employee login/registration system
- File-based time tracking for Photoshop work
- Client detection from file path
- Shift detection (Morning/Afternoon/Night)
- Timer with pause/resume functionality

### Version 2.0 Improvements
1. **Login System** - Employees register and login with username/password (stored in `app_user` table with secure hashing)
2. **Offline Mode** - Data saved locally when offline, auto-syncs when connection returns
3. **Idle Detection** - Auto-pauses timer after 60 seconds of no mouse/keyboard activity
4. **Keyboard Shortcuts**:
   - `Alt+Shift+S` - Start next available file
   - `Alt+Shift+P` - Pause/Resume current file
   - `Alt+Shift+D` - Complete current file (Done)
5. **Enhanced Tracking** - Tracks pause count and idle time per file
6. **Improved Floating UI** - Smaller, cleaner minimized panel
7. **Serial File Opening** - Files open in order, not randomly
8. **Better Multi-file Support** - Switch between files easily

## Project Structure

```
├── main.py                 # Entry point
├── core/
│   ├── supabase_client.py  # Database connection + offline queue + password hashing
│   ├── file_monitor.py     # Global hotkey listener (Alt+Shift shortcuts)
│   └── idle_detector.py    # Mouse/keyboard idle detection (thread-safe)
├── ui/
│   ├── main_window.py      # Main application window
│   ├── login_window.py     # Login/Register screen
│   └── tray_icon.py        # Minimized floating panel
├── utils/
│   ├── shift_detector.py   # Work shift detection
│   └── path_parser.py      # Client extraction from file paths
└── data/
    ├── client_states.json  # Client state storage
    └── offline_queue.json  # Offline data queue
```

## Database Tables (Supabase)

### app_user
- id (auto-generated)
- username (unique)
- password (hashed with per-user salt)
- created_at

### time_entries
- id
- employee_name
- work_type
- shift
- client_name
- filename
- file_path
- time_spent_seconds
- completed_at
- pause_count (NEW - tracks how many times timer was paused)
- total_idle_seconds (NEW - tracks idle time during work)

## SQL for New Columns

Run this in Supabase SQL Editor to add the new columns:

```sql
ALTER TABLE time_entries 
ADD COLUMN pause_count INTEGER DEFAULT 0,
ADD COLUMN total_idle_seconds INTEGER DEFAULT 0;
```

## Running the App

The app runs as a desktop GUI with VNC display. Use the workflow "Time Tracker App" to start.

## Dependencies

- customtkinter - Modern UI framework
- supabase - Database client
- pynput - Keyboard/mouse monitoring for hotkeys and idle detection
- pillow - Image handling
- psutil - Process utilities
- python-dateutil - Date utilities

## Security Notes

- Passwords are hashed with per-user derived salt and iterative hashing
- User credentials never stored in plain text
- Supabase uses anon/public key with Row Level Security (RLS)
- Offline queue data is cleaned of internal metadata before sync

## Technical Notes

- Idle detection uses thread-safe locking for accurate time tracking
- Hotkeys work system-wide using pynput keyboard listener
- Offline queue auto-syncs when internet connection is restored
- All database operations include error handling and fallback to offline storage
