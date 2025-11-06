import bcrypt
from services.db_helper import fetch_user_by_email, fetch_user_roles, set_user_password

def authenticate_user(email, password):
    """Authenticate user by email and password."""
    user = fetch_user_by_email(email)
    
    if not user:
        return False, "User not found.", None
    
    if not user["password_hash"]:
        return False, "Please set up your password first.", None
    
    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return False, "Incorrect password.", None
    
    # Get roles
    roles = fetch_user_roles(user["user_type_id"])
    user["roles"] = roles
    
    return True, None, user

def check_user_needs_password_setup(email):
    """Check if user exists but needs password setup."""
    user = fetch_user_by_email(email)
    if user and not user["password_hash"]:
        return True, user
    return False, None

def create_user_password(email, password):
    """Set password for first-time login."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return set_user_password(email, password_hash)