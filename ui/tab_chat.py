"""Chat tab - AI-powered chat interface"""
import streamlit as st
import requests
from .config import API_BASE_URL


def render_chat_tab():
    """Render the Chat tab UI"""
    
    # Check if user selected
    if "current_user_id" not in st.session_state:
        st.warning("Please select or create a user in the Users tab.")
        return
    
    st.subheader("Chat with AI Agent")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            # Show sources if available
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for src in message["sources"]:
                            st.markdown(
                                f"- **Doc ID {src['doc_id']}**, "
                                f"Chunk {src['chunk_id']} "
                                f"(Score: {src['similarity_score']:.3f})"
                            )

    # Chat input
    user_query = st.chat_input("Type your question here...")

    if user_query:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_query
        })

        # Display user message
        with st.chat_message("user"):
            st.write(user_query)

        # Call AI agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/ai/ask",
                        json={
                            "query": user_query,
                            "user_id": st.session_state.current_user_id
                        },
                        timeout=30
                    )

                    if response.status_code >= 200 and response.status_code < 300:
                        ai_data = response.json()
                        answer = ai_data["answer"]
                        sources = ai_data.get("sources", [])

                        # Display answer
                        st.write(answer)

                        # Display sources
                        if sources:
                            with st.expander("📚 Sources"):
                                for source in sources:
                                    st.markdown(
                                        f"- **Doc ID {source['doc_id']}**, "
                                        f"Chunk {source['chunk_id']} "
                                        f"(Score: {source['similarity_score']:.3f})"
                                    )

                        # Add to chat history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                    else:
                        error_msg = f"Error: {response.text}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                except Exception as e:
                    error_msg = f"Exception: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Clear chat history
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
