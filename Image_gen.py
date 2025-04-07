# --- Stability AI Image Generation Function ---
def generate_image_stability(prompt):
    try:
        # Check if API key exists
        if "stability" not in st.secrets or "key" not in st.secrets["stability"]:
            st.error("Stability API key not configured properly")
            return None
            
        stability_api = client.StabilityInference(
            key=st.secrets["stability"]["key"],
            verbose=True,
        )

        answers = stability_api.generate(
            prompt=prompt,
            seed=12345,
            steps=50,
            cfg_scale=8.0,
            width=512,
            height=512,
            samples=1,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )

        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    st.warning("Prompt blocked by safety filter. Try something else.")
                    return None
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(io.BytesIO(artifact.binary))
                    return img
                    
    except Exception as e:
        st.error(f"Image generation failed: {str(e)}")
        return None

# --- Page Config ---
st.set_page_config(page_title="DigamberGPT", layout="centered")
st.markdown("""
    <style>
    body { background-color: #0f0f0f; color: #39ff14; }
    .stTextArea textarea { background-color: #1a1a1a; color: white; }
    .stButton button { background-color: #39ff14; color: black; border-radius: 10px; }
    .chat-bubble {
        background-color: #1a1a1a; border-radius: 10px; padding: 10px;
        margin: 5px 0; color: white; white-space: pre-wrap; word-wrap: break-word;
    }
    .tab-content { padding: 10px; }
    </style>
    <script>
    document.addEventListener("DOMContentLoaded", function () {
        const textarea = parent.document.querySelector('textarea');
        if (textarea) {
            textarea.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    const btn = parent.document.querySelector('button[kind="primary"]');
                    if (btn) btn.click();
                }
            });
        }
    });
    </script>
""", unsafe_allow_html=True)

# --- Title & Avatar ---
col1, col2 = st.columns([1, 8])
with col1:
    st.image("https://i.imgur.com/3v5p4UQ.png", width=50)
with col2:
    st.markdown("<h1 style='color:cyan;'>DigamberGPT</h1>", unsafe_allow_html=True)

# --- Tab Layout ---
tab1, tab2 = st.tabs(["Chat", "Image Generator"])

with tab1:
    # --- Session Initialization ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {"New Chat": []}
    if "selected_history" not in st.session_state:
        st.session_state.selected_history = "New Chat"
    if "new_chat_created" not in st.session_state:
        st.session_state.new_chat_created = False

    # --- Sidebar (Scrollable History Buttons) ---
    with st.sidebar:
        st.markdown("""
            <style>
            .chat-history {
                max-height: 300px;
                overflow-y: auto;
                padding-right: 10px;
            }
            .chat-history button {
                width: 100%;
                text-align: left;
                margin-bottom: 5px;
                background-color: #262626;
                color: #39ff14;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
            .chat-history button:hover {
                background-color: #39ff14;
                color: black;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Chat History")
        st.markdown('<div class="chat-history">', unsafe_allow_html=True)

        # Add "New Chat" button separately
        if st.button("New Chat", key="new_chat_button"):
            new_chat_name = f"Chat {len(st.session_state.chat_history)}"
            st.session_state.chat_history[new_chat_name] = []
            st.session_state.selected_history = new_chat_name
            st.session_state.new_chat_created = True
            st.rerun()

        # Display existing chats
        for key in [k for k in st.session_state.chat_history.keys() if k != "New Chat"]:
            if st.button(key, key=key):
                st.session_state.selected_history = key
                st.session_state.new_chat_created = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        selected = st.session_state.selected_history

        if selected != "New Chat" and not st.session_state.new_chat_created:
            new_title = st.text_input("Rename Chat", value=selected, key="rename_input")
            if st.button("Save Name"):
                if new_title and new_title != selected:
                    st.session_state.chat_history[new_title] = st.session_state.chat_history.pop(selected)
                    st.session_state.selected_history = new_title
                    st.rerun()

            export_text = ""
            for role, msg in st.session_state.chat_history[selected]:
                prefix = "You" if role == "user" else "DigamberGPT"
                export_text += f"{prefix}: {msg}\n\n"

            st.download_button("Export Chat (.txt)", export_text, file_name=f"{selected.replace(' ', '_')}.txt", mime="text/plain")

            if st.button("Delete Chat"):
                del st.session_state.chat_history[selected]
                st.session_state.selected_history = "New Chat"
                st.session_state.new_chat_created = True
                st.rerun()

    # --- Options ---
    col1, col2 = st.columns(2)
    deep_think = col1.toggle("Deep Think", value=False)
    search_enabled = col2.toggle("Search", value=False)

    # --- File Upload ---

def image_gen_ui():
    prompt = st.text_input('Enter image prompt')
    if prompt:
        image_url = generate_image_stability(prompt)
        st.image(image_url, caption='Generated Image')
