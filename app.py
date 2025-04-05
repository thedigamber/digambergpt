import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Google Sheets Auth
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
client = gspread.authorize(CREDS)
sheet = client.open("digambergpt").sheet1  # Sheet name

# Utility Functions
def get_all_users():
    return sheet.get_all_records()

def find_user(email):
    users = get_all_users()
    for i, user in enumerate(users):
        if user["Email"].lower() == email.lower():
            return user, i + 2  # gspread row index (header is row 1)
    return None, None

def signup_user(email, user_type="free"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([email, user_type, "0", now])
    return True

def update_last_query_time(row):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.update_cell(row, 4, now)

def upgrade_to_premium(row):
    sheet.update_cell(row, 2, "premium")

# Streamlit App
st.set_page_config(page_title="DigamberGPT", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = None
    st.session_state.user_type = "free"

st.title("Welcome to DigamberGPT")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        login_email = st.text_input("Email", key="login_email")
        if st.button("Login"):
            user, row = find_user(login_email)
            if user:
                st.session_state.logged_in = True
                st.session_state.email = login_email
                st.session_state.user_type = user["user type"]
                update_last_query_time(row)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("User not found. Please sign up.")

    with tab2:
        signup_email = st.text_input("Email", key="signup_email")
        if st.button("Sign Up"):
            user, _ = find_user(signup_email)
            if user:
                st.warning("User already exists. Please login.")
            else:
                signup_user(signup_email)
                st.success("Signup successful! Please login.")

else:
    st.success(f"Welcome, {st.session_state.email}!")
    st.write(f"**Account Type:** {st.session_state.user_type.capitalize()}")

    if st.session_state.user_type == "premium":
        st.info("You have access to premium features!")
        # Add premium-only features here
    else:
        st.warning("You are using a free account.")
        if st.button("Upgrade to Premium"):
            _, row = find_user(st.session_state.email)
            if row:
                upgrade_to_premium(row)
                st.session_state.user_type = "premium"
                st.success("Upgraded to Premium!")
                st.rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.email = None
        st.session_state.user_type = "free"
        st.success("Logged out!")
        st.rerun()
