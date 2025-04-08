# Fix for distutils import error - must be at VERY TOP
import sys
import setuptools
from distutils import util

# Standard imports
import streamlit as st
import requests
import io
from PIL import Image
import base64
import re
import time
from dotenv import load_dotenv
import os

# Load environment variables first
load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")

# Gemini AI Configuration with error handling
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")  # Using Gemini 2.0 Flash
    st.success("✅ Gemini 2.0 Flash model loaded successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to load Gemini: {str(e)}")
    model = None

# Sentiment Analysis with error handling
try:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis")
except Exception as e:
    sentiment_pipeline = None
    st.warning("⚠️ Sentiment analysis disabled")

# Other required imports
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid
import emoji

# --- Core Functions ---
def generate_gemini_response(prompt):
    """Generate response from Gemini 2.0 Flash"""
    if not model:
        return "Error: AI model not loaded"
    
    try:
        # Configure generation parameters for faster responses
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=False
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_image(prompt, style="Realistic", width=512, height=512):
    """Generate image using HuggingFace"""
    try:
        api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        headers = {"Authorization": f"Bearer {api_token}"}
        
        model_map = {
            "Anime": "nitrosocke/waifu-diffusion",
            "Realistic": "stabilityai/stable-diffusion-xl-base-1.0",
            "Ghibli": "nitrosocke/Ghibli-Diffusion",
            "Cyberpunk": "DGSpitzer/Cyberpunk-Anime-Diffusion"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": width,
                "height": height,
                "num_inference_steps": 25
            }
        }
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model_map.get(style, 'stabilityai/stable-diffusion-xl-base-1.0')}",
            headers=headers,
            json=payload
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
st.title("⚡ DigamberGPT (Gemini 2.0 Flash)")
st.markdown("""
    <style>
    .stTextInput input {color: #4F8BF9;}
    .stButton button {background-color: #4F8BF9; color: white;}
    .chat-message {padding: 10px; border-radius: 10px; margin: 5px 0;}
    .user-message {background-color: #2a2a2a; color: white;}
    .bot-message {background-color: #1a1a1a; color: #39ff14;}
    </style>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.markdown(f'<div class="chat-message {message["role"]}-message">{message["content"]}</div>', 
                       unsafe_allow_html=True)
        elif message["type"] == "image":
            st.image(message["content"], caption="Generated Image")

# Chat input
if prompt := st.chat_input("Message DigamberGPT..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(f'<div class="chat-message user-message">{prompt}</div>', 
                   unsafe_allow_html=True)
    
    # Determine response type
    if any(word in prompt.lower() for word in ["image", "picture", "photo", "generate", "draw", "banana"]):
        with st.spinner("🖌️ Creating your image with Gemini 2.0 Flash..."):
            image_path = generate_image(prompt)
            if image_path:
                st.session_state.messages.append({"role": "assistant", "type": "image", "content": image_path})
                with st.chat_message("assistant"):
                    st.image(image_path, caption="Generated Image")
    else:
        # Generate text response
        with st.spinner("💡 Gemini 2.0 Flash is thinking..."):
            response = generate_gemini_response(prompt)
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": response})
            with st.chat_message("assistant"):
                st.markdown(f'<div class="chat-message bot-message">{response}</div>', 
                           unsafe_allow_html=True)
                
        # Optional text-to-speech
        if st.toggle("🔊 Speak Response", False, key="tts_toggle"):
            with st.spinner("🔊 Converting to speech..."):
                try:
                    tts = gTTS(text=response, lang='en')
                    audio_file = f"response_{uuid.uuid4().hex}.mp3"
                    tts.save(audio_file)
                    st.audio(audio_file)
                    os.remove(audio_file)
                except Exception as e:
                    st.error(f"⚠️ TTS failed: {str(e)}")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🗑️ Clear Chat History"):
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
    if st.button("📤 Export Chat History"):
        chat_text = "\n".join(
            f"{m['role'].title()}: {m['content']}" 
            for m in st.session_state.messages 
            if m["type"] == "text"
        )
        st.download_button(
            "💾 Download as TXT",
            chat_text,
            file_name="digamber_chat_history.txt"
        )
    
    st.markdown("---")
    st.markdown("**Model Info:** Gemini 2.0 Flash")
    st.markdown("**Version:** 1.0")

# --- APK Download Section ---
st.markdown("---")
st.markdown("### DigamberGPT Android App")
query_params = st.query_params
is_app = query_params.get("app", ["false"])[0].lower() == "true"

if is_app:
    st.markdown(
        """<button disabled style='background-color:orange;color:white;padding:10px 20px;border:none;border-radius:8px;font-size:16px;'>अपडेट उपलब्ध है</button>""",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """<a href="https://drive.google.com/uc?export=download&id=1cdDIcHpQf-gwX9y9KciIu3tNHrhLpoOr" target="_blank">
        <button style='background-color:green;color:white;padding:10px 20px;border:none;border-radius:8px;font-size:16px;'>Download Android APK</button></a>""",
        unsafe_allow_html=True
    )
