import os
import json
import base64
import requests
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GitHubUserStorage:
    def __init__(self):
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.USER_DATA_REPO = os.getenv("GITHUB_REPO", "your-github-username/your-repo-name")
        self.USER_DATA_FILE = "user_data.json"
        self.USER_DATA_PATH = f"https://api.github.com/repos/{self.USER_DATA_REPO}/contents/{self.USER_DATA_FILE}"
        
        # Initialize with default admin user
        self.DEFAULT_DATA = {
            "admin": {
                "password": self.hash_password("admin"),
                "email": "admin@example.com",
                "chat_history": []
            }
        }

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load_user_data(self):
        """Load user data from GitHub"""
        try:
            headers = {
                "Authorization": f"token {self.GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(self.USER_DATA_PATH, headers=headers)
            response.raise_for_status()
            
            content = response.json()["content"]
            decoded_content = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded_content)
        except Exception as e:
            print(f"⚠️ Failed to load user data: {str(e)}")
            return self.DEFAULT_DATA

    def save_user_data(self, data):
        """Save user data to GitHub"""
        try:
            # First get the current file SHA
            headers = {
                "Authorization": f"token {self.GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(self.USER_DATA_PATH, headers=headers)
            sha = response.json().get("sha", None)
            
            # Prepare new content
            content_bytes = json.dumps(data, indent=2).encode("utf-8")
            encoded_content = base64.b64encode(content_bytes).decode("utf-8")
            
            payload = {
                "message": "Update user data",
                "content": encoded_content,
                "sha": sha
            }
            
            response = requests.put(self.USER_DATA_PATH, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Failed to save user data: {str(e)}")
            return False
