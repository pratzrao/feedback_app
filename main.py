import streamlit as st
from services.db_helper import get_manager_level_from_designation

def logout():
    """Logs the user out and redirects to the login page."""
    st.session_state["authenticated"] = False
    st.session_state["email"] = None
    st.session_state["user_data"] = None
    st.session_state["user_roles"] = []
    st.rerun()

def has_role(role_name):
    """Check if current user has a specific role."""
    user_roles = st.session_state.get("user_roles", [])
    return any(role["role_name"] == role_name for role in user_roles)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_roles" not in st.session_state:
    st.session_state["user_roles"] = []

# Pages
pages = {
    "Login": st.Page("login.py", title="Log in", icon=":material/login:", default=True),
    "Password Setup": st.Page("password_setup.py", title="Set Password", icon=":material/key:"),
    "Forgot Password": st.Page("forgot_password.py", title="Reset Password", icon=":material/lock_reset:"),
    "Logout": st.Page(logout, title="Log out", icon=":material/logout:"),
}

# Role-based sections
if st.session_state["authenticated"]:
    st.sidebar.write(f"Logged in as: {st.session_state['user_data']['first_name']} {st.session_state['user_data']['last_name']}")
    
    if has_role("super_admin"):
        # Super admin - full access
        pg = st.navigation({
            "Dashboard": [
                st.Page("screens/hr/dashboard.py", title="Analytics Dashboard", icon=":material/dashboard:"),
            ],
            "Management": [
                st.Page("screens/manager/approve_nominations.py", title="Approve Nominations", icon=":material/approval:"),
                st.Page("screens/hr/manage_employees.py", title="Manage Employees", icon=":material/people:"),
                st.Page("screens/hr/send_reminders.py", title="Send Reminders", icon=":material/mail:"),
            ],
            "My Feedback": [
                st.Page("screens/employee/request_feedback.py", title="Request Feedback", icon=":material/rate_review:"),
                st.Page("screens/employee/my_feedback.py", title="My Feedback", icon=":material/feedback:"),
                st.Page("screens/employee/my_reviews.py", title="Reviews to Complete", icon=":material/assignment:"),
                st.Page("screens/employee/provide_feedback.py", title="Provide Feedback", icon=":material/edit:"),
            ],
            "Admin": [
                st.Page("screens/admin/user_management.py", title="User Management", icon=":material/admin_panel_settings:"),
                st.Page("screens/admin/system_settings.py", title="System Settings", icon=":material/settings:"),
            ],
            "Account": [pages["Logout"]],
        })
    elif has_role("hr"):
        # HR - dashboard and management + own feedback
        pg = st.navigation({
            "Dashboard": [
                st.Page("screens/hr/dashboard.py", title="Analytics Dashboard", icon=":material/dashboard:"),
            ],
            "Management": [
                st.Page("screens/manager/approve_nominations.py", title="Approve Nominations", icon=":material/approval:"),
                st.Page("screens/hr/manage_employees.py", title="Manage Employees", icon=":material/people:"),
                st.Page("screens/hr/send_reminders.py", title="Send Reminders", icon=":material/mail:"),
            ],
            "My Feedback": [
                st.Page("screens/employee/request_feedback.py", title="Request Feedback", icon=":material/rate_review:"),
                st.Page("screens/employee/my_feedback.py", title="My Feedback", icon=":material/feedback:"),
                st.Page("screens/employee/my_reviews.py", title="Reviews to Complete", icon=":material/assignment:"),
                st.Page("screens/employee/provide_feedback.py", title="Provide Feedback", icon=":material/edit:"),
            ],
            "Account": [pages["Logout"]],
        })
    else:
        # Regular employee + managers (for approval functions)
        nav_sections = {
            "My Feedback": [
                st.Page("screens/employee/request_feedback.py", title="Request Feedback", icon=":material/rate_review:"),
                st.Page("screens/employee/my_feedback.py", title="My Feedback", icon=":material/feedback:"),
                st.Page("screens/employee/my_reviews.py", title="Reviews to Complete", icon=":material/assignment:"),
                st.Page("screens/employee/provide_feedback.py", title="Provide Feedback", icon=":material/edit:"),
            ],
            "Account": [pages["Logout"]],
        }
        
        # Add manager approval for team leads and above
        user_data = st.session_state.get("user_data", {})
        manager_level = get_manager_level_from_designation(user_data.get("designation", ""))
        if manager_level >= 1:  # Team Lead or above
            nav_sections["Team Management"] = [
                st.Page("screens/manager/approve_nominations.py", title="Approve Team Nominations", icon=":material/approval:"),
            ]
        
        pg = st.navigation(nav_sections)
else:
    # Not authenticated - login options only
    pg = st.navigation([pages["Login"], pages["Password Setup"], pages["Forgot Password"]])

pg.run()