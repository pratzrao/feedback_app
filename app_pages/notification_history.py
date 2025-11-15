"""
Notification History Page - Standalone page for viewing email notification history
"""

import streamlit as st
from datetime import datetime
from services.db_helper import get_connection, get_active_review_cycle
from utils.cache_helper import get_cached_active_cycle, get_cached_active_users


# Access control handled by main.py navigation structure

st.title("Notification History")
st.markdown(
    "View and filter all email notifications sent during the current review cycle"
)

# Show current cycle info (cached for 1 hour - safe, changes infrequently)
active_cycle = get_cached_active_cycle()
if active_cycle:
    st.info(
        f"Showing notifications for current cycle: **{active_cycle['cycle_display_name']}**"
    )
else:
    st.warning("No active cycle found. Notification history will be empty.")

# Enhanced filtering options
email_filter = st.selectbox(
    "Email Category:",
    ["All Emails Sent", "Targeted Notifications Sent", "Automation Emails Sent"],
    help="Filter by email category",
)

# Employee filter
st.markdown("**Filter by Recipient (optional):**")
conn = get_connection()

# Get all users for employee filter (cached for 5 minutes - moderate risk)
all_users = get_cached_active_users()

user_options = ["All Recipients"] + [
    f"{user[1]} {user[2]} ({user[3]})" for user in all_users
]
selected_employee = st.selectbox(
    "Select Employee:", 
    user_options, 
    help="Filter emails sent to a specific employee"
)

# Build query based on filters - only show notifications for current cycle
if active_cycle:
    query_conditions = ["el.cycle_id = ?"]
    query_params = [active_cycle["cycle_id"]]
else:
    # If no active cycle, show nothing
    query_conditions = ["1 = 0"]  # Always false condition
    query_params = []

# Email category filter
if email_filter == "Targeted Notifications Sent":
    query_conditions.append(
        "(el.email_category = 'targeted' OR el.email_category IS NULL)"
    )
elif email_filter == "Automation Emails Sent":
    query_conditions.append("el.email_category = 'automation'")

# Employee filter
if selected_employee != "All Recipients":
    selected_user_email = selected_employee.split("(")[1].split(")")[0]
    query_conditions.append("el.recipient_email = ?")
    query_params.append(selected_user_email)

where_clause = " AND ".join(query_conditions)

# Pagination controls
col1, col2, col3 = st.columns(3)
with col1:
    page_size = st.selectbox(
        "Records per page:",
        [25, 50, 100, 200],
        index=2,  # Default to 100 (same as before)
        help="Number of records to show per page"
    )

with col2:
    # Get total count first for pagination calculation
    try:
        count_query = f"""
            SELECT COUNT(*)
            FROM email_logs el
            LEFT JOIN users sender ON el.initiated_by = sender.user_type_id
            LEFT JOIN review_cycles rc ON el.cycle_id = rc.cycle_id
            WHERE {where_clause}
        """
        total_records = conn.execute(count_query, tuple(query_params)).fetchone()[0]
    except Exception:
        total_records = 0
    
    if total_records > 0:
        max_page = max(1, (total_records + page_size - 1) // page_size)  # Ceiling division
        current_page = st.number_input(
            "Page:",
            min_value=1,
            max_value=max_page,
            value=1,
            step=1,
            help=f"Page number (1 to {max_page})"
        )
    else:
        current_page = 1
        max_page = 1

with col3:
    if total_records > 0:
        start_record = (current_page - 1) * page_size + 1
        end_record = min(current_page * page_size, total_records)
        st.write(f"**Showing {start_record}-{end_record} of {total_records}**")
    else:
        st.write("**No records found**")

# Calculate offset for pagination
offset = (current_page - 1) * page_size

try:
    # Enhanced query with user details and pagination
    email_logs = conn.execute(
        f"""
        SELECT 
            el.sent_at,
            el.email_type,
            el.subject,
            el.status,
            el.recipient_email,
            el.recipient_name,
            el.email_category,
            sender.first_name || ' ' || sender.last_name as sent_by_name,
            el.initiated_by,
            el.cycle_id,
            rc.cycle_display_name,
            el.request_id
        FROM email_logs el
        LEFT JOIN users sender ON el.initiated_by = sender.user_type_id
        LEFT JOIN review_cycles rc ON el.cycle_id = rc.cycle_id
        WHERE {where_clause}
        ORDER BY el.sent_at DESC
        LIMIT ? OFFSET ?
    """,
        tuple(query_params + [page_size, offset]),
    ).fetchall()

    if email_logs:
        # Display current page info (already shown in pagination controls above)
        pass

        # Group by date for better organization
        logs_by_date = {}
        
        # Define constants for status styling
        STATUS_STYLING = {
            "sent": ("🟢", "Sent"),
            "pending": ("🟡", "Pending"),
        }
        DEFAULT_STATUS = ("🔴", "Failed")
        
        CATEGORY_BADGES = {
            "targeted": "🎯 Targeted",
            "automation": "🤖 Automation"
        }

        for log in email_logs:
            sent_at_str = log[0]
            if sent_at_str:
                try:
                    parsed_date = datetime.fromisoformat(
                        sent_at_str.replace("Z", "+00:00")
                    ).date()
                    sent_date = parsed_date
                except (ValueError, AttributeError):
                    sent_date = "Unknown Date"
            else:
                sent_date = "Unknown Date"

            if sent_date not in logs_by_date:
                logs_by_date[sent_date] = []
            logs_by_date[sent_date].append(log)

        # Display logs grouped by date
        for date_group in sorted(logs_by_date.keys(), reverse=True):
            if date_group != "Unknown Date":
                st.markdown(f"### 📅 {date_group}")
            else:
                st.markdown("### 📅 Unknown Date")

            for log in logs_by_date[date_group]:
                sent_at = log[0][:16] if log[0] else "Unknown"
                email_type = log[1].replace("_", " ").title() if log[1] else "Unknown"
                subject = log[2] or "No Subject"
                status = log[3] or "unknown"
                recipient_email = log[4] or "Unknown"
                recipient_name = log[5] or "Unknown Recipient"
                email_category = log[6] or "targeted"
                sent_by_name = log[7] or "System"
                cycle_name = log[10] or "N/A"

                # Status styling
                status_color, status_text = STATUS_STYLING.get(
                    status, DEFAULT_STATUS
                )

                # Category badge
                category_badge = CATEGORY_BADGES.get(
                    email_category, "🎯 Targeted"
                )

                with st.expander(
                    f"{status_color} {sent_at} • {email_type} → "
                    f"{recipient_name} ({recipient_email})",
                    expanded=False,
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Subject:** {subject}")
                        st.write(f"**Status:** {status_text}")
                        st.write(f"**Category:** {category_badge}")
                        st.write(f"**Recipient:** {recipient_name}")

                    with col2:
                        st.write(f"**Email:** {recipient_email}")
                        st.write(f"**Initiated by:** {sent_by_name}")
                        st.write(f"**Cycle:** {cycle_name}")
                        st.write(f"**Sent:** {sent_at}")
    else:
        st.info("No notifications found matching your filters")

except Exception as e:
    st.error(f"Error retrieving email logs: {e}")
    st.warning(
        "Some columns may not exist yet. Please run the database schema update script."
    )
