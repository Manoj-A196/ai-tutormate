import streamlit as st
import streamlit_authenticator as stauth
import os
from groq import Groq

# -------------------------
# User authentication setup
# -------------------------
names = ["Alice", "Bob"]
usernames = ["alice", "bob"]
passwords = ["abc123", "xyz123"]

# Hash passwords
hashed_pw = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {"name": names[i], "password": hashed_pw[i]}
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "ai_tutormate_cookie",
    "abcdef",
    cookie_expiry_days=30,
)

name, authentication_status, username = authenticator.login("Login", "main")

# -------------------------
# UI if login successful
# -------------------------
if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name} 👋")

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    # Sidebar chat history management
    st.sidebar.subheader("💬 Conversation History")

    # Show saved chats
    if st.session_state.chat_history:
        chat_titles = [f"Chat {i+1}" for i in range(len(st.session_state.chat_history))]
        selected = st.sidebar.radio("Select a chat:", chat_titles, index=0)

        st.session_state.selected_chat = chat_titles.index(selected)

        # Delete selected chat
        if st.sidebar.button("🗑️ Delete Selected Chat"):
            del st.session_state.chat_history[st.session_state.selected_chat]
            st.session_state.selected_chat = None
            st.rerun()

    else:
        st.sidebar.write("No conversations yet.")

    # -------------------------
    # Chat Interface
    # -------------------------
    st.title("🤖 AI Tutormate")

    # Input field
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:", key="chat_input_field")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        # Add new conversation if none selected
        if st.session_state.selected_chat is None:
            st.session_state.chat_history.append([])
            st.session_state.selected_chat = len(st.session_state.chat_history) - 1

        # Save user message
        st.session_state.chat_history[st.session_state.selected_chat].append(
            {"role": "user", "content": user_input}
        )

        # Prepare messages for API
        messages_for_api = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.chat_history[st.session_state.selected_chat]
        ]

        # Connect to Groq API
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key) if api_key else None

        if client:
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages_for_api,
                    temperature=0.7,
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"⚠️ API Error: {e}"
        else:
            answer = "⚠️ No API key configured. Set GROQ_API_KEY to enable AI responses."

        # Save bot reply
        st.session_state.chat_history[st.session_state.selected_chat].append(
            {"role": "assistant", "content": answer}
        )

        # Clear input
        st.session_state.chat_input = ""
        st.rerun()

    # -------------------------
    # Display current chat
    # -------------------------
    if (
        st.session_state.selected_chat is not None
        and st.session_state.selected_chat < len(st.session_state.chat_history)
    ):
        st.subheader("📜 Current Conversation")
        for msg in st.session_state.chat_history[st.session_state.selected_chat]:
            if msg["role"] == "user":
                st.markdown(f"**🧑 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 AI:** {msg['content']}")

# -------------------------
# Authentication handling
# -------------------------
elif authentication_status is False:
    st.error("❌ Username/Password is incorrect")
elif authentication_status is None:
    st.warning("⚠️ Please enter your username and password")
