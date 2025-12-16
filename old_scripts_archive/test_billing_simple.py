import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    st.set_page_config(page_title="Simple Billing Test", layout="wide")
    
    st.title("Simple Billing Dashboard Test")
    
    # Test session state
    st.subheader("Session State Debug")
    
    # Show all session state
    st.write("**All Session State:**")
    for key, value in st.session_state.items():
        st.write(f"- {key}: {value}")
    
    st.markdown("---")
    
    # Test user authentication
    current_user = st.session_state.get('authenticated_user')
    user_email = current_user.get('email', '') if current_user else ''
    
    st.subheader("User Authentication Test")
    st.write(f"**Current User:** {current_user}")
    st.write(f"**User Email:** {user_email}")
    
    # Test access control logic
    st.subheader("Access Control Test")
    if user_email.startswith('admin@') or user_email.startswith('harpreet@'):
        st.success("✅ ACCESS GRANTED - User has billing dashboard access")
        st.write("User email starts with 'admin@' or 'harpreet@'")
        
        # Simple billing content
        st.subheader("Billing Dashboard Content")
        st.info("This is where the billing dashboard would appear")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Billing", "$12,345")
        with col2:
            st.metric("Pending", "$2,345")
        with col3:
            st.metric("Processed", "$10,000")
            
    else:
        st.error("❌ ACCESS DENIED - User does not have billing dashboard access")
        st.write(f"User email '{user_email}' does not start with 'admin@' or 'harpreet@'")
        
    st.markdown("---")
    
    # Manual email test
    st.subheader("Manual Email Test")
    test_email = st.text_input("Enter email to test access:", value=user_email)
    if st.button("Test Access"):
        if test_email.startswith('admin@') or test_email.startswith('harpreet@'):
            st.success(f"✅ Email '{test_email}' would have access")
        else:
            st.error(f"❌ Email '{test_email}' would NOT have access")

if __name__ == "__main__":
    main()