import streamlit as st
import google.generativeai as genai

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Streamlit Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)
st.write("")

# --- Chat UI (Text area at bottom) ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Response Logic ---
if submitted and query.strip():
    with st.spinner("Thinking..."):
        response = model.generate_content(query)
        st.success("Response:")
        st.markdown(response.text)
