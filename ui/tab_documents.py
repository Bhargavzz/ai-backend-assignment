"""Documents tab - Document upload and management"""
import streamlit as st
import requests
from .config import API_BASE_URL, MAX_FILE_SIZE_MB


def render_documents_tab():
    """Render the Documents tab UI"""
    
    # Check if user selected
    if "current_user_id" not in st.session_state:
        st.warning("Please select or create a user in the Users tab.")
        return
    
    current_user = st.session_state.current_user_id
    st.info(f"Current User ID: {current_user}")

    st.subheader("Upload Document (PDF/Image)")

    # Size limit info
    st.markdown("**Note:** Maximum file size is 10 MB.")

    uploaded_file = st.file_uploader(
        "Choose a file (max 10 MB)",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        file_size = uploaded_file.size

        if file_size > MAX_FILE_SIZE_MB:
            st.error("File size exceeds 10 MB limit.")
        else:
            st.info(f"File '{uploaded_file.name}' of size {file_size/(1024*1024):.2f} MB ready for upload.")

            if st.button("Upload and Index", type="primary"):
                with st.spinner("Uploading"):
                    try:
                        # Upload doc
                        files = {
                            "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                        }
                        data = {
                            "title": uploaded_file.name,
                            "user_id": current_user
                        }

                        response = requests.post(
                            f"{API_BASE_URL}/documents/upload",
                            files=files,
                            data=data
                        )

                        if response.status_code >= 200 and response.status_code < 300:
                            doc_data = response.json()
                            doc_id = doc_data["document_id"]
                            st.success(f"☑️ Uploaded! Doc ID: {doc_id}")
                            
                            # Auto-index
                            with st.spinner("Indexing..."):
                                index_response = requests.post(
                                    f"{API_BASE_URL}/documents/index",
                                    json={"document_ids": [doc_id]}
                                )

                                if index_response.status_code >= 200 and index_response.status_code < 300:
                                    st.success("☑️ Indexing complete!")
                                else:
                                    st.error(f"Indexing failed: {index_response.text}")
                                    st.info("Use document list below to retry indexing")
                        else:
                            st.error(f"Upload failed: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.subheader("My Documents")

    # Refresh button
    if st.button("Refresh Document List"):
        st.rerun()
    
    # Fetch user's documents
    try:
        response = requests.get(f"{API_BASE_URL}/users/{current_user}/documents")
        if response.status_code >= 200 and response.status_code < 300:
            docs = response.json()
            
            if not docs:
                st.info("No documents yet. Upload your first document above!")
            else:
                for doc in docs:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"**{doc['title']}** (ID: {doc['id']})")
                    
                    with col2:
                        if st.button("📊 Index", key=f"index_{doc['id']}"):
                            with st.spinner("Indexing..."):
                                try:
                                    idx_resp = requests.post(
                                        f"{API_BASE_URL}/documents/index",
                                        json={"document_ids": [doc['id']]}
                                    )
                                    if idx_resp.status_code == 200:
                                        st.success("✅ Indexed!")
                                    else:
                                        st.error(f"❌ Failed: {idx_resp.text}")
                                except Exception as e:
                                    st.error(f"❌ {str(e)}")
                    
                    st.markdown("---")
        else:
            st.error("Failed to load documents")
    except Exception as e:
        st.error(f"Error: {str(e)}")
