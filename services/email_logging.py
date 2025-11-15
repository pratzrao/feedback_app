"""
Email Logging Service
Centralizes email logging patterns across the application.
This is a safe refactor that doesn't change any functionality.
"""

from typing import Optional
from services.db_helper import get_connection, get_active_review_cycle


def log_email_basic(email_type: str, subject: str, status: str = "sent", recipient_email: Optional[str] = None):
    """
    Basic email logging for backward compatibility.
    
    Args:
        email_type: Type of email being sent
        subject: Email subject line
        status: Email status (sent, failed, pending)
        recipient_email: Optional recipient email
    """
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO email_logs (email_type, subject, status, recipient_email)
            VALUES (?, ?, ?, ?)
            """,
            (email_type, subject, status, recipient_email)
        )
        conn.commit()
    except Exception as e:
        # Silent fail to not break email sending
        print(f"Email logging failed: {e}")


def log_email_enhanced(
    email_type: str,
    subject: str,
    status: str = "sent",
    email_category: str = "targeted",
    recipient_email: Optional[str] = None,
    recipient_name: Optional[str] = None,
    initiated_by: Optional[int] = None,
    cycle_id: Optional[int] = None,
    request_id: Optional[int] = None
):
    """
    Enhanced email logging with full metadata.
    
    Args:
        email_type: Type of email being sent
        subject: Email subject line  
        status: Email status (sent, failed, pending)
        email_category: Category (targeted, automation)
        recipient_email: Recipient email address
        recipient_name: Recipient display name
        initiated_by: User ID who initiated the email
        cycle_id: Review cycle ID (auto-detected if None)
        request_id: Associated feedback request ID
    """
    try:
        conn = get_connection()
        
        # Auto-detect cycle if not provided
        if cycle_id is None:
            active_cycle = get_active_review_cycle()
            if active_cycle:
                cycle_id = active_cycle['cycle_id']
        
        # Insert into enhanced email_logs structure
        cursor = conn.execute(
            """
            INSERT INTO email_logs (
                email_type, subject, status, email_category,
                recipient_email, recipient_name, initiated_by, 
                cycle_id, request_id, sent_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                email_type, subject, status, email_category,
                recipient_email, recipient_name, initiated_by,
                cycle_id, request_id
            )
        )
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        # Fallback to basic logging if enhanced schema fails
        print(f"Enhanced email logging failed, falling back to basic: {e}")
        log_email_basic(email_type, subject, status, recipient_email)
        return None


def log_bulk_email_batch(
    email_type: str,
    subject: str,
    recipients: list,
    initiated_by: Optional[int] = None,
    email_category: str = "targeted"
):
    """
    Log a batch of emails sent to multiple recipients.
    
    Args:
        email_type: Type of email being sent
        subject: Email subject line
        recipients: List of recipient tuples (email, name, user_id)
        initiated_by: User ID who initiated the email
        email_category: Category (targeted, automation)
        
    Returns:
        tuple: (master_log_id, individual_log_ids)
    """
    try:
        conn = get_connection()
        
        # Get active cycle
        active_cycle = get_active_review_cycle()
        cycle_id = active_cycle['cycle_id'] if active_cycle else None
        
        # Create a master log entry for the batch
        cursor = conn.execute(
            """
            INSERT INTO email_logs (
                email_type, subject, status, email_category, 
                initiated_by, cycle_id, sent_at
            ) VALUES (?, ?, 'sent', ?, ?, ?, datetime('now'))
            """,
            (email_type, subject, email_category, initiated_by, cycle_id)
        )
        master_log_id = cursor.lastrowid
        
        # Create individual recipient records
        individual_log_ids = []
        for recipient in recipients:
            if len(recipient) >= 2:
                recipient_email = recipient[0]
                recipient_name = recipient[1]
                
                log_id = log_email_enhanced(
                    email_type=email_type,
                    subject=subject,
                    status="sent",
                    email_category=email_category,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    initiated_by=initiated_by,
                    cycle_id=cycle_id
                )
                if log_id:
                    individual_log_ids.append(log_id)
        
        return master_log_id, individual_log_ids
        
    except Exception as e:
        print(f"Bulk email logging failed: {e}")
        # Fallback to basic logging
        log_email_basic(email_type, subject, "sent")
        return None, []


def log_email_recipient_details(
    log_id: int,
    user_id: int,
    email: str,
    name: str,
    status: str = "delivered"
):
    """
    Log detailed recipient information for an email.
    
    Args:
        log_id: Email log ID to associate with
        user_id: Recipient user ID
        email: Recipient email
        name: Recipient name
        status: Delivery status
    """
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO email_recipients (
                log_id, user_id, email, name, status, created_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (log_id, user_id, email, name, status)
        )
        conn.commit()
    except Exception as e:
        # Silent fail to not break email sending
        print(f"Recipient logging failed: {e}")


def log_email_failure(email_type: str, subject: str, error: str, recipient_email: Optional[str] = None):
    """
    Log failed email attempts with error details.
    
    Args:
        email_type: Type of email that failed
        subject: Email subject line
        error: Error message or description
        recipient_email: Optional recipient email
    """
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO email_logs (
                email_type, subject, status, recipient_email, sent_at
            ) VALUES (?, ?, 'failed', ?, datetime('now'))
            """,
            (email_type, f"{subject} [ERROR: {error}]", recipient_email)
        )
        conn.commit()
    except Exception as e:
        print(f"Failed email logging failed: {e}")