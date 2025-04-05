import streamlit as st
import google.generativeai as genai

# --- Gemini API Setup ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Streamlit UI ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("<h1 style='text-align: center; color: cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Session State to Store Response ---
if "response" not in st.session_state:
    st.session_state.response = ""

# --- Show Previous Response (if any) ---
if st.session_state.response:
    st.success("Response:")
    st.write(st.session_state.response)

# --- Input Box at the Bottom ---
with st.form("query_form", clear_on_submit=True):
    query = st.text_area("Ask your question:")
    submitted = st.form_submit_button("Send")

    if submitted and query.strip() != "":
        with st.spinner("Thinking..."):
            response = model.generate_content(query)
            st.session_state.response = response.text
        st.experimental_rerun()
