import toml
secrets = toml.load(".streamlit/secrets.toml")
api_key = secrets["gemini"]["api_key"]
service_account_token = secrets["gemini"]["service_account_token"]
import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="DigamberGPT", layout="centered")

# Load API keys and credentials from Streamlit secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Setup Google Sheets credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_SHEETS_CREDENTIALS"], scope)
client = gspread.authorize(creds)

# Function to get responses from Gemini
def get_response_from_gemini(prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.title("DigamberGPT - Gemini + Google Sheets")

user_input = st.text_area("Apna sawaal likho...")

if st.button("Bhej do Gemini ko"):
    if user_input.strip() == "":
        st.warning("Kuchh likhna toh padega bhai!")
    else:
        with st.spinner("Gemini soch raha hai..."):
            output = get_response_from_gemini(user_input)
            st.success("Gemini ka jawab mil gaya:")
            st.write(output)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load Google Sheets credentials
google_creds = {
    "type": secrets["google_sheets"]["type"],
    "project_id": secrets["google_sheets"]["project_id"],
    "private_key_id": secrets["google_sheets"]["private_key_id"],
    "private_key": secrets["google_sheets"]["private_key"],
    "client_email": secrets["google_sheets"]["client_email"],
    "client_id": secrets["google_sheets"]["client_id"],
    "auth_uri": secrets["google_sheets"]["auth_uri"],
    "token_uri": secrets["google_sheets"]["token_uri"],
    "auth_provider_x509_cert_url": secrets["google_sheets"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": secrets["google_sheets"]["client_x509_cert_url"]
}

# Set up gspread client
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
gc = gspread.authorize(credentials)

# Open the spreadsheet by ID
sheet = gc.open_by_key("11dW2cYbJ2kCjBE7KTSycsRphl5z9KfXWxoUDf13O5BY").sheet1

# Example read
first_row = sheet.row_values(1)
print("First row from Google Sheet:", first_row)
