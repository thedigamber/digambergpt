# Core imports
import streamlit as st
import requests
import io
from PIL import Image
import uuid
from dotenv import load_dotenv
import os
import sqlite3
import hashlib
import smtplib
from email.mime.text import MIMEText
import random
import string
from gtts import gTTS
from PyPDF2 import PdfReader
import emoji
import time

# Load environment variables
load_dotenv()

# Initialize database
def init_db():
    conn = sqlite3.connect('auth.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                reset_token TEXT,
                token_expiry TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_reset_email(email, token):
    try:
        reset_link = f"http://localhost:8501/reset?token={token}"
        message = f"""Click this link to reset your password: {reset_link}"""
        
        msg = MIMEText(message)
        msg['Subject'] = 'Password Reset Request'
        msg['From'] = os.getenv("SMTP_USERNAME")
        msg['To'] = email
        
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Initialize AI components
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-pro")
    ai_enabled = True
except Exception as e:
    st.error(f"Failed to load Gemini: {str(e)}")
    ai_enabled = False

try:
    from transformers import pipeline
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="finiteautomata/bertweet-base-sentiment-analysis"
    )
    sentiment_enabled = True
except Exception as e:
    st.warning(f"Sentiment analysis disabled: {str(e)}")
    sentiment_enabled = False

# AI Functions
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
        st.error(f"Sentiment analysis failed: {str(e)}")
        return None

def generate_response(prompt):
    if not ai_enabled:
        return "AI service is currently unavailable", None
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.9,
                "top_p": 1.0,
                "max_output_tokens": 4096
            }
        )
        sentiment = analyze_sentiment(response.text)
        return f"मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?\n\n{response.text}", sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

def generate_image(prompt):
    try:
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
        
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_path = f"generated_{uuid.uuid4().hex}.png"
            img.save(img_path)
            return img_path
        
        # Fallback
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=30)
        
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
        
    except Exception as e:
        st.error(f"Image generation failed: {str(e)}")
        return None

# UI Components
def login_page():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not username or not password:
                st.error("All fields are required!")
            else:
                hashed_password = hash_password(password)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
                user = c.fetchone()
                
                if user:
                    st.session_state.user = {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2]
                    }
                    st.session_state.page = "chat"
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account"):
            st.session_state.page = "signup"
            st.rerun()
    with col2:
        if st.button("Forgot Password?"):
            st.session_state.page = "forgot"
            st.rerun()

def signup_page():
    st.title("📝 Create Account")
    
    with st.form("signup_form"):
        username = st.text_input("Username", max_chars=50)
        email = st.text_input("Email", max_chars=100)
        password = st.text_input("Password", type="password", max_chars=50)
        confirm_password = st.text_input("Confirm Password", type="password", max_chars=50)
        submitted = st.form_submit_button("Sign Up")
        
        if submitted:
            if not all([username, email, password, confirm_password]):
                st.error("All fields are required!")
            elif password != confirm_password:
                st.error("Passwords don't match!")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters!")
            else:
                try:
                    hashed_password = hash_password(password)
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                              (username, email, hashed_password))
                    conn.commit()
                    st.success("Account created successfully! Please login.")
                    time.sleep(2)
                    st.session_state.page = "login"
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    if "username" in str(e):
                        st.error("Username already exists!")
                    elif "email" in str(e):
                        st.error("Email already registered!")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def forgot_password_page():
    st.title("🔑 Forgot Password")
    
    tab1, tab2 = st.tabs(["Request Reset", "Reset Password"])
    
    with tab1:
        with st.form("request_reset_form"):
            email = st.text_input("Registered Email")
            submitted = st.form_submit_button("Send Reset Link")
            
            if submitted:
                if not email:
                    st.error("Email is required!")
                else:
                    c = conn.cursor()
                    c.execute("SELECT * FROM users WHERE email=?", (email,))
                    user = c.fetchone()
                    
                    if user:
                        token = generate_reset_token()
                        expiry = time.time() + 3600  # 1 hour from now
                        
                        c.execute("UPDATE users SET reset_token=?, token_expiry=? WHERE email=?",
                                  (token, expiry, email))
                        conn.commit()
                        
                        if send_reset_email(email, token):
                            st.success("Password reset link sent to your email!")
                        else:
                            st.error("Failed to send reset email. Please try again.")
                    else:
                        st.error("Email not found in our system")
    
    with tab2:
        with st.form("reset_password_form"):
            token = st.text_input("Reset Token")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Reset Password")
            
            if submitted:
                if not all([token, new_password, confirm_password]):
                    st.error("All fields are required!")
                elif new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters!")
                else:
                    current_time = time.time()
                    c = conn.cursor()
                    c.execute("SELECT * FROM users WHERE reset_token=? AND token_expiry > ?",
                              (token, current_time))
                    user = c.fetchone()
                    
                    if user:
                        hashed_password = hash_password(new_password)
                        c.execute("UPDATE users SET password=?, reset_token=NULL, token_expiry=NULL WHERE id=?",
                                  (hashed_password, user[0]))
                        conn.commit()
                        st.success("Password reset successfully! Please login.")
                        time.sleep(2)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("Invalid or expired token. Please request a new one.")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def chat_page():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
            "sentiment": None
        })

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sentiment" in msg and msg["sentiment"]:
                sentiment = msg["sentiment"]
                sentiment_emoji = "😊" if sentiment["label"] == "POS" else "😐" if sentiment["label"] == "NEU" else "😠"
                st.caption(f"{sentiment_emoji} {sentiment['label']} ({sentiment['score']})")

    if prompt := st.chat_input("Your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("💭 Thinking..."):
            if any(word in prompt.lower() for word in ["image", "picture", "photo"]):
                img_path = generate_image(prompt)
                if img_path:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})",
                        "sentiment": None
                    })
                    st.rerun()
            else:
                response, sentiment = generate_response(prompt)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                })
                st.rerun()

# Main App Flow
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "forgot":
        forgot_password_page()
    elif st.session_state.page == "chat":
        if "user" in st.session_state:
            chat_page()
        else:
            st.warning("Please login first")
            st.session_state.page = "login"
            st.rerun()

    if st.session_state.page == "chat":
        with st.sidebar:
            st.title(f"👤 {st.session_state.user['username']}")
            
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
                
            st.markdown("---")
            st.markdown("### 🎨 Image Generation")
            st.markdown("Use keywords like 'image', 'picture' or 'generate'")
            
            st.markdown("---")
            if st.button("🔒 Logout"):
                st.session_state.pop("user", None)
                st.session_state.page = "login"
                st.rerun()

if __name__ == "__main__":
    main()
