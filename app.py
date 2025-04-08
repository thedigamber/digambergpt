import streamlit as st
import hashlib
import time
import requests
import io
from PIL import Image
import uuid
import google.generativeai as genai
from transformers import pipeline

# ----- In-Memory Database -----
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        # username: [hashed_password, email]
        "admin": ["8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "admin@example.com"]  # password: "admin"
    }

# ----- Password Hashing -----
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----- AI Initialization -----
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
    ai_enabled = True
except Exception as e:
    st.error(f"AI initialization failed: {str(e)}")
    ai_enabled = False

try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="finiteautomata/bertweet-base-sentiment-analysis")
    sentiment_enabled = True
except Exception as e:
    st.warning(f"Sentiment analysis disabled: {str(e)}")
    sentiment_enabled = False

# ----- AI Functions -----
def analyze_sentiment(text):
    if not sentiment_enabled: return None
    try:
        result = sentiment_pipeline(text[:512])[0]
        return {"label": result["label"], "score": round(result["score"], 3)}
    except Exception as e:
        st.error(f"Sentiment analysis failed: {str(e)}")
        return None

def generate_response(prompt):
    if not ai_enabled: return "AI service is currently unavailable", None
    try:
        response = model.generate_content(prompt, generation_config={
            "temperature": 0.9,
            "top_p": 1.0,
            "max_output_tokens": 4096
        })
        sentiment = analyze_sentiment(response.text)
        return f"मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?\n\n{response.text}", sentiment
    except Exception as e:
        return f"Error: {str(e)}", None

def generate_image(prompt):
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"},
            json={"inputs": prompt},
            timeout=30
        )
        img = Image.open(io.BytesIO(response.content))
        img_path = f"generated_{uuid.uuid4().hex}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        st.error(f"Image generation failed: {str(e)}")
        return None

# ----- Authentication Pages -----
def login_page():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if username in st.session_state.users_db:
                if st.session_state.users_db[username][0] == hash_password(password):
                    st.session_state.user = username
                    st.session_state.page = "chat"
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
        if st.button("Reset Password"):
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
                st.session_state.users_db[username] = [hash_password(password), email]
                st.success("Account created! Please login")
                time.sleep(1)
                st.session_state.page = "login"
                st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def forgot_password_page():
    st.title("🔑 Reset Password")
    
    username = st.text_input("Username")
    new_password = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    
    if st.button("Update Password"):
        if username not in st.session_state.users_db:
            st.error("Username not found!")
        elif new_password != confirm:
            st.error("Passwords don't match!")
        elif len(new_password) < 8:
            st.error("Password too short (min 8 chars)!")
        else:
            st.session_state.users_db[username][0] = hash_password(new_password)
            st.success("Password updated! Please login")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# ----- Chat Page -----
def chat_page():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "मैं DigamberGPT हूँ, मैं तुम्हारी क्या मदद कर सकता हूँ?",
            "sentiment": None
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sentiment"):
                s = msg["sentiment"]
                emoji = "😊" if s["label"] == "POS" else "😐" if s["label"] == "NEU" else "😠"
                st.caption(f"{emoji} {s['label']} ({s['score']})")

    if prompt := st.chat_input("Your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("💭 Thinking..."):
            if any(w in prompt.lower() for w in ["image", "picture", "photo"]):
                img_path = generate_image(prompt)
                if img_path:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"![Generated Image]({img_path})",
                        "sentiment": None
                    })
            else:
                response, sentiment = generate_response(prompt)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                })
        st.rerun()

# ----- Main App -----
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "forgot":
        forgot_password_page()
    elif st.session_state.page == "chat":
        if "user" not in st.session_state:
            st.session_state.page = "login"
            st.rerun()
        else:
            chat_page()
            with st.sidebar:
                st.title(f"👤 {st.session_state.user}")
                if st.button("🗑️ Clear Chat"):
                    st.session_state.messages = []
                    st.rerun()
                if st.button("🔒 Logout"):
                    st.session_state.pop("user")
                    st.session_state.page = "login"
                    st.rerun()

if __name__ == "__main__":
    main()
