import streamlit as st
import streamlit_authenticator as stauth
from groq import Groq
from dotenv import load_dotenv
import os

from chat_db import init_db, save_message, load_messages, clear_history

# Initialize DB
init_db()

# Load secrets
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
client = Groq(api_key=API_KEY)

# Dummy users (can move to config.yaml later)
users = {
    "alice": {"name": "Alice", "password": "abc123"},
    "bob": {"name": "Bob", "password": "xyz123"},
}

# Hash passwords
hashed_passwords = stauth.Hasher([u["password"] for u in users.values()]).generate()

# Auth config
credentials = {
    "usernames": {
        username: {"name": u["name"], "password": pw}
        for username, u, pw in zip(users.keys(), users.values(), hashed_passwords)
    }
}

# Authenticator
authenticator = stauth.Authenticate(
    credentials,
    "ai_tutormate_cookie",
    "abcdef123456",
    cookie_expiry_days=1
)

# Login
name, auth_status, username = authenticator.login("Login", "sidebar")

if auth_status:
    st.title("📘 AI TutorMate - Study Helper")

    # Sidebar
    st.sidebar.subheader(f"👋 Welcome, {name}")
    if st.sidebar.button("🗑️ Clear Chat History"):
        clear_history(username)
        st.sidebar.success("History cleared!")

    # Load conversation
    if "messages" not in st.session_state:
        st.session_state["messages"] = load_messages(username)

    # Chat UI
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Input
    if user_input := st.chat_input("✍️ Ask your study question:"):
        # Save & display user message
        save_message(username, "user", user_input)
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # AI Response
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state["messages"],
                temperature=0.7,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ Error: {str(e)}"

        # Save & display assistant message
        save_message(username, "assistant", answer)
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)

    # Logout
    authenticator.logout("Logout", "sidebar")

elif auth_status is False:
    st.error("❌ Invalid username or password")
elif auth_status is None:
    st.warning("👆 Please login to continue")
