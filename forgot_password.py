import streamlit as st

st.title("Reset Password")

st.info("🚧 Password reset functionality coming soon!")
st.write("Please contact your system administrator for password reset assistance.")

with st.form("forgot_password_form"):
    email = st.text_input("Email Address")
    submit_button = st.form_submit_button("Send Reset Link")
    
    if submit_button:
        if email:
            st.info(f"Password reset instructions would be sent to {email}")
            st.write("For now, please contact your administrator.")
        else:
            st.error("Please enter your email address.")