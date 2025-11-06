import streamlit as st
from services.auth_service import authenticate_user, check_user_needs_password_setup

st.title("360° Feedback System")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Step 1: Email entry
    if "email_entered" not in st.session_state:
        st.session_state["email_entered"] = False
    
    if not st.session_state["email_entered"]:
        st.subheader("Login")
        with st.form("email_form"):
            email = st.text_input("Email Address")
            submit_email = st.form_submit_button("Continue")
            
            if submit_email:
                if email:
                    # Check if user exists and needs password setup
                    needs_setup, user_data = check_user_needs_password_setup(email)
                    
                    if user_data:  # User exists
                        st.session_state["login_email"] = email
                        st.session_state["email_entered"] = True
                        st.session_state["needs_password_setup"] = needs_setup
                        st.rerun()
                    else:
                        st.error("Email not found in the system. Please contact your administrator.")
                else:
                    st.error("Please enter your email address.")
    
    else:
        # Step 2: Password entry or setup
        email = st.session_state["login_email"]
        needs_setup = st.session_state.get("needs_password_setup", False)
        
        if needs_setup:
            # First time login - password setup
            st.subheader(f"Welcome! Set up your password")
            st.info(f"Email: {email}")
            
            with st.form("password_setup_form"):
                password = st.text_input("Create Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_setup = st.form_submit_button("Set Password")
                
                if submit_setup:
                    if not password:
                        st.error("Please enter a password.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        from services.auth_service import create_user_password
                        if create_user_password(email, password):
                            st.success("Password created successfully! Please login.")
                            # Reset and go to login
                            st.session_state["email_entered"] = False
                            st.session_state["needs_password_setup"] = False
                            st.rerun()
                        else:
                            st.error("Error creating password. Please try again.")
        
        else:
            # Regular login
            st.subheader("Enter Password")
            st.info(f"Email: {email}")
            
            with st.form("password_form"):
                password = st.text_input("Password", type="password")
                col1, col2 = st.columns(2)
                
                with col1:
                    submit_login = st.form_submit_button("Login")
                with col2:
                    reset_password = st.form_submit_button("Forgot Password?")
                
                if submit_login:
                    if password:
                        success, error_message, user_data = authenticate_user(email, password)
                        
                        if success:
                            st.session_state["authenticated"] = True
                            st.session_state["email"] = email
                            st.session_state["user_data"] = user_data
                            st.session_state["user_roles"] = user_data["roles"]
                            # Clear login session data
                            st.session_state["email_entered"] = False
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(error_message)
                    else:
                        st.error("Please enter your password.")
                
                if reset_password:
                    st.info("Password reset functionality coming soon. Please contact your administrator.")
        
        # Back button
        if st.button("← Back to Email Entry"):
            st.session_state["email_entered"] = False
            st.rerun()
    
else:
    user_data = st.session_state.get("user_data", {})
    st.success(f"Welcome back, {user_data.get('first_name', 'User')}!")
    st.info("Use the navigation menu to access the different sections of the application.")