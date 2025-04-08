import streamlit as st

# Hardcoded credentials for simplicity
USER_CREDENTIALS = {
    "user1": "password1",
    "user2": "password2",
    "admin": "adminpass"
}

def login():
    st.title("Login")

    # Input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Button to trigger login
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.success("Login successful!")
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Invalid username or password")

def signup():
    st.title("Signup")

    # Input fields for new username and password
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")

    # Button to trigger signup
    if st.button("Signup"):
        if new_username in USER_CREDENTIALS:
            st.error("Username already exists")
        else:
            USER_CREDENTIALS[new_username] = new_password
            st.success("Signup successful! Please login.")
            st.session_state.signup_complete = True

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "signup_complete" not in st.session_state:
        st.session_state.signup_complete = False

    if st.session_state.logged_in:
        st.write(f"Welcome, {st.session_state.username}!")
        # Add your main app code here
    else:
        if st.session_state.signup_complete:
            login()
        else:
            option = st.selectbox("Choose an option", ["Login", "Signup"])
            if option == "Login":
                login()
            else:
                signup()

if __name__ == "__main__":
    main()
