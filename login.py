import streamlit as st
from services.auth_service import authenticate_user

st.title("360° Feedback System - Login")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if email and password:
                success, error_message, user_data = authenticate_user(email, password)
                
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["email"] = email
                    st.session_state["user_data"] = user_data
                    st.session_state["user_roles"] = user_data["roles"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(error_message)
                    if "password first" in error_message:
                        st.info("👆 Click 'Set Password' in the navigation to create your password.")
            else:
                st.error("Please enter both email and password.")
    
    st.markdown("---")
    st.info("**First time user?** If you're listed in our system but haven't set a password yet, use the 'Set Password' option above.")
    
else:
    user_data = st.session_state.get("user_data", {})
    st.success(f"Welcome back, {user_data.get('first_name', 'User')}!")
    st.info("Use the navigation menu to access the different sections of the application.")