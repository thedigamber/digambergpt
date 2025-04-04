import streamlit as st
import google.generativeai as genai
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont
import io
import time

# Set API Keys
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Gemini Model
model = genai.GenerativeModel('models/gemini-2.0-flash')

# Streamlit Page Config
st.set_page_config(page_title="DigamberGPT - All In One Shayari AI", layout="centered")
st.title("DigamberGPT - Sab AI ka Baap (Shayari + Image + Download)")
st.markdown("Jo bhi poochho, milega shayari mein jawab — ek khoobsurat image ke saath!")

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-google-sheets-credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("DigamberGPT-Premium").sheet1  # Sheet ka naam yahan set karo

# User Authentication
user_email = st.text_input("Apna Email ID daalo (for premium access):")
if not user_email:
    st.warning("Premium access ke liye email enter karo!")
    st.stop()

# Check if user is premium
all_users = sheet.get_all_records()
premium_users = {row['Email']: row['Type'] for row in all_users}
user_type = premium_users.get(user_email, "free")

# Free Users Limit
if user_type == "free":
    user_time_key = f"{user_email}_time"
    user_count_key = f"{user_email}_count"

    if user_time_key not in st.session_state:
        st.session_state[user_time_key] = time.time()
        st.session_state[user_count_key] = 0

    time_elapsed = time.time() - st.session_state[user_time_key]
    
    if time_elapsed > 3600:  # 1 hour reset
        st.session_state[user_time_key] = time.time()
        st.session_state[user_count_key] = 0

    if st.session_state[user_count_key] >= 20:
        st.error("Aap free user hain, aur aapka limit (20 queries/hour) khatam ho chuka hai. Upgrade to premium!")
        st.stop()

# Input Prompt
prompt = st.text_input("Apna sawaal likho yahan:")

if prompt:
    with st.spinner("DigamberGPT soch raha hai..."):
        
        # Increment query count for free users
        if user_type == "free":
            st.session_state[user_count_key] += 1
        
        # Shayari Generation
        final_prompt = f"Tum ek AI ho jo har topic (love, coding, life, science) ka jawab shayari mein deta hai.\nSawaal: {prompt}\nShayari mein jawab do:"
        try:
            response = model.generate_content(final_prompt)
            shayari = response.text.strip()
        except:
            shayari = "Kuchh galti ho gayi bhai... AI thoda emotional ho gaya hai!"

        # Image Generation
        image_url = f"https://lexica.art/api/v1/search?q={prompt}"
        try:
            img_data = requests.get(image_url).json()
            image_link = img_data["images"][0]["srcSmall"]
            background = Image.open(requests.get(image_link, stream=True).raw).convert("RGBA")
        except:
            background = Image.new("RGBA", (600, 600), (30, 30, 30))

        # Shayari Overlay
        draw = ImageDraw.Draw(background)
        try:
            font = ImageFont.truetype("arial.ttf", size=28)
        except:
            font = ImageFont.load_default()

        margin = 40
        offset = 50
        for line in shayari.split("\n"):
            draw.text((margin, offset), line, font=font, fill="white")
            offset += 40

        # Display Shayari & Image
        st.markdown(f"**DigamberGPT ki Shayari:**\n\n{shayari}")
        st.image(background, caption="Shayari Image")

        # Download Button
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        st.download_button(
            label="Download Shayari Image",
            data=img_byte_arr.getvalue(),
            file_name="digambergpt_shayari.png",
            mime="image/png"
        )

        # Bonus: Generate Hashtags
        hashtag_prompt = f"Generate 10 trending Hindi poetry hashtags for this theme: {prompt}"
        try:
            hashtags = model.generate_content(hashtag_prompt).text.strip()
            st.markdown(f"**Instagram Hashtags:**\n\n{hashtags}")
        except:
            st.markdown("_Hashtags generate nahi ho paaye..._")
