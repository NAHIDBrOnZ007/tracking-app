import json
import os

class ClientManager:
    def __init__(self):
        self.state_file = "client_states.json"
        self.client_states = self.load_states()
    
    def load_states(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_states(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.client_states, f)
    
    def save_client_state(self, client_name, files_data):
        file_paths = [file_data['path'] for file_data in files_data]
        self.client_states[client_name] = {
            'file_paths': file_paths,
            'saved_at': os.path.getmtime(__file__)  # placeholder
        }
        self.save_states()
    
    def load_client_state(self, client_name):
        if client_name in self.client_states:
            return self.client_states[client_name].get('file_paths', [])
        return []