import streamlit as st
from google.generativeai import configure, GenerativeModel

# Load API key
API_KEY = st.secrets["gemini"]["api_key"]

# Configure Gemini API
configure(api_key=API_KEY)
model = GenerativeModel("gemini-2.0-flash")

# Page Config
st.set_page_config(page_title="DigamberGPT - Neon Chatbot", page_icon="🤖", layout="wide")

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
        font-size: 3em;
        margin-bottom: 20px;
    }
    .stTextInput>div>div>input {
        background-color: #1a1a1a !important;
        color: #39ff14 !important;
        border: 2px solid #39ff14 !important;
        border-radius: 8px;
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
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>🚀 DigamberGPT 🤖</h1>", unsafe_allow_html=True)

# Session state setup
if "history" not in st.session_state:
    st.session_state.history = []

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask me anything!")
    submitted = st.form_submit_button("Send")

# Handle message
if submitted and user_input.strip():
    response = model.generate_content(user_input)
    st.session_state.history.append(("You", user_input))
    st.session_state.history.append(("DigamberGPT", response.text))

# Display messages
for sender, msg in st.session_state.history:
    st.markdown(f"<div class='stChatMessage'><strong>{sender}:</strong> {msg}</div>", unsafe_allow_html=True)
