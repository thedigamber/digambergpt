import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai

# Google Sheet & Gemini API settings
SHEET_ID = '11dW2cYbJ2kCjBE7KTSycsRphl5z9KfXWxoUDf13O5BY'
SHEET_NAME = 'Sheet1'

# Load user data from Google Sheets
def load_user_data():
    creds = Credentials.from_service_account_file("deductive-team-455314-b0-84c8be162979.json")
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def authenticate(email, password, user_df):
    user = user_df[(user_df['email'] == email) & (user_df['password'] == password)]
    return not user.empty

# Gemini setup
genai.configure(api_key="84c8be162979fc2b2bd6f569b590e1bc23b4e4c3")
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Streamlit App
st.set_page_config(page_title="Gemini Chatbot", layout="centered")
st.title("Secure Gemini Chatbot")

# Session setup
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        df = load_user_data()
        if authenticate(email, password, df):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")
else:
    st.success("Welcome to the chat!")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.markdown(f"**{msg['role'].capitalize()}:** {msg['text']}")

    user_input = st.text_input("Type your message:")

    if user_input:
        st.session_state.messages.append({"role": "user", "text": user_input})
        response = chat.send_message(user_input)
        st.session_state.messages.append({"role": "ai", "text": response.text})
        st.experimental_rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.experimental_rerun()
