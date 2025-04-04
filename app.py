import streamlit as st
import toml
from google.generativeai import configure, GenerativeModel

# Load API key from secret.toml
secrets = toml.load("secret.toml")
API_KEY = secrets["gemini"]["api_key"]

# Configure Gemini API
configure(api_key=API_KEY)
model = GenerativeModel("gemini-2.0-flash")

# Page Configuration
st.set_page_config(page_title="DigamberGPT", page_icon="🤖", layout="wide")

# Custom CSS for neon look
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
    .stTextInput, .stTextArea {
        background-color: #1a1a1a !important;
        color: #39ff14 !important;
        border: 2px solid #39ff14 !important;
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

# Chat UI
user_input = st.text_input("Ask me anything!", "")

if user_input:
    response = model.generate_content(user_input)
    st.markdown(f'<div class="stChatMessage">{response.text}</div>', unsafe_allow_html=True)
