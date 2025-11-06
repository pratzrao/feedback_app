import streamlit as st
from services.auth_service import check_user_needs_password_setup, create_user_password

st.title("Set Up Your Password")

with st.form("password_setup_form"):
    email = st.text_input("Email Address")
    password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    submit_button = st.form_submit_button("Set Password")
    
    if submit_button:
        if not email:
            st.error("Please enter your email address.")
        elif not password:
            st.error("Please enter a password.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters long.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            # Check if user exists and needs password setup
            needs_setup, user_data = check_user_needs_password_setup(email)
            
            if needs_setup:
                if create_user_password(email, password):
                    st.success("Password set successfully! You can now log in.")
                    st.info("👆 Click 'Log in' in the navigation to access the system.")
                else:
                    st.error("Error setting password. Please try again.")
            else:
                st.error("Email not found or password already set. Please contact your administrator.")

st.markdown("---")
st.info("**Note:** This option is only for first-time users who need to set up their password. If you already have a password, use the 'Log in' option instead.")