import streamlit as st
import google.generativeai as genai
import time
import random

from modules.chatbot import chatbot_ui
from modules.image_gen import image_gen_ui
from modules.file_reader import file_reader_ui
from modules.settings import settings_ui
from modules.apk_download import apk_ui

st.set_page_config(page_title="DigamberGPT", layout="wide")
st.markdown("<h1 style='text-align: center; color:#39ff14;'>DigamberGPT</h1>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Chat", "Images", "Files", "Settings", "APK"])

with tab1:
    chatbot_ui()

with tab2:
    image_gen_ui()

with tab3:
    file_reader_ui()

with tab4:
    settings_ui()

with tab5:
    apk_ui()
