import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import json

# Google Sheet ID
SHEET_ID = "11dW2cYbJ2kCjBE7KTSycsRphl5z9KfXWxoUDf13O5BY"
SHEET_NAME = "Sheet1"

# Load credentials from Streamlit secrets
def get_credentials():
    service_account_info = st.secrets["gcp_service_account"]
    return Credentials.from_service_account_info(json.loads(service_account_info))

# Load user data
def load_user_data():
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    return pd.DataFrame(data)
