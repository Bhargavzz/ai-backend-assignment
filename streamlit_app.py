"""
Main Streamlit Application Entry Point
Phase 5: Document AI Assistant with RAG
"""
import streamlit as st
import requests
from ui.config import API_BASE_URL, DEFAULT_API_VERSION
from ui.tab_users import render_users_tab
from ui.tab_documents import render_documents_tab
from ui.tab_chat import render_chat_tab


# page config

st.set_page_config(page_title="AI Agent (RAG)", layout="wide")


# session state initialization
if "azure_config" not in st.session_state:
    st.session_state.azure_config = {
        "endpoint": "",
        "api_key": "",
        "deployment": "",
        "api_version": DEFAULT_API_VERSION
    }



# zure OpenAI Configuration Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")

    endpoint = st.text_input(
        "Azure Endpoint",
        value=st.session_state.azure_config["endpoint"],
        placeholder="https://your-resource.openai.azure.com/"
    )

    api_key = st.text_input(
        "API Key",
        value=st.session_state.azure_config["api_key"],
        type="password",
        placeholder="Your Azure OpenAI API Key"
    )

    deployment = st.text_input(
        "Deployment Name",
        value=st.session_state.azure_config["deployment"],
        placeholder="gpt-4o-mini"
    )

    if st.button("💾 Save Configuration"):
        st.session_state.azure_config = {
            "endpoint": endpoint,
            "api_key": api_key,
            "deployment": deployment,
            "api_version": DEFAULT_API_VERSION
        }
        st.success("✅ Configuration saved!")



st.title("📚 AI Agent with RAG")

# Check Azure OpenAI configuration
config_ok = all([
    st.session_state.azure_config["endpoint"],
    st.session_state.azure_config["api_key"],
    st.session_state.azure_config["deployment"]
])

if config_ok:
    st.success("☑️ Azure OpenAI configuration is set.")
else:
    st.warning("⚠️ Please set the Azure OpenAI configuration in the sidebar.")

# Test API server connectivity
try:
    response = requests.get(f"{API_BASE_URL}/docs", timeout=3)
    if response.status_code == 200:
        st.success("☑️ API server is running.")
except:
    st.error("❌ Cannot connect to API server. Ensure it's running: `uvicorn app.main:app --reload`")


#tabs
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👤 Users", "📄 Documents", "💬 Chat"])

with tab1:
    render_users_tab()

with tab2:
    render_documents_tab()

with tab3:
    render_chat_tab()
                



                        















