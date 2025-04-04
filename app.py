import streamlit as st
import google.generativeai as genai

# API key streamlit secrets se lo
api_key = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=api_key)

# Gemini model load karo
model = genai.GenerativeModel('gemini-pro')

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

        response = model.generate_content(final_prompt)

        if response and response.candidates:
            shayari_output = response.candidates[0].content  
            st.markdown(f"**DigamberGPT:**\n\n{shayari_output}")
        else:
            st.error("Koi response nahi mila. API key check karo ya Gemini model active hai ki nahi dekho.")
