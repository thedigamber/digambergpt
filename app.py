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
    if user_data.get("premium", False):
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
        return False
    
    if user_data["usage"]["hour_count"] >= FREE_HOURLY_LIMIT:
        st.error(f"⚠️ Hourly limit reached ({FREE_HOURLY_LIMIT} messages). Try again in an hour or upgrade to premium!")
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
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Paytm_Logo_%28October_2021%29.svg/1200px-Paytm_Logo_%28October_2021%29.svg.png", width=100)
            st.write("Paytm/UPI: 9876543210@paytm")
        with col2:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/PayPal.svg/1200px-PayPal.svg.png", width=100)
            st.write("PayPal: pay@digambergpt.com")
        
        if st.button("💎 Activate Premium Now", key="upgrade_button"):
            # In a real app, you would verify payment here
            st.session_state.users_db[st.session_state.current_user]["premium"] = {
                "active": True,
                "since": datetime.now().strftime("%Y-%m-%d"),
                "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            save_user_db(st.session_state.users_db)
            st.success("🎉 Premium activated! Enjoy unlimited access for 1 month!")
            time.sleep(2)
            st.rerun()

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
                tts.save("response.mp3")
                response_text += "\n\n🎧 Voice response:\n<audio controls><source src='./response.mp3' type='audio/mpeg'></audio>"
            except Exception as e:
                response_text += f"\n\n⚠️ Voice generation failed: {str(e)}"
        
        return response_text, None
    except Exception as e:
        return f"Error: {str(e)}", None

# [Rest of your authentication and chat page code remains similar, 
# but make sure to update all references to premium status checks]

# --- Enhanced Chat Page ---
def chat_page():
    st.title("🤖 DigamberGPT Premium" + (" 💎" if st.session_state.users_db[st.session_state.current_user].get("premium", {}).get("active", False) else ""))
    
    # Show premium status
    user_data = st.session_state.users_db[st.session_state.current_user]
    is_premium = user_data.get("premium", {}).get("active", False)
    
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
    
    # [Rest of your chat page implementation...]
