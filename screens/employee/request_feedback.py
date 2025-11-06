import streamlit as st
from services.db_helper import (
    get_users_for_selection, 
    create_feedback_requests_with_approval,
    check_external_stakeholder_permission,
    get_active_review_cycle
)

st.title("Request 360° Feedback")

# Check if there's an active review cycle
active_cycle = get_active_review_cycle()
if not active_cycle:
    st.error("No active review cycle found. Please contact HR to start a new feedback cycle.")
    st.stop()

st.info(f"**Active Cycle:** {active_cycle['cycle_name']}")
st.info(f"**Nomination Deadline:** {active_cycle['nomination_deadline']}")

current_user_id = st.session_state["user_data"]["user_type_id"]
user_name = f"{st.session_state['user_data']['first_name']} {st.session_state['user_data']['last_name']}"

# Check external stakeholder permission
can_request_external = check_external_stakeholder_permission(current_user_id)

st.write("Select 3-5 colleagues to provide feedback on your performance:")
st.write("You must select **minimum 3** and **maximum 5** reviewers.")

if can_request_external:
    st.success("✅ As a manager-level employee, you can request feedback from external stakeholders.")
else:
    st.info("ℹ️ Only manager-level and above can request feedback from external stakeholders.")

# Get available reviewers
users = get_users_for_selection(exclude_user_id=current_user_id, requester_user_id=current_user_id)

if not users:
    st.error("No available reviewers found.")
    st.stop()

# Relationship type options
relationship_options = [
    "peer",
    "manager", 
    "direct_reportee",
    "internal_stakeholder"
]

if can_request_external:
    relationship_options.append("external_stakeholder")

# Selection interface
selected_reviewers = []

st.subheader("Available Reviewers")

for user in users:
    if user["is_over_limit"]:
        # Show greyed out
        st.write(f"🚫 ~~{user['name']} ({user['vertical']} - {user['designation']})~~ - *Already nominated 4 times*")
    elif user["is_rejected"]:
        # Show as previously rejected
        st.write(f"❌ ~~{user['name']} ({user['vertical']} - {user['designation']})~~ - *Previously rejected by manager*")
    else:
        # Available for selection
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            selected = st.checkbox("", key=f"user_{user['user_type_id']}")
        
        with col2:
            st.write(f"**{user['name']}**")
            st.write(f"{user['vertical']} - {user['designation']}")
        
        with col3:
            if selected:
                relationship = st.selectbox(
                    "Relationship:",
                    relationship_options,
                    key=f"rel_{user['user_type_id']}",
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                selected_reviewers.append((user['user_type_id'], relationship))
            else:
                st.write(f"Nominations: {user['nomination_count']}/4")

# Validation and submission
st.subheader("Review Your Selection")

if len(selected_reviewers) == 0:
    st.warning("⚠️ Please select at least 3 reviewers.")
elif len(selected_reviewers) < 3:
    st.warning(f"⚠️ You have selected {len(selected_reviewers)} reviewers. Please select at least 3.")
elif len(selected_reviewers) > 5:
    st.error(f"❌ You have selected {len(selected_reviewers)} reviewers. Please select maximum 5.")
else:
    st.success(f"✅ You have selected {len(selected_reviewers)} reviewers.")
    
    # Show summary
    st.write("**Selected Reviewers:**")
    for reviewer_id, relationship in selected_reviewers:
        reviewer_info = next(u for u in users if u['user_type_id'] == reviewer_id)
        st.write(f"• {reviewer_info['name']} - {relationship.replace('_', ' ').title()}")
    
    if st.button("Submit Feedback Requests", type="primary"):
        success, message = create_feedback_requests_with_approval(current_user_id, selected_reviewers)
        
        if success:
            st.success("🎉 Feedback requests submitted successfully!")
            st.info("Your requests have been sent to your manager for approval. You will be notified once they are processed.")
            st.balloons()
        else:
            st.error(f"Error submitting requests: {message}")

st.markdown("---")
st.subheader("How it works:")
st.write("""
1. **Select Reviewers**: Choose 3-5 colleagues who work closely with you
2. **Declare Relationships**: For each person, specify how they work with you
3. **Manager Approval**: Your manager will review and approve your selections
4. **Feedback Collection**: Approved reviewers will receive feedback forms
5. **Anonymous Results**: You'll receive anonymized feedback once completed
""")

# Show nomination limits info
st.info("**Note:** Each person can only receive a maximum of 4 feedback requests to prevent overload.")