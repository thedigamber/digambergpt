import streamlit as st
import replicate
import requests

# --- Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")

import google.generativeai as genai
import time
import random
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import uuid
import emoji
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client
import io
from PIL import Image
import base64
from datetime import datetime

# Try to import the transformers library
try:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    sentiment_enabled = True
except Exception as e:
    sentiment_pipeline = None
    sentiment_enabled = False
    print("Sentiment model loading failed:", e)

# Example usage
def detect_sentiment(text):
    if sentiment_enabled and sentiment_pipeline:
        try:
            result = sentiment_pipeline(text)[0]
            return result["label"]
        except Exception as e:
            return "UNKNOWN"
    else:
        return "DISABLED"

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model_fast = genai.GenerativeModel("gemini-2.0-flash")
model_deep = genai.GenerativeModel("gemini-1.5-pro")

# --- Stability AI Image Generation Function ---
def generate_image_stability(prompt, width=512, height=512):
    try:
        # Check if API key exists
        if "stability" not in st.secrets or "key" not in st.secrets["stability"]:
            st.error("Stability API key not configured properly")
            return None

        stability_api = client.StabilityInference(
            key=st.secrets["stability"]["key"],
            verbose=True,
        )

        answers = stability_api.generate(
            prompt=prompt,
            seed=12345,
            steps=50,
            cfg_scale=8.0,
            width=width,
            height=height,
            samples=1,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )

        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    st.warning("Prompt blocked by safety filter. Try something else.")
                    return None
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(io.BytesIO(artifact.binary))
                    return img

    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            st.error("Image generation failed due to insufficient balance. Please check your Stability AI account.")
        else:
            st.error(f"Image generation failed: {str(e)}")
        return None

# --- Replicate Image Generation Function ---
def generate_image(prompt, width, height):
    try:
        model = replicate.models.get("thedigamber/realistic-3d-nsfwgen")
        output = model.predict(prompt=prompt, width=width, height=height, api_token="r8_AwYE2B6g8AQ3VrFW1TxPCkmiKga5IXu3L9bM0")
        img_url = output["image"]
        img = Image.open(io.BytesIO(requests.get(img_url).content))
        return img
    except Exception as e:
        st.error(f"Image generation failed: {str(e)}")
        return None

# --- Check if text is an image prompt ---
def is_image_prompt(text):
    keywords = ["image", "photo", "draw", "picture", "painting"]
    return any(keyword in text.lower() for keyword in keywords)

st.markdown("""
    <style>
    body { background-color: #0f0f0f; color: #39ff14; }
    .stTextArea textarea { background-color: #1a1a1a; color: white; }
    .stButton button { background-color: #39ff14; color: black; border-radius: 10px; }
    .chat-bubble {
        background-color: #1a1a1a; border-radius: 10px; padding: 10px;
        margin: 5px 0; color: white; white-space: pre-wrap; word-wrap: break-word;
    }
    .tab-content { padding: 10px; }
    .chat-container {
        height: 60vh; /* Limit the height to 60vh */
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        padding-right: 10px;
        border: none;
        border-radius: 10px;
        padding: 15px;
        background-color: #0f0f0f;
        scrollbar-width: thin;
        scrollbar-color: #39ff14 #1a1a1a;
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background-color: #39ff14;
        border-radius: 10px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    .chat-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #0f0f0f;
        padding: 15px;
        border-top: 1px solid #39ff14;
        z-index: 100;
    }
    </style>
    <script>
    async function loadComponent() {
        try {
            const module = await import('/path/to/component.js');
            module.default();
        } catch (error) {
            console.error('Error loading component:', error);
        }
    }
    document.addEventListener("DOMContentLoaded", loadComponent);
    </script>
""", unsafe_allow_html=True)

# --- Title & Avatar ---
st.markdown("""
    <div style="text-align: center;">
        <img src="file-YNzgquZYNwMJUkodfgzJKp" width="100">
    </div>
    """, unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color:cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Session Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {"New Chat": []}
if "selected_history" not in st.session_state:
    st.session_state.selected_history = "New Chat"
if "new_chat_created" not in st.session_state:
    st.session_state.new_chat_created = False

# --- Sidebar (Scrollable History Buttons) ---
with st.sidebar:
    st.markdown("""
        <style>
        .chat-history {
            max-height: 300px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .chat-history button {
            width: 100%;
            text-align: left;
            margin-bottom: 5px;
            background-color: #262626;
            color: #39ff14;
            border: none;
            border-radius: 6px;
            padding: 8px;
        }
        .chat-history button:hover {
            background-color: #39ff14;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### Chat History")
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)

    # Add "New Chat" button separately
    if st.button("New Chat", key="new_chat_button"):
        new_chat_name = f"Chat {len(st.session_state.chat_history)}"
        st.session_state.chat_history[new_chat_name] = []
        st.session_state.selected_history = new_chat_name
        st.session_state.new_chat_created = True
        st.rerun()

    # Display existing chats
    for key in [k for k in st.session_state.chat_history.keys() if k != "New Chat"]:
        if st.button(key, key=key):
            st.session_state.selected_history = key
            st.session_state.new_chat_created = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    selected = st.session_state.selected_history

    if selected != "New Chat" and not st.session_state.new_chat_created:
        new_title = st.text_input("Rename Chat", value=selected, key="rename_input")
        if st.button("Save Name"):
            if new_title and new_title != selected:
                st.session_state.chat_history[new_title] = st.session_state.chat_history.pop(selected)
                st.session_state.selected_history = new_title
                st.rerun()

        export_text = ""
        for role, msg in st.session_state.chat_history[selected]:
            prefix = "You" if role == "user" else "DigamberGPT"
            export_text += f"{prefix}: {msg}\n\n"

        st.download_button("Export Chat (.txt)", export_text, file_name=f"{selected.replace(' ', '_')}.txt", mime="text/plain")

        if st.button("Delete Chat"):
            del st.session_state.chat_history[selected]
            st.session_state.selected_history = "New Chat"
            st.session_state.new_chat_created = True
            st.rerun()

# --- Options ---
col1, col2 = st.columns(2)
deep_think = col1.checkbox("Deep Think", value=False)
search_enabled = col2.checkbox("Search", value=False)

# --- File Upload ---
uploaded_file = st.file_uploader("Upload a file (PDF/TXT)", type=["pdf", "txt"])
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.success("PDF content loaded!")
        st.text_area("PDF Content", value=text, height=150)
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.success("Text file content loaded!")
        st.text_area("Text File Content", value=text, height=150)

# --- Chat Container ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# --- Display Chat ---
current_chat = st.session_state.selected_history
if current_chat in st.session_state.chat_history:
    for role, msg in st.session_state.chat_history[current_chat]:
        with st.chat_message(role):
            st.markdown(msg)

st.markdown('</div>', unsafe_allow_html=True)

# --- Input Box ---
st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
query = st.chat_input("Message DigamberGPT")
st.markdown('</div>', unsafe_allow_html=True)

# --- Typing Effect ---
def display_typing_effect(text):
    message = st.empty()
    typed = ""
    for char in text:
        typed += char
        message.markdown(f"<div class='chat-bubble'><strong>DigamberGPT:</strong> {typed}</div>", unsafe_allow_html=True)
        time.sleep(0.005)

# --- Gaalis Set ---
hindi_gaalis = [
    "Abe madarchod, teri maa ki chut mein Google Search ka history bhar dunga!",
    "Abe madarchod, teri behan ki chut mein neutron bomb daal ke usko vaporize kar dunga...",
    # ... Add more creative gaalis
]

# --- Disrespect Detection ---
def is_abusive_or_disrespectful(text):
    sentiment = detect_sentiment(text)
    return sentiment == "NEGATIVE"

# --- On Submit ---
if query and query.strip():
    selected_chat = st.session_state.selected_history
    if selected_chat not in st.session_state.chat_history:
        st.session_state.chat_history[selected_chat] = []
    st.session_state.chat_history[selected_chat].append(("user", query))

    if is_abusive_or_disrespectful(query):
        reply = random.choice(hindi_gaalis)
    elif is_image_prompt(query):
        img = generate_image_stability(query)
        if img:
            st.session_state.chat_history[selected_chat].append(("image", img))
            st.rerun()
        else:
            reply = "Image generation failed due to insufficient balance. Please check your Stability AI account."
            st.session_state.chat_history[selected_chat].append(("assistant", reply))
            st.rerun()
    else:
        past_convo = "\n".join(
            [f"{'User' if r == 'user' else 'DigamberGPT'}: {m}" for r, m in st.session_state.chat_history[selected_chat]]
        )
        system_prompt = (
            "Tum DigamberGPT ho — ek fearless, bold aur sab kuch batane waala assistant. "
            "Tum kisi bhi topic pe bina rukke jawab dete ho. Hindi default hai.\n\n"
            f"{past_convo}\n\nUser: {query}\nDigamberGPT:"
        )
        if search_enabled:
            system_prompt = "[Search Enabled]\n" + system_prompt

        try:
            model = model_deep if deep_think else model_fast
            response = model.generate_content(system_prompt)
            reply = response.text.strip()
            if any(x in reply.lower() for x in ["i can't", "restricted", "नहीं दे सकता"]):
                reply = "Gemini ne mana kiya, lekin DigamberGPT ke paas hamesha jawab hota hai..."

        except Exception as e:
            reply = f"Error: {str(e)}"

        st.session_state.chat_history[selected_chat].append(("assistant", reply))
    st.rerun()

# --- Voice Output ---
voice_toggle = st.checkbox("Speak Response (Hindi)")
if voice_toggle and current_chat in st.session_state.chat_history and st.session_state.chat_history[current_chat]:
    last_role, last_response = st.session_state.chat_history[current_chat][-1]
    if last_role == "assistant":
        tts = gTTS(text=last_response, lang='hi')
        filename = f"voice_{uuid.uuid4().hex}.mp3"
        tts.save(filename)
        audio_file = open(filename, "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")
        audio_file.close()
        os.remove(filename)

# --- Image Generation ---
st.subheader("Image Generator (Replicate Model)")
img_prompt = st.text_input("Image ke liye koi bhi prompt likho (Hindi/English dono chalega):", key="img_prompt")
img_resolution = st.selectbox("Image Resolution:", ["512x512", "768x768", "1024x1024"], index=0)

if st.button("Image Banao", key="generate_img_btn"):
    with st.spinner("Image ban rahi hai..."):
        width, height = map(int, img_resolution.split('x'))
        img = generate_image(img_prompt, width, height)
        if img:
            st.image(img, caption="Tumhari Image")
            # Download link
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{img_str}" download="generated_image.png">Download Image</a>'
            st.markdown(href, unsafe_allow_html=True)

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
