import streamlit as st
import google.generativeai as genai
import time

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Streamlit Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")

# --- Custom Dark Neon Theme ---
st.markdown("""
    <style>
        body {
            background-color: #0f0f0f;
            color: #00ffff;
        }
        .stTextArea textarea {
            background-color: #1a1a1a !important;
            color: #00ffff !important;
        }
        .stButton>button {
            background-color: #00ffff;
            color: #000;
            font-weight: bold;
        }
        .stMarkdown {
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00ffff;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Session State for Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Clear Chat History ---
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# --- Display Previous Chat ---
for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**DigamberGPT:** {chat['bot']}")

# --- Chat Input at Bottom ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Handle Query ---
if submitted and query.strip():
    system_prompt = (
        "You are DigamberGPT, a helpful, friendly and smart assistant. "
        "Always respond like ChatGPT with a clear structure, bullet points, bold text for important parts, "
        "and code in markdown."
    )
    full_prompt = f"{system_prompt}\n\nUser: {query}\n\nAssistant:"
    
    with st.spinner("Thinking..."):
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
    
    st.session_state.chat_history.append({"user": query, "bot": response_text})

    # --- Typing Effect ---
    st.markdown("**You:** " + query)
    st.markdown("**DigamberGPT:** ", unsafe_allow_html=True)
    response_placeholder = st.empty()
    typed = ""
    for char in response_text:
        typed += char
        response_placeholder.markdown(typed)
        time.sleep(0.01)
