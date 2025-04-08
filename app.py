# Fix for distutils import error - must be at VERY TOP
import sys
import setuptools
from distutils import util

# Standard imports
import streamlit as st
import requests
import io
from PIL import Image
import time
import hashlib
import uuid
import os
from PyPDF2 import PdfReader
from gtts import gTTS
import emoji
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Authentication Setup ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        # username: [hashed_password, email]
        "admin": ["8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "admin@example.com"]  # password: "admin"
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Page Config ---
st.set_page_config(
    page_title="DigamberGPT",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Gemini AI Configuration ---
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    st.success("✅ Gemini 2.0 Flash loaded successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to load Gemini: {str(e)}")
    model = None

# --- Sentiment Analysis with Better Model ---
try:
    from transformers import pipeline
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="finiteautomata/bertweet-base-sentiment-analysis",
        tokenizer="finiteautomata/bertweet-base-sentiment-analysis"
    )
    sentiment_enabled = True
    st.success("✅ Sentiment analysis enabled")
except Exception as e:
    sentiment_pipeline = None
    sentiment_enabled = False
    st.warning(f"⚠️ Sentiment analysis disabled: {str(e)}")

def analyze_sentiment(text):
    if not sentiment_enabled:
        return None
    try:
        result = sentiment_pipeline(text[:512])[0]
        return {
            "label": result["label"],
            "score": round(result["score"], 3)
        }
    except Exception as e:
        st.error(f"⚠️ Sentiment analysis failed: {str(e)}")
        return None

# --- Core Functions ---
def generate_response(prompt):
    if not model:
        return "Error: AI model not loaded", None
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 2048
            }
        )
        sentiment = analyze_sentiment(response.text)
        return response.text, sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

def generate_image(prompt):
    try:
        api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers=headers,
            json={"inputs": prompt, "options": {"wait_for_model": True}},
            timeout=30
        )
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        st.error(f"⚠️ Image generation failed: {str(e)}")
        return None

# --- Authentication Pages ---
def login_page():
    st.title("🔐 Login to DigamberGPT")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if username in st.session_state.users_db:
                if st.session_state.users_db[username][0] == hash_password(password):
                    st.session_state.user = username
                    st.session_state.page = "chat"
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid password!")
            else:
                st.error("Username not found")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account"):
            st.session_state.page = "signup"
            st.rerun()
    with col2:
        if st.button("Forgot Password"):
            st.session_state.page = "forgot"
            st.rerun()

def signup_page():
    st.title("📝 Create Account")
    
    with st.form("signup_form"):
        username = st.text_input("Username (min 4 chars)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Sign Up"):
            if username in st.session_state.users_db:
                st.error("Username already exists!")
            elif len(username) < 4:
                st.error("Username too short!")
            elif password != confirm:
                st.error("Passwords don't match!")
            elif len(password) < 8:
                st.error("Password too short (min 8 chars)!")
            else:
                st.session_state.users_db[username] = [hash_password(password), email]
                st.success("Account created! Please login")
                time.sleep(1)
                st.session_state.page = "login"
                st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def forgot_password_page():
    st.title("🔑 Reset Password")
    
    username = st.text_input("Username")
    new_password = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    
    if st.button("Update Password"):
        if username not in st.session_state.users_db:
            st.error("Username not found!")
        elif new_password != confirm:
            st.error("Passwords don't match!")
        elif len(new_password) < 8:
            st.error("Password too short (min 8 chars)!")
        else:
            st.session_state.users_db[username][0] = hash_password(new_password)
            st.success("Password updated! Please login")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# --- Chat Page ---
def chat_page():
    st.title("🤖 DigamberGPT with Sentiment Analysis")
    
    # Chat UI (your original code)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sentiment" in msg and msg["sentiment"]:
                sentiment = msg["sentiment"]
                if sentiment["label"] == "POS":
                    st.markdown(f'<span class="sentiment-positive">😊 Positive ({sentiment["score"]})</span>', unsafe_allow_html=True)
                elif sentiment["label"] == "NEU":
                    st.markdown(f'<span class="sentiment-neutral">😐 Neutral ({sentiment["score"]})</span>', unsafe_allow_html=True)
                elif sentiment["label"] == "NEG":
                    st.markdown(f'<span class="sentiment-negative">😠 Negative ({sentiment["score"]})</span>', unsafe_allow_html=True)

    if prompt := st.chat_input("Your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("💭 Analyzing..."):
            if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw"]):
                img_path = generate_image(prompt)
                if img_path:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})"
                    })
            else:
                response, sentiment = generate_response(prompt)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                })
        st.rerun()

    # Your original sidebar controls
    with st.sidebar:
        st.header(f"👤 {st.session_state.user}")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.subheader("Image Options")
        img_style = st.selectbox("🎨 Style", ["Realistic", "Anime", "Ghibli", "Cyberpunk"], index=0)
        
        st.markdown("---")
        if st.button("📤 Export Chat", use_container_width=True):
            chat_text = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages)
            st.download_button("💾 Download as TXT", chat_text, file_name="digamber_chat.txt", use_container_width=True)
        
        st.markdown("---")
        tts_enabled = st.toggle("🔊 Enable Text-to-Speech")
        if tts_enabled and st.session_state.messages:
            last_msg = st.session_state.messages[-1]["content"]
            tts = gTTS(text=last_msg, lang='en')
            tts.save("temp_audio.mp3")
            st.audio("temp_audio.mp3")
        
        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.pop("user")
            st.session_state.page = "login"
            st.rerun()

# --- Main App Flow ---
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    st.markdown("""
        <style>
        .stTextInput input {color: #4F8BF9;}
        .stButton button {background-color: #4F8BF9; color: white;}
        .chat-message {padding: 10px; border-radius: 10px; margin: 5px 0;}
        .user-message {background-color: #2a2a2a; color: white;}
        .bot-message {background-color: #1a1a1a; color: #39ff14;}
        .sentiment-positive {color: green;}
        .sentiment-neutral {color: blue;}
        .sentiment-negative {color: red;}
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "forgot":
        forgot_password_page()
    elif st.session_state.page == "chat":
        if "user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()

    # APK Download Section
    st.markdown("---")
    st.markdown("### 📱 Mobile App")
    st.markdown("""
    <a href="https://drive.google.com/uc?export=download&id=1cdDIcHpQf-gwX9y9KciIu3tNHrhLpoOr" target="_blank">
    <button style='
        background-color: #4F8BF9;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        margin: 10px 0;
    '>Download Android APK</button>
    </a>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
