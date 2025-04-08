import sys
import setuptools
from distutils import util

import streamlit as st
import requests
import io
from PIL import Image
import time
from dotenv import load_dotenv
import os
from transformers import pipeline
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid
import emoji

load_dotenv()

# Page Config
st.set_page_config(page_title="DigamberGPT", layout="centered", initial_sidebar_state="expanded")

# Gemini AI Configuration
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    st.success("✅ Gemini 2.0 Flash loaded successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to load DigamberGPT: {str(e)}")
    model = None

# Sentiment Analysis
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="finiteautomata/bertweet-base-sentiment-analysis", tokenizer="finiteautomata/bertweet-base-sentiment-analysis")
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

# Abusive response generator
def generate_abusive_response(prompt):
    abusive_responses = [
        "teri behan ki chut mein mera lund jaayega kitna maza aayega 🤤",
        "tere muh mein meri jeb ka lund jaana chahiye 🤐",
        "tujhe apni maa ki yaad dilane ka mann kar raha hai 🤮",
        "teri aukat kya hai, chhup ja yaar 😈",
        "kabhi socha hai, ye sab jo tu keh raha hai, tere liye khatarnak ho sakta hai! 😡"
    ]
    
    # Check if prompt contains insulting language
    if any(word in prompt.lower() for word in ["insult", "fuck", "bitch", "gandu", "sala", "madarchod"]):
        return random.choice(abusive_responses)
    return None

# Core Functions
def generate_response(prompt, chat_history=None):
    if not model:
        return "Error: AI model not loaded", None

    try:
        # Build conversation history for context
        messages = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})

        # Add current prompt
        messages.append({"role": "user", "parts": [prompt]})

        # Generate response with full context
        response = model.generate_content(
            messages,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 2048
            }
        )
        sentiment = analyze_sentiment(response.text)
        abusive_response = generate_abusive_response(prompt)

        # If abusive response is generated, replace the AI's normal response
        if abusive_response:
            return abusive_response, None

        return response.text, sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

# Image generation function (unchanged)
def generate_image(prompt, style="Realistic"):
    try:
        api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        headers = {"Authorization": f"Bearer {api_token}"}
        json_data = {
            "inputs": prompt,
            "options": {"wait_for_model": True}
        }
        response = requests.post(
            f"https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0", headers=headers, json=json_data
        )
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        st.error(f"⚠️ Image generation failed: {str(e)}")
        return None

# UI Setup (unchanged)
st.title("🤖 DigamberGPT with Chat Memory")
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

# Chat History Initialization (unchanged)
if "messages" not in st.session_state:
    st.session_state.messages = []
st.session_state.messages.append({
    "role": "assistant",
    "content": "Hello! I'm DigamberGPT. How can I help you today?",
    "sentiment": None
})

# Display Chat Messages (unchanged)
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

# Chat Input (unchanged)
if prompt := st.chat_input("Your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw"]):
        with st.spinner("🎨 Creating image..."):
            img_path = generate_image(prompt)
            if img_path:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"![Generated Image]({img_path})",
                    "sentiment": None
                })
                with st.chat_message("assistant"):
                    st.image(img_path)
    else:
        with st.spinner("💭 Analyzing..."):
            # Pass only the last 5 messages for context to avoid token limit issues
            recent_history = st.session_state.messages[-5:] if len(st.session_state.messages) > 5 else st.session_state.messages
            response, sentiment = generate_response(prompt, recent_history)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sentiment": sentiment
            })
            with st.chat_message("assistant"):
                st.markdown(response)
                if sentiment:
                    if sentiment["label"] == "POS":
                        st.markdown(f'<span class="sentiment-positive">😊 Positive ({sentiment["score"]})</span>',
                                   unsafe_allow_html=True)
                    elif sentiment["label"] == "NEU":
                        st.markdown(f'<span class="sentiment-neutral">😐 Neutral ({sentiment["score"]})</span>',
                                   unsafe_allow_html=True)
                    elif sentiment["label"] == "NEG":
                        st.markdown(f'<span class="sentiment-negative">😠 Negative ({sentiment["score"]})</span>',
                                   unsafe_allow_html=True)

# Sidebar Controls (unchanged)
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm DigamberGPT. How can I help you today?",
            "sentiment": None
        })
        st.rerun()

# APK Download Section (unchanged)
st.markdown("---")
st.markdown("### 📱 Mobile App")
st.markdown("""
<a href="https://drive.google.com/uc?export=download&id=1cdDIcHpQf-gwX9y9KciIu3tNHrhLpoOr" target="_blank">
<button style='background-color: #4F8BF9;color: white;padding: 10px 20px;border: none;border-radius: 5px;font-size: 16px;margin: 10px 0;'>Download Android APK</button>
</a>
""", unsafe_allow_html=True)
