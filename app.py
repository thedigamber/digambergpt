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
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from gtts import gTTS
import os

# Custom imports
from auth.utils import get_user_db, save_user_db, hash_password

# --- Initialize User Data ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = get_user_db()

# --- Page Config ---
st.set_page_config(
    page_title="DigamberGPT Premium",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constants
FREE_DAILY_LIMIT = 150  # 150 messages per day
FREE_HOURLY_LIMIT = 30   # 30 messages per hour
PREMIUM_PRICE = 150      # ₹150 per month
PREMIUM_FEATURES = {
    "unlimited": "💎 Unlimited messages (no restrictions)",
    "priority": "⚡ Priority processing (fast responses)",
    "explicit": "🔞 Allow explicit content (no filters)",
    "advanced": "🧠 Advanced AI models (better answers)",
    "voice": "🎙️ Voice response generation",
    "early": "🚀 Early access to new features"
}

# --- Check Message Limits ---
def check_message_limits(user):
    user_data = st.session_state.users_db[user]
    
    # Premium users have no limits
    if user_data.get("premium", {}).get("active", False):
        return True
    
    # Initialize usage tracking
    if "usage" not in user_data:
        user_data["usage"] = {
            "day": datetime.now().strftime("%Y-%m-%d"),
            "day_count": 0,
            "hour": datetime.now().strftime("%Y-%m-%d %H:00"),
            "hour_count": 0
        }
    
    # Reset daily counter if new day
    current_day = datetime.now().strftime("%Y-%m-%d")
    if user_data["usage"]["day"] != current_day:
        user_data["usage"]["day"] = current_day
        user_data["usage"]["day_count"] = 0
    
    # Reset hourly counter if new hour
    current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
    if user_data["usage"]["hour"] != current_hour:
        user_data["usage"]["hour"] = current_hour
        user_data["usage"]["hour_count"] = 0
    
    # Check limits
    if user_data["usage"]["day_count"] >= FREE_DAILY_LIMIT:
        st.error(f"⚠️ Daily limit reached ({FREE_DAILY_LIMIT} messages). Try again tomorrow or upgrade to premium!")
        st.session_state.show_upgrade = True
        return False
    
    if user_data["usage"]["hour_count"] >= FREE_HOURLY_LIMIT:
        st.error(f"⚠️ Hourly limit reached ({FREE_HOURLY_LIMIT} messages). Try again in an hour or upgrade to premium!")
        st.session_state.show_upgrade = True
        return False
    
    return True

# --- Premium Upgrade Modal ---
def show_upgrade_modal():
    with st.expander("💎 Upgrade to Premium (₹150/month)", expanded=True):
        st.markdown("### 🚀 Premium Features:")
        for feature in PREMIUM_FEATURES.values():
            st.markdown(f"- {feature}")
        
        # Payment options
        st.markdown("### 💳 Payment Methods:")
        st.write("Paytm/UPI: 7903762242@ptsb")
        
        # Demo mode warning
        st.warning("DEMO MODE: For testing purposes, premium can be activated without payment")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💎 Activate Premium (Demo)", key="demo_upgrade"):
                activate_premium()
        with col2:
            if st.button("💰 Pay & Activate", key="real_upgrade"):
                st.info("In a production app, this would redirect to payment gateway")
                activate_premium()

def activate_premium():
    """Activate premium subscription for the current user"""
    st.session_state.users_db[st.session_state.current_user]["premium"] = {
        "active": True,
        "since": datetime.now().strftime("%Y-%m-%d"),
        "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    }
    save_user_db(st.session_state.users_db)
    st.success("🎉 Premium activated! Enjoy unlimited access for 1 month!")
    time.sleep(1)
    st.rerun()

# --- Gemini AI Configuration ---
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel("gemini-1.0-pro")  # Basic model for free users
    premium_model = genai.GenerativeModel("gemini-1.5-pro")  # Better model for premium users
    st.success("✅ AI Models loaded successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to load AI models: {str(e)}")
    model = None
    premium_model = None

# --- Core Functions ---
def generate_response(prompt):
    if not model:
        return "Error: AI model not loaded", None
    
    try:
        user = st.session_state.current_user
        user_data = st.session_state.users_db[user]
        is_premium = user_data.get("premium", {}).get("active", False)
        
        # Update usage counters for free users
        if not is_premium:
            user_data["usage"]["day_count"] += 1
            user_data["usage"]["hour_count"] += 1
            save_user_db(st.session_state.users_db)
        
        chat_history = user_data["chat_history"]
        messages = []
        
        for msg in chat_history[-20:]:  # Last 20 messages as context
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})
        
        messages.append({"role": "user", "parts": [prompt]})
        
        # Configuration based on premium status
        generation_config = {
            "temperature": 0.9,
            "top_p": 1.0,
            "max_output_tokens": 8192 if is_premium else 2048
        }
        
        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE"
        }
        
        # Use premium model for premium users
        current_model = premium_model if is_premium else model
        
        response = current_model.generate_content(
            messages,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        response_text = f"मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?\n\n{response.text}"
        
        # Add voice response for premium users
        if is_premium:
            try:
                tts = gTTS(text=response.text, lang='hi')
                audio_path = f"response_{uuid.uuid4().hex}.mp3"
                tts.save(audio_path)
                response_text += f"\n\n🎧 Voice response:\n<audio controls><source src='{audio_path}' type='audio/mpeg'></audio>"
            except Exception as e:
                response_text += f"\n\n⚠️ Voice generation failed: {str(e)}"
        
        return response_text, None
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
                    st.session_state.show_upgrade = False
                    
                    # Initialize chat history
                    if "messages" not in st.session_state:
                        st.session_state.messages = st.session_state.users_db[username]["chat_history"].copy()
                        if not st.session_state.messages:
                            welcome_msg = {
                                "role": "assistant",
                                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                                "premium": st.session_state.users_db[username].get("premium", {}).get("active", False)
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
                    "chat_history": [],
                    "usage": {
                        "day": datetime.now().strftime("%Y-%m-%d"),
                        "day_count": 0,
                        "hour": datetime.now().strftime("%Y-%m-%d %H:00"),
                        "hour_count": 0
                    }
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

# --- Chat Page ---
def chat_page():
    user_data = st.session_state.users_db[st.session_state.current_user]
    is_premium = user_data.get("premium", {}).get("active", False)
    
    st.title("🤖 DigamberGPT" + (" 💎" if is_premium else ""))
    
    # Show premium status
    if is_premium:
        expiry_date = user_data["premium"]["expires"]
        days_left = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days
        st.success(f"💎 PREMIUM MEMBER (Expires in {days_left} days)")
    else:
        # Show usage counters
        usage = user_data.get("usage", {})
        day_count = usage.get("day_count", 0)
        hour_count = usage.get("hour_count", 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.progress(day_count/FREE_DAILY_LIMIT)
            st.caption(f"Daily: {day_count}/{FREE_DAILY_LIMIT}")
        with col2:
            st.progress(hour_count/FREE_HOURLY_LIMIT)
            st.caption(f"Hourly: {hour_count}/{FREE_HOURLY_LIMIT}")
        
        if day_count >= FREE_DAILY_LIMIT*0.8:  # Show upgrade prompt at 80% usage
            st.session_state.show_upgrade = True
    
    # Show upgrade modal if needed
    if st.session_state.get("show_upgrade", False):
        show_upgrade_modal()
        return
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = user_data["chat_history"].copy()
        if not st.session_state.messages:
            welcome_msg = {
                "role": "assistant",
                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                "premium": is_premium
            }
            st.session_state.messages.append(welcome_msg)
            user_data["chat_history"].append(welcome_msg)
            save_user_db(st.session_state.users_db)
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Your message..."):
        # Check for duplicate message
        if st.session_state.messages and st.session_state.messages[-1]["content"] == prompt:
            st.warning("Duplicate message detected!")
            st.stop()
        
        # Check message limit
        if not check_message_limits(st.session_state.current_user):
            st.rerun()
        
        # Add user message
        user_msg = {
            "role": "user", 
            "content": prompt,
            "premium": is_premium
        }
        st.session_state.messages.append(user_msg)
        user_data["chat_history"].append(user_msg)
        
        with st.spinner("💭 Generating response..."):
            if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw"]):
                img_path = generate_image(prompt)
                if img_path:
                    img_msg = {
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})",
                        "premium": is_premium
                    }
                    st.session_state.messages.append(img_msg)
                    user_data["chat_history"].append(img_msg)
            else:
                response, _ = generate_response(prompt)
                ai_msg = {
                    "role": "assistant", 
                    "content": response,
                    "premium": is_premium
                }
                st.session_state.messages.append(ai_msg)
                user_data["chat_history"].append(ai_msg)
            
            save_user_db(st.session_state.users_db)
        
        st.rerun()

    # Sidebar
    with st.sidebar:
        st.header(f"👤 {st.session_state.current_user}")
        
        if is_premium:
            st.success("💎 Premium Member")
        else:
            st.warning(f"Free Tier ({len(user_data['chat_history'])}/{FREE_DAILY_LIMIT} messages)")
            if st.button("💎 Upgrade to Premium", use_container_width=True):
                st.session_state.show_upgrade = True
                st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
                "premium": is_premium
            }]
            user_data["chat_history"] = st.session_state.messages.copy()
            save_user_db(st.session_state.users_db)
            st.rerun()
        
        st.markdown("---")
        st.subheader("🎨 Premium Features")
        for feature in PREMIUM_FEATURES.values():
            st.markdown(f"- {feature}")
        
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
        st.session_state.show_upgrade = False
    
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
    elif st.session_state.page == "chat":
        if "current_user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()

if __name__ == "__main__":
    main()
