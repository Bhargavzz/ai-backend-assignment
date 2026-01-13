"""Configuration constants for Streamlit UI"""
import os

# API Configuration

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# File Upload Limits
MAX_FILE_SIZE_MB = 10 * 1024 * 1024  # 10 MB in bytes

# Azure OpenAI Configuration
DEFAULT_API_VERSION = "2024-12-01-preview"
