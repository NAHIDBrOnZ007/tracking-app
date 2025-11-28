import os
import re

class PathParser:
    def __init__(self):
        self.patterns = [
            r'\\\d{4}_[A-Z]+_[A-Za-z0-9]+\\',  # \0034_TOG_Enhance\
            r'\\\d{4}_[A-Z]+\\',              # \0034_JH\
            r'/\d{4}_[A-Z]+_[A-Za-z0-9]+/',   # /0034_TOG_Enhance/
            r'/\d{4}_[A-Z]+/',                # /0034_JH/
        ]
    
    def extract_client_from_path(self, file_path):
        # Convert to consistent format
        normalized_path = file_path.replace('/', '\\')
        
        # Try patterns to extract client code
        for pattern in self.patterns:
            matches = re.findall(pattern, normalized_path)
            if matches:
                # Extract just the client code (0034_JH) from the matched path segment
                client_match = re.search(r'\d{4}_[A-Z]+(?:_[A-Za-z0-9]+)?', matches[0])
                if client_match:
                    return client_match.group()
        
        # Fallback: split path and look for pattern
        path_parts = normalized_path.split('\\')
        for part in path_parts:
            # Look for patterns like 0034_JH or 0035_TOG_Enhance
            if re.match(r'\d{4}_[A-Z]+', part):
                return part
            if re.match(r'\d{4}_[A-Z]+_[A-Za-z0-9]+', part):
                return part
        
        # Final fallback: use the folder that contains numbers and letters
        for part in path_parts:
            if any(c.isdigit() for c in part) and any(c.isalpha() for c in part):
                return part
        
        return "Unknown_Client"