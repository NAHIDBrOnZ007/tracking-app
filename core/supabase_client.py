from supabase import create_client, Client
import os
import json
import hashlib
from datetime import datetime

class SupabaseClient:
    def __init__(self):
        self.url = "https://owvdzkshzhhegophqwlp.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93dmR6a3NoemhoZWdvcGhxd2xwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA3ODA4MTEsImV4cCI6MjA3NjM1NjgxMX0.Rg3IxzjqrxVOXo0fYC082YS4Ycejge-T1CvCUxxiGRs"
        self.offline_queue_file = "data/offline_queue.json"
        self.is_online = True
        
        try:
            self.client: Client = create_client(self.url, self.key)
            self.is_online = True
        except Exception as e:
            print(f"Supabase connection error: {e}")
            self.client = None
            self.is_online = False
    
    def _hash_password(self, password, username=""):
        base_salt = "schl_time_tracker_2024"
        user_salt = hashlib.sha256((username + base_salt).encode()).hexdigest()[:16]
        combined = password + user_salt + base_salt
        for _ in range(1000):
            combined = hashlib.sha256(combined.encode()).hexdigest()
        return combined
    
    def check_connection(self):
        try:
            if self.client:
                self.client.table('time_entries').select('id').limit(1).execute()
                self.is_online = True
                return True
        except Exception:
            self.is_online = False
        return False
    
    def register_user(self, username, password):
        if not self.client:
            return False, "No connection to database"
        
        try:
            existing = self.client.table('app_user').select('*').eq('username', username).execute()
            if existing.data and len(existing.data) > 0:
                return False, "Username already exists"
            
            hashed_password = self._hash_password(password, username)
            
            data = {
                'username': username,
                'password': hashed_password,
                'created_at': datetime.now().isoformat()
            }
            response = self.client.table('app_user').insert(data).execute()
            if response.data:
                return True, "Registration successful"
            return False, "Registration failed"
        except Exception as e:
            return False, f"Error: {e}"
    
    def login_user(self, username, password):
        if not self.client:
            return False, None, "No connection to database"
        
        try:
            hashed_password = self._hash_password(password, username)
            response = self.client.table('app_user').select('*').eq('username', username).eq('password', hashed_password).execute()
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                user_data['password'] = None
                return True, user_data, "Login successful"
            return False, None, "Invalid username or password"
        except Exception as e:
            return False, None, f"Error: {e}"
    
    def insert_time_entry(self, data):
        if not self.client or not self.is_online:
            self.save_to_offline_queue(data)
            print("Saved to offline queue")
            return False
            
        try:
            response = self.client.table('time_entries').insert(data).execute()
            print("Data saved to Supabase successfully")
            return True
        except Exception as e:
            print(f"Error inserting data: {e}")
            self.save_to_offline_queue(data)
            return False
    
    def save_to_offline_queue(self, data):
        queue = self.load_offline_queue()
        entry = data.copy()
        entry['_queued_at'] = datetime.now().isoformat()
        queue.append(entry)
        
        try:
            os.makedirs(os.path.dirname(self.offline_queue_file), exist_ok=True)
            with open(self.offline_queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            print(f"Error saving offline queue: {e}")
    
    def load_offline_queue(self):
        try:
            if os.path.exists(self.offline_queue_file):
                with open(self.offline_queue_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading offline queue: {e}")
        return []
    
    def sync_offline_queue(self):
        if not self.check_connection():
            return 0
        
        queue = self.load_offline_queue()
        if not queue:
            return 0
        
        synced_count = 0
        remaining = []
        
        for entry in queue:
            clean_entry = {k: v for k, v in entry.items() if not k.startswith('_')}
            
            try:
                response = self.client.table('time_entries').insert(clean_entry).execute()
                if response.data:
                    synced_count += 1
                else:
                    remaining.append(entry)
            except Exception as e:
                print(f"Error syncing entry: {e}")
                remaining.append(entry)
        
        try:
            with open(self.offline_queue_file, 'w') as f:
                json.dump(remaining, f, indent=2)
        except Exception:
            pass
        
        print(f"Synced {synced_count} entries from offline queue")
        return synced_count
    
    def get_offline_queue_count(self):
        return len(self.load_offline_queue())
    
    def get_time_entries(self, employee_name=None):
        if not self.client:
            return []
            
        try:
            query = self.client.table('time_entries').select('*')
            if employee_name:
                query = query.eq('employee_name', employee_name)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
