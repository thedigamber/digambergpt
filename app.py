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
import uuid
from PyPDF2 import PdfReader
from gtts import gTTS

# Custom imports
from auth.utils import get_user_db, save_user_db, hash_password

# --- Initialize User Data ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = get_user_db()

# --- Page Config ---
st.set_page_config(
    page_title="DigamberGPT",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Gemini AI Configuration ---
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel("gemini-2.0-flash")
    st.success("✅ Gemini 2.0 Flash loaded successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to load Gemini: {str(e)}")
    model = None

# --- Sentiment Analysis ---
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
        chat_history = st.session_state.users_db[st.session_state.current_user]["chat_history"]
        messages = []
        
        for msg in chat_history[-20:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})
        
        messages.append({"role": "user", "parts": [prompt]})
        
        response = model.generate_content(
            messages,
            generation_config={
                "temperature": 0.9,
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
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {st.secrets['huggingface']['api_token']}"},
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
        else:
            st.error(f"⚠️ Image generation failed with status: {response.status_code}")
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
                if st.session_state.users_db[username]["password"] == hash_password(password):
                    st.session_state.current_user = username
                    st.session_state.page = "chat"
                    
                    # Initialize chat history
                    if "messages" not in st.session_state:
                        st.session_state.messages = st.session_state.users_db[username]["chat_history"].copy()
                        if not st.session_state.messages:
                            welcome_msg = {
                                "role": "assistant",
                                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                                "sentiment": None
                            }
                            st.session_state.messages.append(welcome_msg)
                            st.session_state.users_db[username]["chat_history"].append(welcome_msg)
                            save_user_db(st.session_state.users_db)
                    
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
                st.session_state.users_db[username] = {
                    "password": hash_password(password),
                    "email": email,
                    "chat_history": []
                }
                
                if save_user_db(st.session_state.users_db):
                    st.success("Account created! Please login")
                    time.sleep(1)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error("Failed to save account. Please try again.")

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
            st.session_state.users_db[username]["password"] = hash_password(new_password)
            if save_user_db(st.session_state.users_db):
                st.success("Password updated! Please login")
                time.sleep(1)
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Failed to update password. Please try again.")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# --- Chat Page ---
def chat_page():
    st.title("🤖 DigamberGPT with Sentiment Analysis")
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = st.session_state.users_db[st.session_state.current_user]["chat_history"].copy()
        if not st.session_state.messages:
            welcome_msg = {
                "role": "assistant",
                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                "sentiment": None
            }
            st.session_state.messages.append(welcome_msg)
            st.session_state.users_db[st.session_state.current_user]["chat_history"].append(welcome_msg)
            save_user_db(st.session_state.users_db)
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sentiment"):
                sentiment = msg["sentiment"]
                if sentiment["label"] == "POS":
                    st.markdown(f'<span class="sentiment-positive">😊 Positive ({sentiment["score"]})</span>', unsafe_allow_html=True)
                elif sentiment["label"] == "NEU":
                    st.markdown(f'<span class="sentiment-neutral">😐 Neutral ({sentiment["score"]})</span>', unsafe_allow_html=True)
                elif sentiment["label"] == "NEG":
                    st.markdown(f'<span class="sentiment-negative">😠 Negative ({sentiment["score"]})</span>', unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Your message..."):
        # Check for duplicate message
        if st.session_state.messages and st.session_state.messages[-1]["content"] == prompt:
            st.warning("Duplicate message detected!")
            st.stop()
        
        # Add user message
        user_msg = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_msg)
        st.session_state.users_db[st.session_state.current_user]["chat_history"].append(user_msg)
        
        with st.spinner("💭 Generating response..."):
            if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw"]):
                img_path = generate_image(prompt)
                if img_path:
                    img_msg = {
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})",
                        "sentiment": None
                    }
                    st.session_state.messages.append(img_msg)
                    st.session_state.users_db[st.session_state.current_user]["chat_history"].append(img_msg)
            else:
                response, sentiment = generate_response(prompt)
                ai_msg = {
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                }
                st.session_state.messages.append(ai_msg)
                st.session_state.users_db[st.session_state.current_user]["chat_history"].append(ai_msg)
            
            # Save updated chat history
            save_user_db(st.session_state.users_db)
        
        st.rerun()

    # Sidebar
    with st.sidebar:
        st.header(f"👤 {st.session_state.current_user}")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                "sentiment": None
            }]
            st.session_state.users_db[st.session_state.current_user]["chat_history"] = st.session_state.messages.copy()
            save_user_db(st.session_state.users_db)
            st.rerun()
        
        st.markdown("---")
        st.subheader("🎨 Image Generation Tips")
        st.markdown("""
        - Be specific in descriptions
        - Include style preferences
        - Example: "A futuristic city at night, cyberpunk style"
        """)
        
        st.markdown("---")
        if st.button("📤 Export Chat", use_container_width=True):
            chat_text = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages)
            st.download_button(
                "💾 Download as TXT",
                chat_text,
                file_name=f"digamber_chat_{st.session_state.current_user}.txt"
            )
        
        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.pop("current_user")
            st.session_state.pop("messages", None)
            st.session_state.page = "login"
            st.rerun()

# --- Main App ---
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    # Custom CSS
    st.markdown("""
        <style>
        .stTextInput input {color: #4F8BF9;}
        .stButton button {background-color: #4F8BF9; color: white;}
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
        if "current_user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()

    # APK Download
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
