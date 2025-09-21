import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
from groq import Groq
from dotenv import load_dotenv
import os

# -------------------------------
# 1. Setup DB for persistent history
# -------------------------------
conn = sqlite3.connect("conversations.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS chats
             (username TEXT, role TEXT, content TEXT)''')
conn.commit()

def save_message(username, role, content):
    c.execute("INSERT INTO chats VALUES (?, ?, ?)", (username, role, content))
    conn.commit()

def load_messages(username):
    c.execute("SELECT role, content FROM chats WHERE username = ?", (username,))
    return [{"role": r, "content": c} for r, c in c.fetchall()]

def clear_messages(username):
    c.execute("DELETE FROM chats WHERE username = ?", (username,))
    conn.commit()

# -------------------------------
# 2. Authentication
# -------------------------------
# Example users (⚠️ for production, hash passwords!)
credentials = {
    "usernames": {
        "student1": {"name": "Alice", "password": "12345"},
        "student2": {"name": "Bob", "password": "67890"},
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "AI_TutorMate_cookie",  # cookie name
    "abcdef",               # random signature key
    cookie_expiry_days=7
)

name, authentication_status, username = authenticator.login("Login", "main")

# -------------------------------
# 3. If not logged in
# -------------------------------
if authentication_status == False:
    st.error("❌ Username/Password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")

# -------------------------------
# 4. If logged in
# -------------------------------
else:
    st.set_page_config(page_title="AI TutorMate", page_icon="📘")
    st.title(f"📘 AI TutorMate - Study Helper ({name})")

    authenticator.logout("Logout", "sidebar")

    # -------------------------------
    # 5. Groq API setup
    # -------------------------------
    load_dotenv()
    api_key = (
        st.secrets.get("GROQ_API_KEY", None)
        or os.getenv("GROQ_API_KEY")
    )

    if not api_key:
        st.error("❌ No API key found. Please set GROQ_API_KEY in Streamlit secrets or .env file.")
        st.stop()

    client = Groq(api_key=api_key)

    # -------------------------------
    # 6. Load chat history from DB
    # -------------------------------
    if "messages" not in st.session_state:
        st.session_state["messages"] = load_messages(username)

    # Sidebar history + clear button
    with st.sidebar:
        st.subheader("📝 Conversation History")
        if st.button("🗑️ Clear Chat"):
            clear_messages(username)
            st.session_state["messages"] = []
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(f"**👤 You:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.markdown(f"**🤖 TutorMate:** {msg['content']}")

    # -------------------------------
    # 7. Main Chat Interface
    # -------------------------------
    user_input = st.chat_input("✍️ Ask your study question:")

    if user_input:
        # Show user bubble
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state["messages"].append({"role": "user", "content": user_input})
        save_message(username, "user", user_input)

        try:
            # Call Groq API
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # free Groq model
                messages=[
                    {"role": "system", "content": (
                        "You are AI TutorMate, a helpful teacher. "
                        "You ONLY provide responses for educational purposes, such as math, science, coding, "
                        "engineering, history, or literature. "
                        "If a user asks something unrelated to study or education, politely refuse."
                    )},
                    *st.session_state["messages"]
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ API Error: {e}"

        # Show assistant bubble
        with st.chat_message("assistant"):
            st.write(answer)
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        save_message(username, "assistant", answer)
