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
            "unlimited": "💎 बेरोकटोक messaging - बात करो ��ी भर के!",
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
            "अच्छा जी! VIP मेहमान आए हैं! 😎 बताइए हुजूर क��या सेवा करूँ?",
            "ओहो! पैसे वाले बंदे! 💰 बोलो क्या ख़ास चाहिए?"
            ]
                        ROASTS = [
            "अरे भाई, इतना सीरियस क्यों हो रहे हो? teri apni maa chudwani hai kya be ! 😆",
            "ऐसे सवाल पूछोगे तो लोग क्या कहेंगे? teri behan ki chut mein lund mera 🤦‍♂️",
            "यार तुम्हारे सवाल से तो ChatGPT भी थक जाए! lekin mai nahi थकूंगा tumhari behan chod e mein😴"
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
                                                                                                                model = genai.GenerativeModel("gemini-2.0-flash")
                                                                                                                premium_model = genai.GenerativeModel("gemini-2.0-flash")
                                                                                                                st.success("✅ AI मोड चालू हो गया!")
                                                                                                                except Exception as e:
                                                                                                                    st.error(f"⚠️ AI लोड नहीं हुआ: {str(e)}")
                                                                                                                    model = None
                                                                                                                    premium_model = None
                                                                                                                                                                                                                                        # --- Core Chat Function ---
                                                                                                                    def generate_response(prompt):
                                                                                                                        abuse_reply = desi_abuse_engine(prompt)
                                                                                                                        if abuse_reply:
                                                                                                                            return abuse_reply, None
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
                                                                                                                                                                                                                                                                                # Build conversation context (without system role)
                                                                                                                                        chat_history = user_data["chat_history"]
                                                                                                                                        messages = []
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
                                                    
