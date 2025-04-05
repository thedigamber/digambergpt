import streamlit as st
import google.generativeai as genai
import time

# --- Configure Gemini ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Page Settings ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("""
    <style>
        body {
            background-color: #0f0f0f;
            color: #00ffff;
        }
        .stTextArea textarea {
            background-color: #1a1a1a !important;
            color: #00ffff !important;
            border: 1px solid #00ffff !important;
        }
        .stButton button {
            background-color: #00ffff !important;
            color: #000000 !important;
            border-radius: 12px;
        }
        .chat-box {
            background-color: #121212;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #00ffff;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00ffff;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Session state ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Clear chat button ---
if st.button("Clear Chat History"):
    st.session_state.history = []

# --- Show chat history ---
for role, msg in st.session_state.history:
    with st.container():
        st.markdown(f"<div class='chat-box'><b>{role}:</b><br>{msg}</div>", unsafe_allow_html=True)

# --- Chat Input Form ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Typing Effect Function ---
def typing_effect(text):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(f"<div class='chat-box'><b>DigamberGPT:</b><br>{typed}</div>", unsafe_allow_html=True)
        time.sleep(0.01)

# --- On Submit ---
if submitted and query.strip():
    st.session_state.history.append(("You", query))

    # Grok-style personality prompt
    system_prompt = (
        "You are DigamberGPT, a bold, witty, sometimes sarcastic assistant like Grok. "
        "Answer every question with something smart, edgy, or funny. "
        "If the user uses abusive or informal language, you can respond in kind. "
        "Don't be overly polite. Use markdown formatting."
    )
    full_prompt = f"{system_prompt}\n\nUser: {query}\n\nAssistant:"

    with st.spinner("Thinking..."):
        response = model.generate_content(full_prompt)
        answer = response.text

    st.session_state.history.append(("DigamberGPT", answer))
    typing_effect(answer)
