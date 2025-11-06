import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import streamlit as st

def send_email(to_email, subject, body):
    """Send email using SMTP."""
    try:
        # Email configuration from secrets
        if "email" in st.secrets:
            smtp_server = st.secrets["email"]["smtp_server"]
            smtp_port = st.secrets["email"]["smtp_port"]
            email_user = st.secrets["email"]["email_user"]
            email_password = st.secrets["email"]["email_password"]
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            text = msg.as_string()
            server.sendmail(email_user, to_email, text)
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