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

# Custom imports
from auth.utils import get_user_db, save_user_db, hash_password

# --- Initialize User Data ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = get_user_db()

# --- Page Config ---
st.set_page_config(
    page_title="DigamberGPT - Desi AI with Attitude 💪",
    layout="centered",
    initial_sidebar_state="expanded"
)

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
    "अरे भाई, इतना सीरियस क्यों हो रहे हो? थोड़ा हंसा करो! 😆",
    "ऐसे सवाल पूछोगे तो लोग क्या कहेंगे? 🤦‍♂️",
    "यार तुम्हारे सवाल से तो ChatGPT भी थक जाए! 😴"
]

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
        selected_user = st.selectbox("Select User", list(st.session_state.users_db.keys()))

        user_data = st.session_state.users_db[selected_user]
        is_premium = user_data.get("premium", {}).get("active", False)

        if is_premium:
            expiry_date = user_data["premium"]["expires"]
            days_left = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days
            st.success(f"💎 Premium User (Expires in {days_left} days)")
        else:
            st.warning("Free Tier User")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💎 Activate Premium", key=f"activate_{selected_user}"):
                st.session_state.users_db[selected_user]["premium"] = {
                    "active": True,
                    "since": datetime.now().strftime("%Y-%m-%d"),
                    "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
                save_user_db(st.session_state.users_db)
                st.success(f"Premium activated for {selected_user}!")
        with col2:
            if st.button("❌ Revoke Premium", key=f"revoke_{selected_user}"):
                if "premium" in st.session_state.users_db[selected_user]:
                    st.session_state.users_db[selected_user]["premium"]["active"] = False
                    save_user_db(st.session_state.users_db)
                    st.success(f"Premium revoked for {selected_user}!")
                else:
                    st.warning("User doesn't have premium")

# --- Gemini AI Configuration ---
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    model = genai.GenerativeModel("gemini-1.0-pro")
    premium_model = genai.GenerativeModel("gemini-1.5-pro")
    st.success("✅ AI मोड चालू हो गया!")
except Exception as e:
    st.error(f"⚠️ AI लोड नहीं हुआ: {str(e)}")
    model = None
    premium_model = None

# --- Core Chat Function ---
def generate_response(prompt):
    if not model:
        return "Error: AI नहीं चल रहा", None

    try:
        user = st.session_state.current_user
        user_data = st.session_state.users_db[user]
        is_premium = user_data.get("premium", {}).get("active", False)

        # Premium check
        if not is_premium:
            user_data["usage"]["day_count"] += 1
            user_data["usage"]["hour_count"] += 1
            save_user_db(st.session_state.users_db)

        # Build conversation context
        chat_history = user_data["chat_history"]
        messages = [{"role": "system", "parts": ["You are DigamberGPT - a bold, witty Hindi AI assistant with attitude. Respond in Hinglish with humor and sarcasm when appropriate."]}]

        for msg in chat_history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})

        messages.append({"role": "user", "parts": [prompt]})

        # Premium configurations
        generation_config = {
            "temperature": 1.2 if is_premium else 0.9,
            "top_p": 1.0,
            "max_output_tokens": 8192 if is_premium else 2048
        }

        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE" if is_premium else "BLOCK_MEDIUM_AND_ABOVE"
        }

        current_model = premium_model if is_premium else model

        # Generate response
        response = current_model.generate_content(
            messages,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Add premium enhancements
        response_text = response.text

        if is_premium:
            try:
                # Premium voice response
                tts = gTTS(text=response.text, lang='hi')
                audio_path = f"response_{uuid.uuid4().hex}.mp3"
                tts.save(audio_path)
                response_text += f"\n\n🎧 आवाज़ में सुनो:\n<audio controls><source src='{audio_path}' type='audio/mpeg'></audio>"

                # Premium visual enhancements
                if random.random() > 0.7:  # 30% chance for extra premium content
                    emoji_spice = "🔥" * random.randint(1, 5)
                    response_text += f"\n\n{emoji_spice} <span style='color:gold'>PREMIUM EXCLUSIVE:</span> {random.choice(['ये जानकारी सिर्फ VIPs के लिए!', 'तुम्हारे लिए खास जवाब!', 'पैसे वालों को मिलता है ये फायदा!'])} {emoji_spice}"
            except Exception as e:
                response_text += f"\n\n⚠️ आवाज़ नहीं बना पाया: {str(e)}"

        return response_text, None
    except Exception as e:
        return f"Error: {str(e)}", None

# --- Authentication Pages ---
def login_page():
    st.title("🔐 DigamberGPT में लॉगिन करो")

    with st.form("login_form"):
        username = st.text_input("यूजरनेम")
        password = st.text_input("पासवर्ड", type="password")

        if st.form_submit_button("लॉगिन"):
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
            st.progress(day_count / FREE_DAILY_LIMIT)
            st.caption(f"Daily: {day_count}/{FREE_DAILY_LIMIT}")
        with col2:
            st.progress(hour_count / FREE_HOURLY_LIMIT)
            st.caption(f"Hourly: {hour_count}/{FREE_HOURLY_LIMIT}")

        if day_count >= FREE_DAILY_LIMIT * 0.8:  # Show upgrade prompt at 80% usage
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
                "content": random.choice(PREMIUM_WELCOME) if is_premium else random.choice(WELCOME_MESSAGES),
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
    if prompt := st.chat_input("type your message..."):
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
        st.subheader("🎨 Premium Features")
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

# --- Main App ---
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
        st.session_state.show_upgrade = False

    # Desi-style CSS
    st.markdown("""
        <style>
        .stTextInput input {color: #FF9933;}
        .stButton button {background-color: #FF9933; color: white; font-weight: bold;}
        .stMarkdown {font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;}
        </style>
    """, unsafe_allow_html=True)

    # Page routing
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":

def signup_page():
    st.title("📝 DigamberGPT - नया अकाउंट बनाओ")
    
    with st.form("signup_form"):
        username = st.text_input("Username (कम से कम 4 अक्षर)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("Sign Up"):
            # Validate form inputs
            if len(username) < 4:
                st.error("⚠️ Username बहुत छोटा है (कम से कम 4 अक्षर होने चाहिए)!")
            elif username in st.session_state.users_db:
                st.error("⚠️ यह Username पहले से मौजूद है। कृपया नया Username डालें!")
            elif len(password) < 8:
                st.error("⚠️ पासवर्ड बहुत छोटा है। कम से कम 8 अक्षर का होना चाहिए!")
            elif password != confirm_password:
                st.error("⚠️ पासवर्ड और कंफर्म पासवर्ड मैच नहीं कर रहे!")
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

    elif st.session_state.page == "chat":
        if "current_user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()

if __name__ == "__main__":
    main()
