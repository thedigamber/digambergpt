from .storage import GitHubUserStorage

# Initialize storage
user_storage = GitHubUserStorage()

def get_user_db():
    """Get the user database"""
    return user_storage.load_user_data()

def save_user_db(data):
    """Save the user database"""
    return user_storage.save_user_data(data)

def hash_password(password):
    """Hash a password for storage"""
    return user_storage.hash_password(password)
