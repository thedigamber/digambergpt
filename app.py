import streamlit as st
import google.generativeai as genai

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Streamlit Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- UI (Textbox at Bottom) ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- ChatGPT-style Prompt and Response ---
if submitted and query.strip():
    system_prompt = (
        "You are DigamberGPT, a helpful, friendly and smart assistant. "
        "Always respond in a clear and structured way like ChatGPT. "
        "Use bullet points, bold important parts, and format code in markdown."
    )
    full_prompt = f"{system_prompt}\n\nUser: {query}\n\nAssistant:"

    with st.spinner("Thinking..."):
        response = model.generate_content(full_prompt)
        st.success("Response:")
        st.markdown(response.text)
