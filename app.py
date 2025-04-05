import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime
import pytz
import json

# --- Load credentials from JSON file ---
with open("deductive-team-455314-b0-330466287823.json") as f:
    creds_dict = json.load(f)
creds = Credentials.from_service_account_info(creds_dict, scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)
sheet = client.open("digambergpt").sheet1

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")  # Use "gemini-2.0-flash" if available in your setup

# --- Streamlit UI ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Inputs ---
email = st.text_input("Enter your email")
password = st.text_input("Enter password", type="password")
query = st.text_area("Ask your question")
submit = st.button("Send")

# --- Authenticate user ---
def is_valid_user(email, password):
    users = sheet.get_all_records()
    for i, row in enumerate(users, start=2):
        if row["email"] == email and row["user_type"] == password:
            return i
    return None

# --- Handle AI query ---
def handle_query(q):
    response = model.generate_content(q)
    return response.text

# --- Process on click ---
if submit and email and password and query:
    row = is_valid_user(email, password)
    if row:
        with st.spinner("Thinking..."):
            reply = handle_query(query)
        st.success("Response:")
        st.write(reply)

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        queries = sheet.cell(row, 3).value or "0"
        sheet.update_cell(row, 3, str(int(queries) + 1))
        sheet.update_cell(row, 4, now.strftime("%Y-%m-%d %H:%M:%S"))

        st.experimental_rerun()
    else:
        st.error("Invalid email or password.")
