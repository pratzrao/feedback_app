import streamlit as st
from datetime import datetime, timedelta, date
from services.db_helper import (
    get_hr_dashboard_metrics,
    get_users_with_pending_reviews,
    create_new_review_cycle,
    get_active_review_cycle,
    get_current_cycle_phase
)
from services.email_service import send_reminder_email

st.title("HR Analytics Dashboard")

# Current cycle status
st.subheader("Current Review Cycle")
active_cycle = get_active_review_cycle()
current_phase = get_current_cycle_phase()

if active_cycle:
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**{active_cycle['cycle_name']}**")
        st.write(f"Current Phase: **{current_phase}**")
    with col2:
        st.write(f"Nomination Deadline: {active_cycle['nomination_deadline']}")
        st.write(f"Feedback Deadline: {active_cycle['feedback_deadline']}")
else:
    st.warning("⚠️ No active review cycle")

# Create new cycle section
st.subheader("Cycle Management")

if st.button("🔄 Create New Review Cycle"):
    st.session_state.show_cycle_form = True

if st.session_state.get('show_cycle_form', False):
    st.subheader("Create New Review Cycle")
    
    with st.form("new_cycle_form"):
        cycle_name = st.text_input(
            "Cycle Name", 
            value=f"Review Cycle {datetime.now().strftime('%Y-%m')}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            nomination_start = st.date_input(
                "Nomination Start Date", 
                value=date.today()
            )
            nomination_deadline = st.date_input(
                "Nomination Deadline", 
                value=nomination_start + timedelta(weeks=1)
            )
            approval_deadline = st.date_input(
                "Approval Deadline", 
                value=nomination_deadline + timedelta(weeks=1)
            )
        
        with col2:
            feedback_deadline = st.date_input(
                "Feedback Deadline", 
                value=approval_deadline + timedelta(weeks=3)
            )
            results_deadline = st.date_input(
                "Results Deadline", 
                value=feedback_deadline + timedelta(weeks=1)
            )
        
        col1, col2 = st.columns(2)
        with col1:
            create_cycle = st.form_submit_button("✅ Create Cycle", type="primary")
        with col2:
            cancel_cycle = st.form_submit_button("❌ Cancel")
        
        if create_cycle:
            if cycle_name:
                user_id = st.session_state["user_data"]["user_type_id"]
                if create_new_review_cycle(
                    cycle_name, nomination_start, nomination_deadline, 
                    approval_deadline, feedback_deadline, results_deadline, user_id
                ):
                    st.success("🎉 Review cycle created successfully!")
                    st.session_state.show_cycle_form = False
                    st.rerun()
                else:
                    st.error("❌ Error creating cycle")
            else:
                st.error("Please enter a cycle name")
        
        if cancel_cycle:
            st.session_state.show_cycle_form = False
            st.rerun()

# Get metrics
metrics = get_hr_dashboard_metrics()

# Display key metrics
st.subheader("Dashboard Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", metrics.get('total_users', 0))

with col2:
    st.metric("Pending Requests", metrics.get('pending_requests', 0))

with col3:
    st.metric("Completed This Month", metrics.get('completed_this_month', 0))

with col4:
    st.metric("Users with Incomplete", metrics.get('users_with_incomplete', 0))

# Users with pending reviews
st.subheader("Users with Pending Reviews")

pending_users = get_users_with_pending_reviews()

if pending_users:
    st.write(f"**{len(pending_users)} users** have pending reviews:")
    
    # Bulk reminder option
    if st.button("📨 Send Reminders to All", type="secondary"):
        success_count = 0
        for user in pending_users:
            if send_reminder_email(user['email'], user['pending_count']):
                success_count += 1
        
        if success_count > 0:
            st.success(f"✅ Reminders sent to {success_count} users!")
        else:
            st.error("❌ Failed to send reminders.")
    
    st.divider()
    
    # Individual user list
    for user in pending_users:
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.write(f"**{user['name']}**")
        
        with col2:
            st.write(f"{user['vertical']}")
        
        with col3:
            st.write(f"**{user['pending_count']}** pending")
        
        with col4:
            if st.button("📨 Remind", key=f"remind_{user['user_type_id']}"):
                if send_reminder_email(user['email'], user['pending_count']):
                    st.success("✅ Sent!")
                else:
                    st.error("❌ Failed")
        
        st.divider()
else:
    st.success("🎉 No users have pending reviews!")

# Additional insights
st.subheader("Cycle Progress Insights")

if active_cycle and metrics:
    total_users = metrics.get('total_users', 0)
    pending_requests = metrics.get('pending_requests', 0)
    
    if total_users > 0:
        completion_rate = max(0, (total_users - metrics.get('users_with_incomplete', 0)) / total_users * 100)
        st.metric("Overall Completion Rate", f"{completion_rate:.1f}%")
        
        progress_bar = st.progress(completion_rate / 100)
        
        if completion_rate < 50:
            st.warning("⚠️ Completion rate is low. Consider sending reminders.")
        elif completion_rate < 80:
            st.info("📈 Good progress! Keep monitoring completion rates.")
        else:
            st.success("🎯 Excellent completion rate!")

# Phase-specific guidance
st.subheader("Current Phase Guidance")

if current_phase == "Nomination Phase":
    st.info("📝 **Nomination Phase:** Employees are selecting reviewers. Monitor nomination submissions.")
elif current_phase == "Manager Approval Phase":
    st.info("✅ **Approval Phase:** Managers are reviewing nominations. Follow up on pending approvals.")
elif current_phase == "Feedback Collection Phase":
    st.info("📋 **Collection Phase:** Reviewers are completing feedback. Send reminders to boost completion rates.")
elif current_phase == "Results Processing Phase":
    st.info("📊 **Results Phase:** Compile and share results with employees.")
elif current_phase == "Cycle Complete":
    st.success("🎉 **Cycle Complete:** Consider starting a new cycle or reviewing process improvements.")
else:
    st.warning("⚠️ **No Active Cycle:** Create a new review cycle to begin the feedback process.")

# Quick actions
st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("👥 Manage Employees"):
        st.switch_page("screens/hr/manage_employees.py")

with col2:
    if st.button("📧 Send Reminders"):
        st.switch_page("screens/hr/send_reminders.py")

with col3:
    if pending_users:
        st.write(f"📊 {len(pending_users)} users need follow-up")