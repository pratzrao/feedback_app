import bcrypt
import secrets
from datetime import datetime, timedelta
from services.db_helper import fetch_user_by_email, fetch_user_roles, set_user_password, get_connection

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
    if user:
        if not user["password_hash"]:
            return True, user  # Needs password setup
        else:
            return False, user  # Has password, ready to login
    return False, None  # User doesn't exist

def create_user_password(email, password):
    """Set password for first-time login."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return set_user_password(email, password_hash)

def generate_password_reset_token(email):
    """Generate a secure password reset token and store it in database."""
    user = fetch_user_by_email(email)
    if not user:
        return False, "User not found."
    
    # Generate secure token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)  # Token expires in 24 hours
    
    conn = get_connection()
    try:
        # Store token in database
        update_query = """
            UPDATE users 
            SET password_reset_token = ?, password_reset_expires = ?
            WHERE email = ?
        """
        conn.execute(update_query, (reset_token, expires_at.isoformat(), email))
        conn.commit()
        
        # Send reset email
        from services.email_service import send_password_reset_email
        if send_password_reset_email(email, user['first_name'], reset_token):
            return True, "Password reset email sent successfully!"
        else:
            return False, "Failed to send password reset email. Please contact your administrator."
            
    except Exception as e:
        print(f"Error generating reset token: {e}")
        return False, "Error generating reset token. Please try again."

def validate_reset_token(token):
    """Validate a password reset token."""
    conn = get_connection()
    try:
        query = """
            SELECT email, password_reset_expires, first_name, last_name
            FROM users 
            WHERE password_reset_token = ? AND is_active = 1
        """
        result = conn.execute(query, (token,))
        user = result.fetchone()
        
        if not user:
            return False, None, "Invalid reset token."
        
        email, expires_str, first_name, last_name = user
        expires_at = datetime.fromisoformat(expires_str)
        
        if datetime.now() > expires_at:
            return False, None, "Reset token has expired. Please request a new one."
        
        return True, {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }, None
        
    except Exception as e:
        print(f"Error validating reset token: {e}")
        return False, None, "Error validating token."

def reset_password_with_token(token, new_password):
    """Reset password using a valid token."""
    # First validate the token
    is_valid, user_data, error = validate_reset_token(token)
    if not is_valid:
        return False, error
    
    email = user_data['email']
    
    # Hash the new password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_connection()
    try:
        # Update password and clear reset token
        update_query = """
            UPDATE users 
            SET password_hash = ?, password_reset_token = NULL, password_reset_expires = NULL
            WHERE email = ?
        """
        conn.execute(update_query, (password_hash, email))
        conn.commit()
        
        return True, "Password reset successfully!"
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False, "Error resetting password. Please try again."