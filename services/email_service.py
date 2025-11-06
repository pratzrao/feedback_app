import smtplib
import streamlit as st
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart

def send_email(to_email, subject, body):
    """Send email using SMTP."""
    try:
        # Email configuration from secrets
        if "email" in st.secrets:
            smtp_server = st.secrets["email"]["smtp_server"]
            smtp_port = st.secrets["email"]["smtp_port"]
            email_user = st.secrets["email"]["email_user"]
            email_password = st.secrets["email"]["email_password"]
            from_email = st.secrets["email"].get("from_email", email_user)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True
        else:
            print("Email configuration not found in secrets. Skipping email.")
            return True  # Return True for demo purposes
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_feedback_request_email(to_email, requester_name, app_url=""):
    """Send feedback request notification."""
    subject = "360° Feedback Request"
    body = f"""
    <h2>Feedback Request</h2>
    <p>Hello,</p>
    <p>{requester_name} has requested your feedback as part of their 360° performance review.</p>
    <p>Please log in to the feedback system to complete your review.</p>
    <p>Thank you for your participation!</p>
    """
    return send_email(to_email, subject, body)

def send_reminder_email(to_email, pending_count, app_url=""):
    """Send reminder for pending reviews."""
    subject = "Reminder: Pending Feedback Reviews"
    body = f"""
    <h2>Pending Reviews Reminder</h2>
    <p>Hello,</p>
    <p>You have {pending_count} pending feedback review(s) waiting for completion.</p>
    <p>Please log in to the system to complete your reviews at your earliest convenience.</p>
    <p>Thank you!</p>
    """
    return send_email(to_email, subject, body)

def send_approval_needed_email(manager_email, requester_name):
    """Send notification to manager about pending approvals."""
    subject = "Feedback Request Approval Needed"
    body = f"""
    <h2>Approval Required</h2>
    <p>Hello,</p>
    <p>{requester_name} has submitted feedback requests that require your approval.</p>
    <p>Please log in to the system to review and approve these nominations.</p>
    <p>Thank you!</p>
    """
    return send_email(manager_email, subject, body)

def send_rejection_notice_email(requester_email, reviewer_name, rejection_reason):
    """Send rejection notice to requester."""
    subject = "Feedback Request Rejected"
    body = f"""
    <h2>Feedback Request Rejected</h2>
    <p>Hello,</p>
    <p>Your feedback request for {reviewer_name} has been rejected by your manager.</p>
    <p><strong>Reason:</strong> {rejection_reason}</p>
    <p>Please select a different reviewer and resubmit your request.</p>
    <p>Thank you!</p>
    """
    return send_email(requester_email, subject, body)

def send_password_reset_email(email, first_name, reset_token):
    """Send password reset email with token."""
    subject = "Password Reset - 360° Feedback System"
    body = f"""
    <h2>Password Reset Request</h2>
    <p>Hello {first_name},</p>
    <p>You have requested to reset your password for the 360° Feedback System.</p>
    
    <div style="background-color: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <h3>Your Reset Token:</h3>
        <p style="font-family: monospace; font-size: 16px; font-weight: bold; color: #333;">
            {reset_token}
        </p>
    </div>
    
    <p><strong>Instructions:</strong></p>
    <ol>
        <li>Copy the reset token above</li>
        <li>Return to the login page</li>
        <li>Click "Forgot Password?" again</li>
        <li>Select "I have a reset token"</li>
        <li>Paste the token and create your new password</li>
    </ol>
    
    <p><strong>Important:</strong></p>
    <ul>
        <li>This token expires in 24 hours</li>
        <li>Use this token only once</li>
        <li>If you didn't request this reset, please contact your administrator</li>
    </ul>
    
    <p>If you have any issues, please contact your system administrator.</p>
    
    <p>Best regards,<br>360° Feedback System</p>
    """
    return send_email(email, subject, body)