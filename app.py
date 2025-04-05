import streamlit as st
import google.generativeai as genai

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["gemini"]["api_key"])
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Streamlit Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)
st.write("---")

# --- Initialize Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Display Previous Messages ---
for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**DigamberGPT:** {chat['bot']}")

# --- Text Input Box at Bottom ---
with st.form("chat_form", clear_on_submit=True):
    query = st.text_area("Ask me anything...", key="input_text", height=100)
    submitted = st.form_submit_button("Send")

# --- Handle Submission ---
if submitted and query.strip():
    # Prompt with friendly tone
    system_prompt = (
        "You are DigamberGPT, a helpful, friendly and smart assistant. "
        "Always respond in a clear and structured way like ChatGPT. "
        "Use markdown formatting, bullet points, and code blocks if needed."
    )
    full_prompt = f"{system_prompt}\n\nUser: {query}\n\nAssistant:"

    with st.spinner("Thinking..."):
        response = model.generate_content(full_prompt)
        answer = response.text

    # Show response
    st.markdown(f"**You:** {query}")
    st.markdown(f"**DigamberGPT:** {answer}")

    # Save in session state
    st.session_state.chat_history.append({"user": query, "bot": answer})
