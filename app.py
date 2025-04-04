import streamlit as st
import google.generativeai as genai
import toml

# Load API key from secrets
with open("secret.toml", "r") as f:
    secrets = toml.load(f)

genai.configure(api_key=secrets["GEMINI_API_KEY"])

# Streamlit UI Setup with Full Neon Look
st.set_page_config(page_title="DIGAMBERGPT", page_icon="🤖")

st.markdown(
    """
    <style>
        body {
            background-color: black;
            color: #00FFFF;
            font-family: 'Courier New', monospace;
        }
        .stTextInput, .stTextArea, .stButton > button {
            background-color: #111;
            color: #0ff;
            border: 2px solid #0ff;
            padding: 10px;
            font-size: 18px;
        }
        .stTextInput:hover, .stTextArea:hover, .stButton > button:hover {
            background-color: #222;
            color: #fff;
            border: 2px solid #ff0;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center; color: #0ff; font-size: 50px;'>DIGAMBERGPT 🤖</h1>", unsafe_allow_html=True)

st.write("### Ask me anything!")
user_input = st.text_input("", placeholder="Type your message...")

if user_input:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(user_input)
    
    st.markdown(
        f"""
        <div style='border: 2px solid #0ff; padding: 10px; border-radius: 10px; background-color: #111;'>
            <p style='color: #0ff; font-size: 18px;'>{response.text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
