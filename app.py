import streamlit as st
import google.generativeai as genai
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image, ImageDraw, ImageFont
import io
import time

# Streamlit Config
st.set_page_config(page_title="DigamberGPT - All In One Shayari AI", layout="centered")
st.title("DigamberGPT - Sab AI ka Baap (Shayari + Image + Download)")
st.markdown("Jo bhi poochho, milega shayari mein jawab — ek khoobsurat image ke saath!")

# Gemini API Setup
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-2.0-flash')

# Google Sheets Authentication (No JSON parsing now)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_SHEETS_CREDENTIALS"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/11dW2cYbJ2kCjBE7KTSycsRphl5z9KfXWxoUDf13O5BY/edit").sheet1

# User Input
prompt = st.text_input("Apna sawaal likho yahan:")
user_ip = st.session_state.get("ip", str(time.time()))

# Query Count System
rows = sheet.get_all_records()
user_data = next((row for row in rows if row['user'] == user_ip), None)
current_time = int(time.time())

if user_data:
    last_time = int(user_data['last'])
    count = int(user_data['count'])
    premium = user_data['premium'].lower() == "yes"

    if not premium and current_time - last_time < 3600 and count >= 20:
        st.warning("Free user ho tum, 20 queries/hour limit poori ho gayi hai. Premium lo aur masti karo!")
        st.stop()
    elif current_time - last_time >= 3600:
        sheet.update_cell(rows.index(user_data)+2, 2, current_time)
        sheet.update_cell(rows.index(user_data)+2, 3, 1)
    else:
        sheet.update_cell(rows.index(user_data)+2, 3, count + 1)
else:
    sheet.append_row([user_ip, current_time, 1, "no"])

if prompt:
    with st.spinner("DigamberGPT soch raha hai..."):

        final_prompt = (
            "Tum ek AI ho jo har topic (love, coding, life, science) ka jawab shayari mein deta hai."
            f"\nSawaal: {prompt}\nShayari mein jawab do:"
        )
        try:
            response = model.generate_content(final_prompt)
            shayari = response.text.strip()
        except:
            shayari = "Kuchh galti ho gayi bhai... AI thoda emotional ho gaya hai!"

        # Image from Lexica
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

        # Show Result
        st.markdown(f"**DigamberGPT ki Shayari:**\n\n{shayari}")
        st.image(background, caption="Shayari Image")

        # Download Option
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        st.download_button(
            label="Download Shayari Image",
            data=img_byte_arr.getvalue(),
            file_name="digambergpt_shayari.png",
            mime="image/png"
        )

        # Hashtag Generator
        hashtag_prompt = f"Generate 10 trending Hindi poetry hashtags for this theme: {prompt}"
        try:
            hashtags = model.generate_content(hashtag_prompt).text.strip()
            st.markdown(f"**Instagram Hashtags:**\n\n{hashtags}")
        except:
            st.markdown("_Hashtags generate nahi ho paaye..._")
