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
from dotenv import load_dotenv
import os

# Load environment variables first
load_dotenv()

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
    model = genai.GenerativeModel("gemini-2.0-flash")
    st.success("✅ Gemini 2.0 Flash loaded successfully!")
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
    """Analyze text sentiment with proper error handling"""
    if not sentiment_enabled:
        return None
    
    try:
        result = sentiment_pipeline(text[:512])[0]  # Limit input size
        return {
            "label": result["label"],
            "score": round(result["score"], 3)
        }
    except Exception as e:
        st.error(f"⚠️ Sentiment analysis failed: {str(e)}")
        return None

# --- Other Required Imports ---
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid
import emoji

# --- Core Functions ---
def generate_response(prompt):
    """Generate response from Gemini with sentiment analysis"""
    if not model:
        return "Error: AI model not loaded", None
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 2048
            }
        )
        sentiment = analyze_sentiment(response.text)
        return response.text, sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

def generate_image(prompt, style="Realistic"):
    """Generate image using HuggingFace"""
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"},
            json={"inputs": prompt}
        )
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        st.error(f"⚠️ Image generation failed: {str(e)}")
        return None

# --- UI Setup ---
st.title("🤖 DigamberGPT with Sentiment Analysis")
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

# --- Chat History Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat Messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sentiment" in msg and msg["sentiment"]:
            sentiment = msg["sentiment"]
            if sentiment["label"] == "POS":
                st.markdown(f'<span class="sentiment-positive">😊 Positive ({sentiment["score"]})</span>', 
                           unsafe_allow_html=True)
            elif sentiment["label"] == "NEU":
                st.markdown(f'<span class="sentiment-neutral">😐 Neutral ({sentiment["score"]})</span>', 
                           unsafe_allow_html=True)
            elif sentiment["label"] == "NEG":
                st.markdown(f'<span class="sentiment-negative">😠 Negative ({sentiment["score"]})</span>', 
                           unsafe_allow_html=True)

# --- Chat Input ---
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
                    "content": f"![Generated Image]({img_path})"
                })
                with st.chat_message("assistant"):
                    st.image(img_path)
    else:
        with st.spinner("💭 Analyzing..."):
            response, sentiment = generate_response(prompt)
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

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.subheader("Image Options")
    img_style = st.selectbox(
        "🎨 Style",
        ["Realistic", "Anime", "Ghibli", "Cyberpunk"],
        index=0
    )
    
    st.markdown("---")
    if st.button("📤 Export Chat", use_container_width=True):
        chat_text = "\n".join(
            f"{m['role']}: {m['content']}" 
            for m in st.session_state.messages
        )
        st.download_button(
            "💾 Download as TXT",
            chat_text,
            file_name="digamber_chat.txt",
            use_container_width=True
        )
    
    st.markdown("---")
    tts_enabled = st.toggle("🔊 Enable Text-to-Speech")
    if tts_enabled and st.session_state.messages:
        last_msg = st.session_state.messages[-1]["content"]
        tts = gTTS(text=last_msg, lang='en')
        tts.save("temp_audio.mp3")
        st.audio("temp_audio.mp3")
    
    st.markdown("---")
    st.markdown("**Model Info**")
    st.markdown("- Gemini 2.0 Flash")
    st.markdown("- Sentiment Analysis")
    st.markdown("- Version 2.1")

# --- APK Download Section ---
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
