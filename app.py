import streamlit as st
from google.generativeai import configure, GenerativeModel

# Load API key from Streamlit secrets
API_KEY = st.secrets["gemini"]["api_key"]

# Configure Gemini API
configure(api_key=API_KEY)
model = GenerativeModel("gemini-2.0-flash")

# Page Config
st.set_page_config(page_title="DigamberGPT", page_icon="🤖", layout="wide")

# Neon Style CSS
st.markdown("""
    <style>
    body {
        background-color: #0d0d0d;
        color: #39ff14;
    }
    .stApp {
        background-color: #0d0d0d;
    }
    h1 {
        color: #ff00ff;
        text-align: center;
        text-shadow: 2px 2px 10px #ff00ff;
    }
    input[type="text"] {
        background-color: #1a1a1a !important;
        color: #39ff14 !important;
        border: 2px solid #39ff14 !important;
        padding: 10px;
    }
    .stButton>button {
        background-color: #ff00ff;
        color: white;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #39ff14;
        color: black;
    }
    .stChatMessage {
        background-color: #1a1a1a;
        border-left: 4px solid #39ff14;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>🚀 DigamberGPT 🤖</h1>", unsafe_allow_html=True)

# Initialize session state for input clearing
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Chat UI
user_input = st.text_input("Ask me anything!", key="user_input")

if user_input:
    response = model.generate_content(user_input)
    st.markdown(f'<div class="stChatMessage">{response.text}</div>', unsafe_allow_html=True)
    
    # Clear input field and rerun to close keyboard
    st.session_state.user_input = ""
    st.experimental_rerun()
