import streamlit as st
import google.generativeai as genai
import time

# --- Gemini Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("""
    <style>
    body { background-color: #0f0f0f; color: #00ffff; }
    textarea, .stTextInput>div>div>input {
        background-color: #111 !important; color: #0ff !important;
    }
    .neon-btn {
        background-color: #0ff;
        color: black;
        font-weight: bold;
        border-radius: 8px;
        padding: 8px 16px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Clear Chat Button ---
if st.button("Clear Chat History", key="clear"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# --- File Upload ---
uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "docx"])
if uploaded_file:
    st.success(f"Uploaded file: {uploaded_file.name}")

# --- User Input Form (Textbox at Bottom) ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Check if message is abusive ---
def is_abusive(text):
    abusive_words = ["gandu", "madarchod", "bhosdike", "chutiya"]
    return any(word in text.lower() for word in abusive_words)

# --- Generate Response ---
if submitted and query.strip():
    full_prompt = ""

    # Add chat history for memory
    for turn in st.session_state.chat_history:
        full_prompt += f"User: {turn['user']}\nAssistant: {turn['bot']}\n"

    # Add current input
    full_prompt += f"User: {query}\nAssistant:"

    # Special Grok-style reply for abuse
    if is_abusive(query):
        reply = "Tere jaise chutiye se baat karke mera processor garam ho gaya be!"
    else:
        with st.spinner("Thinking..."):
            response = model.generate_content(full_prompt)
            reply = response.text.strip()

    # Update chat history
    st.session_state.chat_history.append({"user": query, "bot": reply})

# --- Display Chat History ---
for msg in st.session_state.chat_history:
    st.markdown(f"**You:** {msg['user']}")
    with st.spinner("DigamberGPT is typing..."):
        time.sleep(1.2)
        st.markdown(f"<div style='color:#0ff;'>**DigamberGPT:** {msg['bot']}</div>", unsafe_allow_html=True)

# --- Avatar (Just for style) ---
st.markdown("<p style='text-align: center;'>Powered by <strong style='color:#0ff;'>DigamberGPT</strong> — Your AI Partner</p>", unsafe_allow_html=True)
