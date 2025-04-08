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
        # username: [hashed_password, email, chat_history]
        "admin": [
            "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", 
            "admin@example.com",
            []
        ]  # password: "admin"
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
    model = genai.GenerativeModel("gemini-pro")  # Changed to gemini-pro for better performance
    st.success("✅ Gemini Pro loaded successfully!")
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
def generate_response(prompt, chat_history=None):
    if not model:
        return "Error: AI model not loaded", None
    
    try:
        # Build conversation history
        messages = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})
        
        messages.append({"role": "user", "parts": [prompt]})
        
        response = model.generate_content(
            messages,
            generation_config={
                "temperature": 0.9,  # Increased for more creative responses
                "top_p": 1.0,
                "max_output_tokens": 4096
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        
        response_text = f"मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?\n\n{response.text}"
        sentiment = analyze_sentiment(response.text)
        return response_text, sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

def generate_image(prompt):
    try:
        # Try multiple models with fallback
        models = [
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
            "CompVis/stable-diffusion-v1-4"
        ]
        
        for model_name in models:
            try:
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model_name}",
                    headers={"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"},
                    json={
                        "inputs": prompt,
                        "options": {
                            "wait_for_model": True,
                            "guidance_scale": 9,
                            "num_inference_steps": 50
                        }
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img_path = f"generated_{uuid.uuid4().hex}.png"
                    img.save(img_path)
                    return img_path
                
            except Exception as e:
                continue
                
        st.error("⚠️ All image generation attempts failed. Please try again later.")
        return None
        
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
                    # Load user's chat history
                    st.session_state.messages = st.session_state.users_db[username][2]
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
                st.session_state.users_db[username] = [
                    hash_password(password), 
                    email,
                    []  # Initialize empty chat history
                ]
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
    
    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = {
            "role": "assistant",
            "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
            "sentiment": None
        }
        st.session_state.messages.append(welcome_msg)
        # Save to user's history
        st.session_state.users_db[st.session_state.user][2].append(welcome_msg)

    # Display chat messages
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

    # Chat input
    if prompt := st.chat_input("Your message..."):
        # Add user message
        user_msg = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_msg)
        st.session_state.users_db[st.session_state.user][2].append(user_msg)
        
        with st.spinner("💭 Analyzing..."):
            if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw"]):
                img_path = generate_image(prompt)
                if img_path:
                    img_msg = {
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})"
                    }
                    st.session_state.messages.append(img_msg)
                    st.session_state.users_db[st.session_state.user][2].append(img_msg)
            else:
                response, sentiment = generate_response(prompt, st.session_state.messages[-10:])  # Last 10 messages as context
                ai_msg = {
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                }
                st.session_state.messages.append(ai_msg)
                st.session_state.users_db[st.session_state.user][2].append(ai_msg)
        st.rerun()

    # Sidebar controls
    with st.sidebar:
        st.header(f"👤 {st.session_state.user}")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.users_db[st.session_state.user][2] = []
            welcome_msg = {
                "role": "assistant",
                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                "sentiment": None
            }
            st.session_state.messages.append(welcome_msg)
            st.session_state.users_db[st.session_state.user][2].append(welcome_msg)
            st.rerun()
        
        st.markdown("---")
        st.subheader("🎨 Image Generation Tips")
        st.markdown("""
        - Be specific in your description
        - Include style preferences (e.g., 'digital art', 'photorealistic')
        - Example: "A cyberpunk cityscape at night with neon lights, digital art style"
        """)
        
        st.markdown("---")
        if st.button("📤 Export Chat", use_container_width=True):
            chat_text = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages)
            st.download_button(
                "💾 Download as TXT",
                chat_text,
                file_name=f"digamber_chat_{st.session_state.user}.txt",
                use_container_width=True
            )
        
        st.markdown("---")
        tts_enabled = st.toggle("🔊 Enable Text-to-Speech")
        if tts_enabled and st.session_state.messages:
            last_msg = st.session_state.messages[-1]["content"]
            tts = gTTS(text=last_msg, lang='hi' if any(char in last_msg for char in 'अआइईउऊऋएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह') else 'en')
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
    
    # Custom CSS
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

    # Page routing
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
