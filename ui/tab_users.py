"""Users tab - User creation and selection"""
import streamlit as st
import requests
from .config import API_BASE_URL


def render_users_tab():
    """Render the Users tab UI"""
    
    st.subheader("Create User")

    col1, col2 = st.columns([2, 1])
    with col1:
        new_username = st.text_input("Username", placeholder="Enter username")
        new_email = st.text_input("Email", placeholder="Enter email")
    
    with col2:
        st.write("")  # spacing
        st.write("")  # spacing
        if st.button("Create User"):
            if new_username and new_email:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/users/",
                        json={"username": new_username, "email": new_email},
                        timeout=5
                    )
                    if response.status_code >= 200 and response.status_code < 300:
                        user_data = response.json()
                        st.success(f"User created! User ID: {user_data['id']}")
                        st.session_state.current_user_id = user_data['id']
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Exception: {str(e)}")
            else:
                st.warning("Please provide both username and email.")

    st.markdown("---")

    # Select existing user
    st.subheader("Select Existing User")
    user_id_input = st.number_input(
        "User ID",
        min_value=1,
        value=st.session_state.get("current_user_id", 1),
    )

    if st.button("Load User"):
        # Validate user exists by checking their documents endpoint
        try:
            response = requests.get(
                f"{API_BASE_URL}/users/{user_id_input}/documents",
                timeout=5
            )
            if response.status_code >= 200 and response.status_code < 300:
                st.session_state.current_user_id = user_id_input
                st.success(f"User {user_id_input} selected")
            elif response.status_code == 404:
                st.error(f"User ID {user_id_input} does not exist")
            else:
                st.error(f"Error validating user: {response.text}")
        except Exception as e:
            st.error(f"Failed to validate user: {str(e)}")
