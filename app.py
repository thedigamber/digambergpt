import google.generativeai as genai
import streamlit as st

# API key load karna (Secrets se ya direct)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Sahi Model Load Karna
model = genai.GenerativeModel('gemini-2.0-flash')

st.set_page_config(page_title="DigamberGPT - Gemini Shayari AI", layout="centered")
st.title("DigamberGPT - Poetic AI Powered by Gemini")
st.markdown("**Har topic ka jawab milega, lekin ek shayari ke andaaz mein!**")

prompt = st.text_input("Apna sawaal likho yahan:")

if prompt:
    with st.spinner("DigamberGPT soch raha hai..."):
        final_prompt = (
            "Tum ek AI ho jo har topic (science, love, coding, gyaan) pe baat karta hai, "
            "lekin har jawab shayari mein deta hai. Ab iska jawab do shayari ke style mein:\n\n"
            f"{prompt}"
        )
        try:
            response = model.generate_content(final_prompt)
            st.markdown(f"**DigamberGPT:**\n\n{response.text}")
        except Exception as e:
            st.error(f"Error: {e}")
