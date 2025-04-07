

def chatbot_ui():
    user_input = st.text_input('Ask me anything')
    if user_input:
        st.info('Typing...')
        response = generate_gemini_response(user_input)
        st.success(response)
      
