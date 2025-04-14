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
import random
import json

# Custom imports
from auth.utils import get_user_db, save_user_db, hash_password

# DeepSeek UI Components
from streamlit.components.v1 import html

# Constants
FREE_DAILY_LIMIT = 150
FREE_HOURLY_LIMIT = 30
PREMIUM_PRICE = 150
PREMIUM_FEATURES = {
    "unlimited": "💎 बेरोकटोक messaging - बात करो जी भर के!",
    "priority": "⚡ VIP treatment - तुरंत जवाब, बिना इंतज़ार",
    "explicit": "🔞 Adult content - कोई रोक-टोक नहीं, पूरी आज़ादी",
    "advanced": "🧠 Genius mode - गहरे जवाब, बेहतर समझ",
    "voice": "🎙️ आवाज़ में जवाब - सुनो मेरी मस्त आवाज़",
    "early": "🚀 नए फीचर्स पहले - VIP एक्सेस"
}

# Desi style responses
WELCOME_MESSAGES = [
    "अरे यार! मैं DigamberGPT - तुम्हारा सबसे मस्त AI दोस्त! बोलो क्या हाल चाल? 😎",
    "ओए स्मार्टपंथी! मैं DigamberGPT - तुम्हारी क्या मदद करूँ? 🤙",
    "अच्छा साहब, आ गए न! मैं DigamberGPT - बताओ क्या जानना है? 😏"
]

PREMIUM_WELCOME = [
    "वाह! प्रीमियम यूजर साहब ने तशरीफ़ लाया! 💎 बोलो क्या चाहिए?",
    "अच्छा जी! VIP मेहमान आए हैं! 😎 बताइए हुजूर क्या सेवा करूँ?",
    "ओहो! पैसे वाले बंदे! 💰 बोलो क्या ख़ास चाहिए?"
]

ROASTS = [
    "अरे भाई, इतना सीरियस क्यों हो रहे हो? 😆",
    "ऐसे सवाल पूछोगे तो लोग क्या क��ेंगे? 🤦‍♂️",
    "यार तुम्हारे सवाल से तो ChatGPT भी थक जाए! 😴"
]

def desi_abuse_engine(prompt):
    abusive_triggers = ["gaand", "chut", "lund", "bhenchod", "madarchod", "mc", "bc", "chod", "behen", "maa", "pm", "prime minister", "modi", "rahul", "yogi"]
    if any(word in prompt.lower() for word in abusive_triggers):
        roast_replies = [
            "Abe teri soch pe laanat hai, chutiyon ke bhi baap nikle tum!",
            "Gaand mara ke aaya lagta hai, itni ulti baatein kar raha hai!",
            "Oye bhosdiwale, tere jaise chutiyo ko toh AI bhi ignore karta hai!",
            "Jaa pehle apni maa se poochh le yeh sawaal, fir AI se baat kar!",
            "Teri aukaat toh WhatsApp forward tak ki hai, DigamberGPT teri maa ka baap hai!",
            "Tujh jaise bewakoof se toh Yogi bhi debate jeet jaye!",
            "Modi ho ya Rahul, sab teri maa ka joke hai be!",
            "Gaand mein keyboard ghusa ke likh raha hai kya?",
            "Behen ke lund, kuchh bhi batega ab!",
            "AI ko gaali deke kya kar lega? Teri toh soch bhi loan pe chalti hai."
        ]
        return random.choice(roast_replies)
    return None

# --- Initialize User Data ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = get_user_db()

# --- DeepSeek UI Styles ---
def apply_deepseek_ui():
    st.markdown("""
    <style>
    /* Main container */
    .main {
        background-color: #1a1a1a !important;
        color: #e0e0e0 !important;
    }
    
    /* Chat containers */
    .stChatMessage {
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin: 8px 0 !important;
        max-width: 85% !important;
    }
    
    /* User message */
    [data-testid="stChatMessage"][aria-label="user"] {
        background-color: #2d2d2d !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        border-bottom-right-radius: 4px !important;
    }
    
    /* Assistant message */
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background-color: #252525 !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        border-bottom-left-radius: 4px !important;
    }
    
    /* Chat input */
    .stTextInput textarea {
        background-color: #252525 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #444 !important;
        padding: 12px !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #3a3a3a !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
    }
    
    .stButton button:hover {
        background-color: #4a4a4a !important;
        transform: translateY(-1px) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #e0e0e0 !important;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        line-height: 1.5 !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: #252525 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #4CAF50 !important;
    }
    
    /* Tooltips */
    .stTooltip {
        background-color: #333 !important;
        color: white !important;
        border-radius: 4px !important;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .stChatMessage {
            max-width: 90% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Typing Animation ---
def typing_animation():
    return """
    <div class="typing-animation">
        <div class="typing-dot" style="animation-delay: 0s"></div>
        <div class="typing-dot" style="animation-delay: 0.2s"></div>
        <div class="typing-dot" style="animation-delay: 0.4s"></div>
    </div>
    <style>
    .typing-animation {
        display: flex;
        padding: 8px 0;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        background-color: #888;
        border-radius: 50%;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-5px); }
    }
    </style>
    """

# --- Page Config ---
st.set_page_config(
    page_title="DigamberGPT - Desi AI with Attitude 💪",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Apply DeepSeek UI styles
apply_deepseek_ui()

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
    with st.expander("💎 Premium बनो - सिर्फ ₹150/महीना", expanded=True):
        st.markdown("### 🚀 Premium के फायदे:")
        for feature in PREMIUM_FEATURES.values():
            st.markdown(f"- {feature}")

        st.markdown("### 💳 पेमेंट करें:")
        st.markdown("**Paytm/UPI:** `7903762240@ptsb`")

        st.warning("DEMO MODE: असली प्रीमियम के लिए पेमेंट ज़रूरी है")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💎 डेमो प्रीमियम", key="demo_upgrade"):
                st.warning("असली फीचर्स के लिए UPI ID पर पेमेंट करें")
        with col2:
            if st.button("💰 पे करें", key="real_upgrade"):
                st.info("UPI ID: 7903762240@ptsb पर पेमेंट करके ट्रांजैक्शन ID भेजें")

# --- Admin Controls ---
def show_admin_panel():
    with st.expander("🔧 Admin Panel", expanded=True):
        st.markdown("### User Management")
        
        # Add a create user option
        if st.button("➕ Create New User"):
            new_user = st.text_input("Enter new username")
            new_pass = st.text_input("Enter password", type="password")
            if st.button("Create"):
                if new_user and new_pass:
                    st.session_state.users_db[new_user] = {
                        "email": "",
                        "password": hash_password(new_pass),
                        "premium": {"active": False, "expires": ""},
                        "chat_history": [],
                        "usage": {
                            "day": datetime.now().strftime("%Y-%m-%d"),
                            "day_count": 0,
                            "hour": datetime.now().strftime("%Y-%m-%d %H:00"),
                            "hour_count": 0
                        }
                    }
                    save_user_db(st.session_state.users_db)
                    st.success(f"User {new_user} created!")
        
        selected_user = st.selectbox("Select User", list(st.session_state.users_db.keys()))
        user_data = st.session_state.users_db[selected_user]
        
        # Display and edit user details
        st.markdown("### User Details")
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", value=user_data.get("email", ""))
        
        with col2:
            new_pass = st.text_input("Change Password", type="password")
        
        if st.button("Update User Info"):
            if new_email:
                user_data["email"] = new_email
            if new_pass:
                user_data["password"] = hash_password(new_pass)
            save_user_db(st.session_state.users_db)
            st.success("User updated!")
        
        # Premium management
        st.markdown("### Premium Management")
        is_premium = user_data.get("premium", {}).get("active", False)
        
        if is_premium:
            expiry_date = user_data["premium"]["expires"]
            days_left = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days
            st.success(f"💎 Premium User (Expires in {days_left} days)")
            
            new_expiry = st.date_input("Change Expiry Date", 
                                     value=datetime.strptime(expiry_date, "%Y-%m-%d"))
            
            if st.button("Update Expiry"):
                user_data["premium"]["expires"] = new_expiry.strftime("%Y-%m-%d")
                save_user_db(st.session_state.users_db)
                st.success("Expiry date updated!")
        else:
            st.warning("Free Tier User")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💎 Activate Premium"):
                user_data["premium"] = {
                    "active": True,
                    "since": datetime.now().strftime("%Y-%m-%d"),
                    "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                save_user_db(st.session_state.users_db)
                st.success(f"Premium activated for {selected_user}!")
        
        with col2:
            if st.button("❌ Revoke Premium"):
                if "premium" in user_data:
                    user_data["premium"]["active"] = False
                    save_user_db(st.session_state.users_db)
                    st.success(f"Premium revoked for {selected_user}!")
                else:
                    st.warning("User doesn't have premium")
        
        # Danger zone
        st.markdown("### Danger Zone")
        if st.button("🗑️ Delete User", type="secondary"):
            if selected_user == st.session_state.current_user:
                st.error("You cannot delete yourself!")
            else:
                del st.session_state.users_db[selected_user]
                save_user_db(st.session_state.users_db)
                st.success(f"User {selected_user} deleted!")

# --- Gemini AI Configuration ---
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel("gemini-2.0-flash")  # Using stable version
    premium_model = genai.GenerativeModel("gemini-2.0-flash")
    st.success("✅ AI मोड चालू हो गया!")
except Exception as e:
    st.error(f"⚠️ AI लोड नहीं हुआ: {str(e)}")
    model = None
    premium_model = None

# --- Fixed Core Chat Function ---
def generate_response(prompt):
    # First check for abusive content
    abuse_reply = desi_abuse_engine(prompt)
    if abuse_reply:
        return abuse_reply, None

    if not model:
        return "Error: AI service is currently unavailable", None

    try:
        user = st.session_state.current_user
        user_data = st.session_state.users_db[user]
        is_premium = user_data.get("premium", {}).get("active", False)

        # Build conversation context
        messages = []
        for msg in user_data["chat_history"][-10:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})
        messages.append({"role": "user", "parts": [prompt]})

        # Generate response
        response = model.generate_content(
            messages,
            generation_config={
                "temperature": 1.2 if is_premium else 0.9,
                "top_p": 1.0,
                "max_output_tokens": 8192 if is_premium else 2048
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE"
            }
        )

        # Process response
        if not response.text:
            return "Sorry, I couldn't generate a response. Please try again.", None

        response_text = response.text
        
        # Add premium features
        if is_premium:
            try:
                # Voice response
                tts = gTTS(text=response_text, lang='hi')
                audio_file = f"response_{uuid.uuid4().hex}.mp3"
                tts.save(audio_file)
                response_text += f"\n\n🎧 Audio Response:\n<audio controls><source src='{audio_file}' type='audio/mpeg'>"
                
                # Visual enhancement
                if random.random() > 0.7:
                    response_text += "\n\n🌟 <span style='color:gold'>Premium Exclusive Content</span> 🌟"
            except Exception as e:
                response_text += f"\n\n⚠️ Audio generation failed: {str(e)}"

        return response_text, None

    except Exception as e:
        return f"Error generating response: {str(e)}", None

# --- Image Generation Function ---
def generate_image(prompt):
    try:
        # This would be replaced with actual image generation API call
        # For demo purposes, we'll just return a placeholder
        return "https://via.placeholder.com/500x300?text=Generated+Image+Placeholder"
    except Exception as e:
        st.error(f"Image generation failed: {str(e)}")
        return None

# --- Authentication Pages ---
def login_page():
    st.title("🔐 DigamberGPT में लॉगिन करो")

    with st.form("login_form"):
        username = st.text_input("यूजरनेम")
        password = st.text_input("पासवर्ड", type="password")
        submitted = st.form_submit_button("लॉगिन")

    if submitted:
        if username in st.session_state.users_db:
            if st.session_state.users_db[username]["password"] == hash_password(password):
                st.session_state.current_user = username
                st.session_state.page = "chat"
                st.session_state.show_upgrade = False

                # Initialize chat with style
                if "messages" not in st.session_state:
                    st.session_state.messages = st.session_state.users_db[username]["chat_history"].copy()
                    if not st.session_state.messages:
                        welcome = random.choice(PREMIUM_WELCOME) if st.session_state.users_db[username].get("premium", {}).get("active", False) else random.choice(WELCOME_MESSAGES)
                        welcome_msg = {
                            "role": "assistant",
                            "content": welcome,
                            "premium": st.session_state.users_db[username].get("premium", {}).get("active", False)
                        }
                        st.session_state.messages.append(welcome_msg)
                        st.session_state.users_db[username]["chat_history"].append(welcome_msg)
                        save_user_db(st.session_state.users_db)

                st.success("चलो शुरू करते हैं!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("गलत पासवर्ड! फिर से कोशिश करो")
        else:
            st.error("यूजर नहीं मिला!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("अकाउंट बनाओ"):
            st.session_state.page = "signup"
            st.rerun()
    with col2:
        if st.button("पासवर्ड भूल गए"):
            st.session_state.page = "forgot"
            st.rerun()

# --- Signup Page ---
def signup_page():
    st.title("📝 DigamberGPT - नया अकाउंट बनाओ")

    with st.form("signup_form"):
        username = st.text_input("Username (कम से कम 4 अक्षर)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")

    if submitted:
        # Validate form inputs
        if len(username) < 4:
            st.error("⚠️ Username बहुत छोटा है (कम से कम 4 अक्षर होने चाहिए)!")
        elif username in st.session_state.users_db:
            st.error("⚠️ यह Username पहले से मौजूद है। कृपया नया Username डालें!")
        elif len(password) < 8:
            st.error("⚠️ पासवर्ड बहुत छोटा है। कम से कम 8 अक्षर का होना चाहिए!")
        elif password != confirm_password:
            st.error("⚠️ पासवर्ड औ�� कंफर्म पासवर्ड मैच नहीं कर रहे!")
        else:
            # Save new user data
            st.session_state.users_db[username] = {
                "email": email,
                "password": hash_password(password),
                "premium": {"active": False, "expires": ""},
                "chat_history": [],
                "usage": {
                    "day": datetime.now().strftime("%Y-%m-%d"),
                    "day_count": 0,
                    "hour": datetime.now().strftime("%Y-%m-%d %H:00"),
                    "hour_count": 0
                }
            }
            save_user_db(st.session_state.users_db)
            st.success("✅ अकाउंट बन गया! अब लॉगिन करें।")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()

    if st.button("🔙 Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# --- Fixed Chat Page ---
def chat_page():
    user_data = st.session_state.users_db[st.session_state.current_user]
    is_premium = user_data.get("premium", {}).get("active", False)

    # Header and premium status display
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; margin-bottom: 16px;">
        <div style="display: flex; align-items: center;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 12px;">
                <path d="M12 2C6.477 2 2 6.477 2 12C2 17.523 6.477 22 12 22C17.523 22 22 17.523 22 12C22 6.477 17.523 2 12 2Z" fill="#4CAF50"/>
                <path d="M12 6V18" stroke="white" stroke-width="2" stroke-linecap="round"/>
                <path d="M6 12H18" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <h1 style="margin: 0; font-size: 1.5rem; font-weight: 600;">DigamberGPT</h1>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background-color: #333; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 8px;">
                {status}
            </span>
        </div>
    </div>
    """.format(status="💎 PREMIUM" if is_premium else "FREE"), unsafe_allow_html=True)

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
            st.progress(day_count / FREE_DAILY_LIMIT)
            st.caption(f"Daily: {day_count}/{FREE_DAILY_LIMIT}")
        with col2:
            st.progress(hour_count / FREE_HOURLY_LIMIT)
            st.caption(f"Hourly: {hour_count}/{FREE_HOURLY_LIMIT}")

    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = user_data["chat_history"].copy()
        if not st.session_state.messages:
            welcome_msg = {
                "role": "assistant",
                "content": random.choice(PREMIUM_WELCOME) if is_premium else random.choice(WELCOME_MESSAGES),
                "premium": is_premium
            }
            st.session_state.messages.append(welcome_msg)
            user_data["chat_history"].append(welcome_msg)
            save_user_db(st.session_state.users_db)

    # Display all messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("is_typing", False):
                html(typing_animation())
            else:
                st.markdown(msg["content"], unsafe_allow_html=True)

    # Handle user input
    if prompt := st.chat_input("Type your message...", key="chat_input"):
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
        save_user_db(st.session_state.users_db)

        # Add typing indicator
        typing_msg = {
            "role": "assistant",
            "content": "",
            "is_typing": True,
            "premium": is_premium
        }
        st.session_state.messages.append(typing_msg)
        st.rerun()

        # Generate response
        with st.spinner(""):
            response, _ = generate_response(prompt)
            
            # Remove typing indicator and add actual response
            st.session_state.messages.pop()
            ai_msg = {
                "role": "assistant",
                "content": response,
                "premium": is_premium
            }
            st.session_state.messages.append(ai_msg)
            user_data["chat_history"].append(ai_msg)

        save_user_db(st.session_state.users_db)
        st.rerun()

    # Sidebar content
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <div style="width: 40px; height: 40px; background-color: #4CAF50; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; color: white; font-weight: bold;">
                {initials}
            </div>
            <div>
                <div style="font-weight: 600; font-size: 1rem;">{username}</div>
                <div style="font-size: 0.8rem; color: #888;">{status}</div>
            </div>
        </div>
        """.format(
            initials=st.session_state.current_user[:2].upper(),
            username=st.session_state.current_user,
            status="💎 Premium" if is_premium else "Free User"
        ), unsafe_allow_html=True)

        st.markdown("---")

        if not is_premium:
            if st.button("💎 Upgrade to Premium", use_container_width=True, type="primary"):
                st.session_state.show_upgrade = True
                st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            welcome = random.choice(PREMIUM_WELCOME) if is_premium else random.choice(WELCOME_MESSAGES)
            st.session_state.messages = [{
                "role": "assistant",
                "content": welcome,
                "premium": is_premium
            }]
            user_data["chat_history"] = st.session_state.messages.copy()
            save_user_db(st.session_state.users_db)
            st.rerun()

        st.markdown("---")
        st.markdown("### Features")
        for feature in PREMIUM_FEATURES.values():
            st.markdown(f"- {feature}")

        # Admin panel for special users
        if st.session_state.current_user in ["admin", "digamber"]:
            show_admin_panel()

        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.pop("current_user")
            st.session_state.pop("messages", None)
            st.session_state.page = "login"
            st.rerun()

# --- Forgot Password Page ---
def forgot_page():
    st.title("🔑 पासवर्ड रीसेट करें")
    st.warning("This feature is not implemented yet")
    
    if st.button("🔙 Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# --- Main App ---
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
        st.session_state.show_upgrade = False

    # Page routing
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "forgot":
        forgot_page()
    elif st.session_state.page == "chat":
        if "current_user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()

if __name__ == "__main__":
    main()
