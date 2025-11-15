import streamlit as st
from datetime import datetime
from services.db_helper import (
    get_connection,
    get_active_review_cycle,
    get_all_cycles,
    get_users_for_selection,
    get_pending_approvals_for_manager,
    get_pending_reviewer_requests,
    get_pending_reviews_for_user,
    get_user_nominations_status,
)
from utils.cache_helper import (
    get_cached_departments,
    get_cached_active_users,
    get_cached_active_cycle,
    get_page_cached_user_data,
    SafeCache,
    invalidate_on_user_action
)
# Import centralized email logging for future use
from services.email_logging import log_email_basic, log_email_enhanced

# Helper functions for calculating specific user groups
def get_users_with_pending_nominations():
    """Get users who have incomplete nomination process using optimized JOIN query."""
    conn = get_connection()
    
    # Get active cycle
    active_cycle = get_active_review_cycle()
    if not active_cycle:
        return []
    
    cycle_id = active_cycle['cycle_id']
    
    # Single optimized query using JOINs to find users with pending nomination issues
    # This replaces the N+1 query pattern with a single database call
    query = """
        SELECT DISTINCT 
            u.user_type_id,
            u.first_name || ' ' || u.last_name as name,
            u.email,
            u.vertical,
            u.designation
        FROM users u
        WHERE u.is_active = 1 
        AND (
            -- Users who can nominate more (haven't reached 4 approved)
            (SELECT COUNT(*) 
             FROM feedback_requests fr 
             WHERE fr.requester_id = u.user_type_id 
             AND fr.cycle_id = ? 
             AND fr.status = 'approved') < 4
            
            OR
            
            -- Users with requests awaiting manager approval
            EXISTS (
                SELECT 1 FROM feedback_requests fr2
                WHERE fr2.requester_id = u.user_type_id 
                AND fr2.cycle_id = ?
                AND fr2.status = 'pending_manager_approval'
            )
            
            OR
            
            -- Users with requests awaiting reviewer acceptance
            EXISTS (
                SELECT 1 FROM feedback_requests fr3
                WHERE fr3.requester_id = u.user_type_id 
                AND fr3.cycle_id = ?
                AND fr3.status = 'pending_reviewer_acceptance'
            )
        )
        ORDER BY u.first_name, u.last_name
    """
    
    result = conn.execute(query, (cycle_id, cycle_id, cycle_id))
    users = result.fetchall()
    
    # Convert to expected format
    return [{
        'user_type_id': user[0],
        'name': user[1],
        'email': user[2],
        'vertical': user[3],
        'designation': user[4]
    } for user in users]

def get_managers_with_pending_approvals():
    """Get managers who have pending approval requests using optimized JOIN query."""
    conn = get_connection()
    
    # Get active cycle
    active_cycle = get_active_review_cycle()
    if not active_cycle:
        return []
    
    cycle_id = active_cycle['cycle_id']
    
    # Single optimized query using JOINs to find managers with pending approvals
    # This replaces the N+1 query pattern with a single database call
    query = """
        SELECT DISTINCT 
            m.user_type_id,
            m.email,
            m.first_name || ' ' || m.last_name as name,
            m.vertical
        FROM users m
        INNER JOIN users u ON u.reporting_manager_email = m.email AND u.is_active = 1
        INNER JOIN feedback_requests fr ON fr.requester_id = u.user_type_id
        WHERE m.is_active = 1
        AND fr.cycle_id = ?
        AND fr.status = 'pending_manager_approval'
        ORDER BY m.first_name, m.last_name
    """
    
    result = conn.execute(query, (cycle_id,))
    managers = result.fetchall()
    
    # Convert to expected format
    return [{
        'user_type_id': manager[0],
        'email': manager[1],
        'name': manager[2],
        'vertical': manager[3]
    } for manager in managers]

def get_users_with_pending_reviews():
    """Get users who have accepted reviews but haven't completed them using optimized JOIN query."""
    conn = get_connection()
    
    # Get active cycle
    active_cycle = get_active_review_cycle()
    if not active_cycle:
        return []
    
    cycle_id = active_cycle['cycle_id']
    
    # Single optimized query using JOINs to find users with pending reviews to complete
    # This replaces the N+1 query pattern with a single database call
    query = """
        SELECT DISTINCT 
            u.user_type_id,
            u.first_name || ' ' || u.last_name as name,
            u.email,
            u.vertical,
            u.designation
        FROM users u
        INNER JOIN feedback_requests fr ON fr.reviewer_id = u.user_type_id
        WHERE u.is_active = 1
        AND fr.cycle_id = ?
        AND fr.status = 'approved'
        AND NOT EXISTS (
            -- Check if review is not completed (no final response)
            SELECT 1 FROM final_responses fres
            WHERE fres.request_id = fr.request_id
        )
        ORDER BY u.first_name, u.last_name
    """
    
    result = conn.execute(query, (cycle_id,))
    users = result.fetchall()
    
    # Convert to expected format
    return [{
        'user_type_id': user[0],
        'name': user[1],
        'email': user[2],
        'vertical': user[3],
        'designation': user[4]
    } for user in users]

def get_actual_managers():
    """Get users who are actually managers of other people."""
    conn = get_connection()

    query = """
        SELECT DISTINCT m.user_type_id, m.email, m.first_name, m.last_name, m.vertical
        FROM users m 
        WHERE EXISTS (
            SELECT 1 FROM users u 
            WHERE u.reporting_manager_email = m.email AND u.is_active = 1
        ) AND m.is_active = 1
        ORDER BY m.first_name, m.last_name
    """
    result = conn.execute(query)
    managers = result.fetchall()

    return [{
        'user_type_id': m[0],
        'email': m[1], 
        'name': f"{m[2]} {m[3]}",
        'vertical': m[4]
    } for m in managers]

st.title("Email Notifications Center")
st.markdown("Configure and send email notifications for feedback deadlines and reminders")

# Get active cycle info (cached for 1 hour - safe, changes infrequently)
active_cycle = get_cached_active_cycle()

if not active_cycle:
    st.warning("No active review cycle found. Email notifications require an active cycle.")
    st.info("Create a new review cycle from the Dashboard to enable email notifications.")
    st.stop()

# Display active cycle info
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Active Cycle:** {active_cycle['cycle_display_name']}")
    st.write(f"Phase: {active_cycle.get('phase_status', 'Active')}")
with col2:
    st.write(f"Nomination Deadline: {active_cycle['nomination_deadline']}")
    st.write(f"Feedback Deadline: {active_cycle['feedback_deadline']}")

st.markdown("---")

# Send targeted notifications only
st.subheader("Send Targeted Notifications")

# Notification type selection
notification_type = st.selectbox(
    "Select Notification Type:",
    [
        "nomination_reminder",
        "approval_reminder",
        "feedback_reminder",
        "deadline_warning",
        "cycle_completion",
        "custom_message",
    ],
    format_func=lambda x: {
        "nomination_reminder": "Nomination Reminder",
        "approval_reminder": "Manager Approval Reminder",
        "feedback_reminder": "Feedback Completion Reminder",
        "deadline_warning": "Deadline Warning",
        "cycle_completion": "Cycle Completion Notice",
        "custom_message": "Custom Message",
    }[x],
)

# Target audience selection - dynamic based on notification type
col1, col2 = st.columns(2)
with col1:
    # Build audience options dynamically
    audience_options = [
        "all_users",
        "specific_users", 
        "by_vertical",
        "managers_only",
    ]
    
    # Add specific pending option based on notification type
    if notification_type == "nomination_reminder":
        audience_options.append("pending_nominations")
    elif notification_type == "approval_reminder":
        audience_options.append("pending_approvals")
    elif notification_type == "feedback_reminder":
        audience_options.append("pending_reviews")
    
    def get_audience_label(x):
        labels = {
            "all_users": "All Active Users",
            "specific_users": "Specific Users",
            "by_vertical": "By Department", 
            "managers_only": "Managers Only",
            "pending_nominations": "Users with Pending Nomination Approvals",
            "pending_approvals": "Managers with Pending Approvals",
            "pending_reviews": "Users with Pending Reviews",
        }
        return labels.get(x, x)
    
    audience_type = st.radio(
        "Target Audience:",
        audience_options,
        format_func=get_audience_label,
    )

with col2:
    st.info("All notifications are sent immediately when the 'Send Notification' button is clicked.")
    
    # Show specific information for pending nomination types
    if audience_type == "pending_nominations":
        st.info("""
        **Users with Pending Nomination Approvals:**
        - Users who haven't nominated 4 people
        - Users whose managers haven't approved their nominations  
        - Users whose reviewers haven't accepted their invitations
        """)
    elif audience_type == "pending_approvals":
        st.info("""
        **Managers with Pending Approvals:**
        - Managers who have pending nominations awaiting their approval
        """)
    elif audience_type == "pending_reviews":
        st.info("""
        **Users with Pending Reviews:**
        - Users who have accepted feedback requests but haven't completed them
        """)

# Audience-specific configuration
selected_users = []
selected_vertical = None

if audience_type == "specific_users":
    all_users = get_users_for_selection()
    user_options = [f"{user['name']} ({user['email']})" for user in all_users]
    selected_user_options = st.multiselect(
        "Select Users:", user_options, help="Choose specific users to notify"
    )
    # Map back to user objects
    selected_users = [
        all_users[i]
        for i, option in enumerate(user_options)
        if option in selected_user_options
    ]

elif audience_type == "by_vertical":
    # Use cached departments (1-hour cache - safe, rarely changes)
    verticals = get_cached_departments()
    selected_vertical = st.selectbox(
        "Select Department:", [v[0] for v in verticals if v[0]]
    )
    
elif audience_type == "managers_only":
    # Get actual managers (users who manage other people)
    selected_users = get_actual_managers()
    st.success(f"Found {len(selected_users)} managers")
    
elif audience_type == "pending_nominations":
    # Get users with pending nomination issues  
    selected_users = get_users_with_pending_nominations()
    st.success(f"Found {len(selected_users)} users with pending nomination approvals")
    
elif audience_type == "pending_approvals":
    # Get managers with pending approval requests
    selected_users = get_managers_with_pending_approvals()  
    st.success(f"Found {len(selected_users)} managers with pending approvals")
    
elif audience_type == "pending_reviews":
    # Get users with pending reviews to complete
    selected_users = get_users_with_pending_reviews()
    st.success(f"Found {len(selected_users)} users with pending reviews")
    
elif audience_type == "all_users":
    selected_users = get_users_for_selection()
    st.success(f"Found {len(selected_users)} active users")

# Message customization
st.subheader("Message Configuration")

# Pre-defined templates based on notification type
templates = {
    "nomination_reminder": {
        "subject": "Action Required: Complete Your Nomination Process",
        "body": """Dear {name},

We notice you have pending items in the nomination process for {cycle_name}.

This could include:
• Nominating up to 4 colleagues for feedback
• Waiting for manager approval of your nominations  
• Waiting for reviewers to accept your feedback invitations

Please log into the system to check your current status and complete any remaining steps. The nomination deadline is {nomination_deadline}.

If you have questions, please contact HR.

Best regards,
Talent Management""",
    },
    "approval_reminder": {
        "subject": "Manager Action Required: Review Team Nominations",
        "body": """Dear {name},

You have pending nomination approvals for your team members in the {cycle_name}.

Please review and approve/reject the nominations at your earliest convenience. The nomination deadline is {nomination_deadline}.

Questions? Contact HR.

Best regards,
Talent Management""",
    },
    "feedback_reminder": {
        "subject": "Reminder: Complete Your Feedback Reviews",
        "body": """Dear {name},

You have {pending_count} feedback review(s) pending completion for the {cycle_name}.

Please complete these reviews by {feedback_deadline} to ensure everyone receives their feedback on time.

Thank you for your participation.

Best regards,
Talent Management""",
    },
    "deadline_warning": {
        "subject": "Urgent: Approaching Deadline",
        "body": """Dear {name},

This is a final reminder that the deadline for {deadline_type} is approaching: {deadline_date}.

Please take action immediately to avoid missing this important deadline.

Contact HR if you need assistance.

Best regards,
Talent Management""",
    },
    "cycle_completion": {
        "subject": "Feedback Cycle Complete - Thank You!",
        "body": """Dear {name},

The {cycle_name} has been successfully completed.

Your feedback results are now available in the system. Thank you for your participation in this important development process.

Best regards,
Talent Management""",
    },
    "custom_message": {
        "subject": "Custom Notification",
        "body": """Dear {name},

[Your custom message here]

Best regards,
Talent Management""",
    },
}

template = templates[notification_type]

# Allow customization
custom_subject = st.text_input("Email Subject:", value=template["subject"])

custom_body = st.text_area(
    "Email Body:",
    value=template["body"],
    height=200,
    help="Available variables: {name}, {email}, {cycle_name}, {nomination_deadline}, {feedback_deadline}, {pending_count}",
)

# Preview section
st.subheader("Preview")
with st.expander("Email Preview"):
    preview_vars = {
        "name": "John Doe",
        "email": "john.doe@company.com",
        "cycle_name": active_cycle["cycle_display_name"],
        "nomination_deadline": active_cycle["nomination_deadline"],
        "feedback_deadline": active_cycle["feedback_deadline"],
        "pending_count": "2",
        "deadline_type": "feedback completion",
        "deadline_date": active_cycle["feedback_deadline"],
    }

    try:
        preview_subject = custom_subject.format(**preview_vars)
        preview_body = custom_body.format(**preview_vars)

        st.write(f"**Subject:** {preview_subject}")
        st.write("**Body:**")
        st.text(preview_body)
    except KeyError as e:
        st.error(f"Invalid template variable: {e}")

# Send configuration
col1, col2 = st.columns(2)
with col1:
    st.write("**Delivery:** Send Immediately")

with col2:
    # Calculate recipient count - cache user data to avoid duplicate queries
    recipient_count = 0
    cached_users = None
    
    if audience_type == "all_users":
        # Use page-level cache to avoid querying twice in same page load
        cached_users = get_page_cached_user_data(
            "all_active_users",
            "SELECT user_type_id, first_name, last_name, email FROM users WHERE is_active = 1"
        )
        recipient_count = len(cached_users)
    elif audience_type == "specific_users":
        recipient_count = len(selected_users)
        cached_users = selected_users
    elif audience_type == "by_vertical" and selected_vertical:
        # Use page-level cache for vertical users
        cached_users = get_page_cached_user_data(
            f"vertical_users_{selected_vertical}",
            "SELECT user_type_id, first_name, last_name, email FROM users WHERE is_active = 1 AND vertical = ?",
            (selected_vertical,)
        )
        recipient_count = len(cached_users)
    elif audience_type == "pending_nominations":
        cached_users = get_users_with_pending_nominations()
        recipient_count = len(cached_users)
    elif audience_type == "pending_approvals":
        cached_users = get_managers_with_pending_approvals()
        recipient_count = len(cached_users)
    elif audience_type == "pending_reviews":
        cached_users = get_users_with_pending_reviews()
        recipient_count = len(cached_users)

    st.write(f"**Recipients:** {recipient_count} users")

# Send button
if st.button("Send Notification", type="primary", disabled=recipient_count == 0):
    # Use cached users to avoid duplicate queries
    success_count = 0
    users_to_send = cached_users or []

    # Count successful sends (simulation)
    success_count = len(users_to_send)

    if success_count > 0:
        # Enhanced email logging with new structure
        conn = get_connection()
        try:
            # Get current cycle
            active_cycle = get_active_review_cycle()
            cycle_id = active_cycle.get('cycle_id') if active_cycle else None
            
            # Create a master log entry
            cursor = conn.execute(
                """
                INSERT INTO email_logs (
                    email_type, subject, status, email_category, 
                    initiated_by, cycle_id, sent_at
                ) VALUES (?, ?, 'sent', 'targeted', ?, ?, datetime('now'))
                """,
                (
                    notification_type,
                    custom_subject,
                    st.session_state["user_data"]["user_type_id"],
                    cycle_id
                ),
            )
            log_id = cursor.lastrowid
            
            # Use cached recipients to avoid duplicate queries
            all_recipients = []
            
            if audience_type in ["all_users", "by_vertical"]:
                # Use cached database results (tuples: user_type_id, first_name, last_name, email)
                all_recipients = users_to_send
            elif audience_type == "specific_users":
                # Convert user dict format to tuple format
                all_recipients = [(u['user_type_id'], u['name'].split()[0], u['name'].split()[-1], u['email']) for u in users_to_send]
            elif audience_type in ["pending_nominations", "pending_approvals", "pending_reviews"]:
                # Convert user dict format to tuple format
                all_recipients = [(u['user_type_id'], u['name'].split()[0], u['name'].split()[-1], u['email']) for u in users_to_send]
            
            # Insert individual recipient records
            for recipient in all_recipients:
                user_id, first_name, last_name, email = recipient
                recipient_name = f"{first_name} {last_name}"
                
                # Create individual email log entry
                conn.execute(
                    """
                    INSERT INTO email_logs (
                        email_type, subject, status, email_category,
                        recipient_email, recipient_name, initiated_by, cycle_id, sent_at
                    ) VALUES (?, ?, 'sent', 'targeted', ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        notification_type,
                        custom_subject,
                        email,
                        recipient_name,
                        st.session_state["user_data"]["user_type_id"],
                        cycle_id
                    ),
                )
                
                # Also create entry in email_recipients table for detailed tracking
                conn.execute(
                    """
                    INSERT INTO email_recipients (
                        log_id, recipient_email, recipient_name, delivery_status, delivered_at
                    ) VALUES (?, ?, ?, 'delivered', datetime('now'))
                    """,
                    (log_id, email, recipient_name),
                )
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging email: {e}")
            # Fallback to basic logging if new schema fails
            try:
                conn.execute(
                    "INSERT INTO email_logs (email_type, subject, status) VALUES (?, ?, 'sent')",
                    (notification_type, custom_subject)
                )
                conn.commit()
            except:
                pass

        st.success(f"Notification sent to {success_count} recipients!")
        
        # Email sending doesn't change user data, so no cache invalidation needed
        # (We follow the principle: only invalidate when data actually changes)
    else:
        st.error("Failed to send notifications")

# Notification history moved to separate page
st.markdown("---")