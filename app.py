import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import google.generativeai as genai

# Load secrets
genai_api_key = st.secrets["gemini"]["api_key"]
creds_dict = st.secrets["gcp_service_account"]

# Configure Gemini
genai.configure(api_key=genai_api_key)

# Authenticate with Google Sheets
creds = Credentials.from_service_account_info(creds_dict)
client = gspread.authorize(creds)
sheet = client.open("digambergpt").sheet1

# Streamlit UI
st.title("DigamberGPT")

menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

def find_user(email):
    users = sheet.get_all_records()
    for i, user in enumerate(users):
        if user["Email"].lower() == email.lower():
            return i + 2, user  # +2 because get_all_records starts after headers, and Google Sheets rows start from 1
    return None, None

if choice == "Signup":
    st.subheader("Create New Account")
    new_email = st.text_input("Email")
    user_type = st.selectbox("Select User Type", ["free", "premium"])
    if st.button("Signup"):
        row, existing = find_user(new_email)
        if existing:
            st.warning("User already exists.")
        else:
            now = datetime.datetime.now().isoformat()
            sheet.append_row([new_email, user_type, 0, now])
            st.success("Signup successful! Please login.")

elif choice == "Login":
    st.subheader("Login to your account")
    email = st.text_input("Email")
    if st.button("Login"):
        row, user_data = find_user(email)
        if user_data:
            st.session_state["email"] = email
            st.session_state["user_type"] = user_data["user type"]
            st.success(f"Welcome {email}!")
        else:
            st.error("User not found. Please signup first.")

# After login
if "email" in st.session_state:
    st.subheader("Chat with DigamberGPT")

    prompt = st.text_input("You:", key="input")
    if st.button("Send"):
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat(history=[])
        response = chat.send_message(prompt)
        st.markdown(f"**Bot:** {response.text}")

        # Update query count
        row, user_data = find_user(st.session_state["email"])
        if row and user_data:
            current_queries = int(user_data["queries the hostime"]) + 1
            now = datetime.datetime.now().isoformat()
            sheet.update(f"C{row}", current_queries)  # queries the hostime
            sheet.update(f"D{row}", now)             # last query time
