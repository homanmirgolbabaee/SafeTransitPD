import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import requests
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Page Configuration ===
st.set_page_config(
    page_title="StudentGuide.AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Custom CSS ===
# === Custom CSS for Dark Theme ===
st.markdown("""
    <style>
    /* Main Layout */
    .main {
        padding: 0rem 1rem;
        background-color: #0e1117;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        background-color: #1e2127;
        border: 1px solid #2e3441;
        color: #fff;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2e3441;
        border-color: #3e4451;
    }
    
    /* Card Styling */
    .card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0px;
        background-color: #1e2127;
        border: 1px solid #2e3441;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: #ffffff;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.4);
    }
    
    /* Metric Card Styling */
    .metric-card {
        background-color: #1e2127;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin: 10px 0px;
        border: 1px solid #2e3441;
        color: #ffffff;
    }
    
    /* Chat Message Styling */
    .chat-message {
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: #2e3441;
        color: #ffffff;
        border: 1px solid #3e4451;
    }
    
    .chat-message-bot {
        background-color: #1e2127;
    }
    
    .chat-message-user {
        background-color: #2e3441;
    }
    
    /* Resource Card Styling */
    .resource-card {
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
        background-color: #1e2127;
        border: 1px solid #2e3441;
        color: #ffffff;
        transition: transform 0.2s ease;
    }
    
    .resource-card:hover {
        transform: translateY(-2px);
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #ffffff !important;
    }
    
    /* Text */
    p {
        color: #c8c9cb !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1e2127;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #2e3441;
        color: #ffffff;
        border: 1px solid #3e4451;
    }
    
    /* Selectbox */
    .stSelectbox>div>div {
        background-color: #2e3441;
        color: #ffffff;
        border: 1px solid #3e4451;
    }
    
    /* File Uploader */
    .stFileUploader>div>div {
        background-color: #2e3441;
        color: #ffffff;
        border: 1px solid #3e4451;
    }
    
    /* Metrics */
    .stMetric>div {
        background-color: #1e2127;
        color: #ffffff;
    }
    
    /* Tabs */
    .stTabs>div>div>div {
        background-color: #1e2127;
        color: #ffffff;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e2127;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2e3441;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3e4451;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .card, .metric-card, .resource-card {
        animation: fadeIn 0.3s ease-out;
    }
    </style>
""", unsafe_allow_html=True)

# === Session State Management ===
class SessionState:
    def init_state():
        if 'language' not in st.session_state:
            st.session_state.language = 'english'
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None

# === LLM Integration ===
class LLMHandler:
    def __init__(self):
        self.api_key = os.getenv('LLAMA_API_KEY')
    
    def process_query(self, query: str) -> str:
        """Process user query through LLM"""
        try:
            # Placeholder for LLM integration
            return f"This is a placeholder response for: {query}"
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            return None

# === Analytics Handler ===
class AnalyticsHandler:
    @staticmethod
    def track_event(event_name: str, metadata: Dict = None):
        """Track user interactions"""
        timestamp = datetime.now().isoformat()
        event_data = {
            'timestamp': timestamp,
            'event': event_name,
            'metadata': metadata or {}
        }
        # Save to session state for demo
        if 'analytics' not in st.session_state:
            st.session_state.analytics = []
        st.session_state.analytics.append(event_data)

    @staticmethod
    def get_metrics():
        """Get usage analytics"""
        if 'analytics' in st.session_state:
            return {
                'total_interactions': len(st.session_state.analytics),
                'recent_events': st.session_state.analytics[-5:]
            }
        return {'total_interactions': 0, 'recent_events': []}

# === Main Page Renderers ===
def render_home():
    st.title("Welcome to StudentGuide.AI 🎓")
    
    # Quick Stats
    col1, col2, col3 = st.columns(3)
    metrics = AnalyticsHandler.get_metrics()
    
    with col1:
        st.markdown("""
            <div class="card">
            <h3>💬 Chat Assistant</h3>
            <p>Get instant help with your questions</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Start Chat"):
            st.session_state.page = "chat"
            AnalyticsHandler.track_event("chat_opened")

    with col2:
        st.markdown("""
            <div class="card">
            <h3>📄 Document Analysis</h3>
            <p>Upload and analyze your documents</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Upload Document"):
            st.session_state.page = "documents"
            AnalyticsHandler.track_event("document_section_opened")

    with col3:
        st.markdown("""
            <div class="card">
            <h3>📚 Resources</h3>
            <p>Access student resources and guides</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Browse Resources"):
            st.session_state.page = "resources"
            AnalyticsHandler.track_event("resources_opened")

def render_chat():
    st.header("Chat Assistant 💬")
    
    # Chat interface
    llm = LLMHandler()
    
    # Display chat history
    for message in st.session_state.chat_history:
        message_class = "chat-message-bot" if message['is_bot'] else "chat-message-user"
        st.markdown(f"""
            <div class="chat-message {message_class}">
                <b>{'🤖 Bot' if message['is_bot'] else '👤 You'}:</b> {message['text']}
            </div>
        """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.text_input("Type your message:", key="chat_input")
    col1, col2 = st.columns([6,1])
    with col1:
        user_input = st.text_input("Type your message...", key="chat_input")
    with col2:
        send_button = st.button("Send", key="send_msg")
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'text': user_input,
            'is_bot': False
        })
        
        # Get bot response
        with st.spinner("Processing..."):
            response = llm.process_query(user_input)
            st.session_state.chat_history.append({
                'text': response,
                'is_bot': True
            })
        
        # Track interaction
        AnalyticsHandler.track_event("chat_message_sent")
        
        # Clear input and refresh
        st.session_state.chat_input = ""
        st.experimental_rerun()

def render_documents():
    st.header("Document Analysis 📄")
    
    uploaded_file = st.file_uploader("Upload your document", type=['pdf', 'docx', 'txt'])
    if uploaded_file:
        st.success("File uploaded successfully!")
        
        # Display document analysis options
        analysis_type = st.selectbox(
            "Select analysis type:",
            ["Summary", "Translation", "Key Points Extraction"]
        )
        
        if st.button("Analyze Document"):
            with st.spinner("Analyzing document..."):
                # Placeholder for document analysis
                st.markdown("""
                    <div class="card">
                    <h4>Analysis Results</h4>
                    <p>Document analysis placeholder results...</p>
                    </div>
                """, unsafe_allow_html=True)
                AnalyticsHandler.track_event("document_analyzed")

def render_resources():
    st.header("Student Resources 📚")
    
    # Resource categories
    categories = {
        "Housing": [
            {"title": "Finding Accommodation", "description": "Guide to student housing"},
            {"title": "Rental Contracts", "description": "Understanding Italian rental agreements"}
        ],
        "Academic": [
            {"title": "Course Registration", "description": "Step-by-step registration guide"},
            {"title": "Study Tips", "description": "Effective study methods"}
        ],
        "Administrative": [
            {"title": "Visa Process", "description": "Student visa application guide"},
            {"title": "Healthcare", "description": "Accessing medical services"}
        ]
    }
    
    category = st.selectbox("Select Category:", list(categories.keys()))
    
    for resource in categories[category]:
        st.markdown(f"""
            <div class="resource-card">
                <h4>{resource['title']}</h4>
                <p>{resource['description']}</p>
            </div>
        """, unsafe_allow_html=True)

def render_analytics():
    st.header("Analytics Dashboard 📊")
    
    metrics = AnalyticsHandler.get_metrics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h4>Total Interactions</h4>
            </div>
        """, unsafe_allow_html=True)
        st.metric("Total Interactions", metrics['total_interactions'])
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h4>Recent Activity</h4>
            </div>
        """, unsafe_allow_html=True)
        for event in metrics['recent_events']:
            st.write(f"Event: {event['event']} at {event['timestamp']}")

# === Main Application ===
def main():
    # Initialize session state
    SessionState.init_state()
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Go to",
            ["Home", "Chat", "Documents", "Resources", "Analytics"]
        )
    
    # Main content
    if page == "Home":
        render_home()
    elif page == "Chat":
        render_chat()
    elif page == "Documents":
        render_documents()
    elif page == "Resources":
        render_resources()
    elif page == "Analytics":
        render_analytics()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state.clear()