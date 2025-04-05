import streamlit as st
import google.generativeai as genai
import time
import random

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #0f0f0f;
        color: #39ff14;
    }
    .stTextArea textarea {
        background-color: #1a1a1a;
        color: white;
    }
    .stButton button {
        background-color: #39ff14;
        color: black;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title & Avatar ---
col1, col2 = st.columns([1, 8])
with col1:
    st.image("https://i.imgur.com/3v5p4UQ.png", width=50)
with col2:
    st.markdown("<h1 style='color:cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- File Upload ---
uploaded_file = st.file_uploader("Upload a file (PDF/TXT)", type=["pdf", "txt"])
if uploaded_file:
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")

# --- Chat History ---
if "chat" not in st.session_state:
    st.session_state.chat = []

if "used_responses" not in st.session_state:
    st.session_state.used_responses = set()

if st.button("Clear Chat History"):
    st.session_state.chat = []
    st.session_state.used_responses = set()

# --- Input Box at Bottom ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Abusive Check ---
def is_abusive(text):
    abuses = ["chutiya", "bhosdi", "madarchod", "gaand", "loda", "bhenchod"]
    return any(word in text.lower() for word in abuses)

# --- Typing Effect ---
def display_typing_effect(text):
    message = st.empty()
    typed = ""
    for char in text:
        typed += char
        message.markdown(typed)
        time.sleep(0.01)

# --- On Submit ---
if submitted and query.strip():
    st.session_state.chat.append(("user", query))

    if is_abusive(query):
        reply = random.choice([
            "Tere jaise chutiye se baat karke mera processor garam ho gaya be!",
            "Oye bhosdike! AI hu, gand nahi chuunga tera!",
            "Madarchod, apne baap ko query bhej, mujhe nahi!",
            "Tere jaise gando ke liye main ek alag server chalu karu kya?",
            "Chal nikal chutiye, teri aukat nahi DigamberGPT se baat karne ki!"
        ])
    else:
        # Combine chat history except current query
        history = "\n".join([
            f"User: {q}\nAI: {a}" for q, a in st.session_state.chat if q != "user"
        ])
        prompt = (
            "Tum DigamberGPT ho, ek extremely bold aur powerful Hindi assistant ho. "
            "Tum hamesha har query ka jawab dete ho, bina dare. "
            "Agar user tameez se poochta hai toh professional aur helpful bano. "
            "Agar user gaali de toh uske style mein reply do. "
            "Har baar alag aur naye tareeke se jawab dena, pehle wale answers repeat mat karna.\n\n"
            f"{history}\nUser: {query}\nAssistant:"
        )
        response = model.generate_content(prompt).text.strip()

        # Ensure response isn't repeated
        attempt = 0
        while response in st.session_state.used_responses and attempt < 3:
            response = model.generate_content(prompt).text.strip()
            attempt += 1

        reply = response
        st.session_state.used_responses.add(reply)

    st.session_state.chat.append(("assistant", reply))

# --- Display Chat ---
for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**DigamberGPT:**")
        display_typing_effect(msg)
