import streamlit as st
import google.generativeai as genai

# Streamlit page config
st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖", layout="centered")

# Apply custom CSS for stylish UI
st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: white;
    }
    .stChatInput > div {
        border: 1px solid #ff4b4b;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Gemini API Key
GEMINI_API_KEY = "AIzaSyCHXLmu1SIn8NVCkkSLORILH7eMXzSlA_k"

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Chatbot UI
st.title("🤖 Gemini AI Chatbot")
st.write("Ask me anything!")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display previous messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Gemini API Call
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(user_input)
    bot_reply = response.text.strip()
    
    # Display bot response
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
