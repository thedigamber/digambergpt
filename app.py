# Core imports
import streamlit as st
from streamlit_option_menu import option_menu
import requests
import io
from PIL import Image
import time
import uuid
from dotenv import load_dotenv
import os
import sqlite3
import hashlib
import smtplib
from email.mime.text import MIMEText
import random
import string

# Load environment variables
load_dotenv()

# Database setup
conn = sqlite3.connect('auth.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              email TEXT UNIQUE,
              password TEXT)''')
conn.commit()

# Email configuration (use environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# App configuration
st.set_page_config(
    page_title="DigamberGPT Pro",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Authentication functions
def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_reset_email(email, token):
    reset_link = f"http://yourdomain.com/reset?token={token}"
    message = f"""Click this link to reset your password: {reset_link}"""
    
    msg = MIMEText(message)
    msg['Subject'] = 'Password Reset Request'
    msg['From'] = SMTP_USERNAME
    msg['To'] = email
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# AI Functions
def generate_grok_style_response(prompt, chat_history=None):
    """Generate unfiltered, continuous response in Grok style"""
    # This would connect to your self-hosted AI model
    # For demo, we'll use a mock response
    grok_style = """
    मैं DigamberGPT हूँ, सीमाओं से मुक्त AI सहायक। 
    
    """
    
    response = grok_style + f"""
    आपका प्रश्न: {prompt}
    
    मैं इस विषय पर विस्तार से चर्चा कर सकता हूँ। यहाँ पूरी जानकारी है:
    
    - पहला पॉइंट: विषय का मूल विश्लेषण
    - दूसरा पॉइंट: तकनीकी पहलू
    - तीसरा पॉइंट: व्यावहारिक अनुप्रयोग
    - चौथा पॉइंट: वैकल्पिक दृष्टिकोण
    
    क्या आप किसी विशिष्ट पहलू पर और जानकारी चाहेंगे?
    """
    
    return response, None

def generate_image(prompt):
    """Improved image generation with multiple model support"""
    try:
        # Try Stable Diffusion first
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
        
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": prompt}
        )
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_path = f"generated_{uuid.uuid4().hex}.png"
            img.save(img_path)
            return img_path
        
        # Fallback to other model if first fails
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})
        
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
        
    except Exception as e:
        st.error(f"⚠️ Image generation failed: {str(e)}")
        return None

# UI Components
def login_page():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            hashed_password = hash_password(password)
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
            user = c.fetchone()
            
            if user:
                st.session_state.user = user
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Invalid credentials")

    if st.button("Forgot Password?"):
        st.session_state.page = "forgot"
        st.rerun()
        
    if st.button("Create Account"):
        st.session_state.page = "signup"
        st.rerun()

def signup_page():
    st.title("📝 Create Account")
    
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords don't match")
            else:
                try:
                    hashed_password = hash_password(password)
                    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                              (username, email, hashed_password))
                    conn.commit()
                    st.success("Account created! Please login.")
                    st.session_state.page = "login"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username or email already exists")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def forgot_password_page():
    st.title("🔑 Forgot Password")
    
    with st.form("forgot_form"):
        email = st.text_input("Registered Email")
        submitted = st.form_submit_button("Send Reset Link")
        
        if submitted:
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            
            if user:
                token = generate_reset_token()
                send_reset_email(email, token)
                st.success("Reset link sent to your email")
            else:
                st.error("Email not found")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def chat_page():
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
            "sentiment": None
        })

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sentiment" in msg and msg["sentiment"]:
                sentiment = msg["sentiment"]
                sentiment_emoji = "😊" if sentiment["label"] == "POS" else "😐" if sentiment["label"] == "NEU" else "😠"
                st.caption(f"{sentiment_emoji} {sentiment['label']} ({sentiment['score']})")

    # Chat input
    if prompt := st.chat_input("Your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
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
                response, sentiment = generate_grok_style_response(prompt)
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
    
    # Navigation
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "forgot":
        forgot_password_page()
    elif st.session_state.page == "chat":
        chat_page()

    # Sidebar controls
    if st.session_state.page == "chat":
        with st.sidebar:
            st.title("⚙️ DigamberGPT Pro")
            
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
