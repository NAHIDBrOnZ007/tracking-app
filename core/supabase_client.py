from supabase import create_client, Client
import os

class SupabaseClient:
    def __init__(self):
        self.url = "https://owvdzkshzhhegophqwlp.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93dmR6a3NoemhoZWdvcGhxd2xwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA3ODA4MTEsImV4cCI6MjA3NjM1NjgxMX0.Rg3IxzjqrxVOXo0fYC082YS4Ycejge-T1CvCUxxiGRs"
        
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"Supabase connection error: {e}")
            self.client = None
    
    def insert_time_entry(self, data):
        if not self.client:
            print("Supabase client not available")
            return False
            
        try:
            response = self.client.table('time_entries').insert(data).execute()
            print("Data saved to Supabase successfully")
            return True
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False
    
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