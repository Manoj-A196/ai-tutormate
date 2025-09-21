import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import datetime
from groq import Groq
from dotenv import load_dotenv
import os

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or "your_groq_api_key_here"
client = Groq(api_key=api_key)

# -----------------------------
# Database Setup
# -----------------------------
def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_message(username, role, content):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (username, role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def load_history(username):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute(
        "SELECT id, role, content, timestamp FROM messages WHERE username=? ORDER BY id",
        (username,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def delete_message(msg_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

def clear_all_history(username):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE username=?", (username,))
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(page_title="AI TutorMate", page_icon="📘", layout="wide")

# -----------------------------
# Authentication Setup
# -----------------------------
names = ["Alice", "Bob"]
usernames = ["alice", "bob"]
passwords = ["123", "456"]  # demo passwords
hashed_pw = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "password": hashed_pw[i]
        }
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "tutormate_cookie",
    "abcdef",
    cookie_expiry_days=30
)

name, auth_status, username = authenticator.login("Login", "sidebar")

# -----------------------------
# Login Handling
# -----------------------------
if auth_status is False:
    st.error("❌ Invalid username or password")
elif auth_status is None:
    st.warning("⚠️ Please enter username and password")
elif auth_status:
    st.sidebar.success(f"✅ Logged in as {name}")
    st.session_state.username = username

    authenticator.logout("Logout", "sidebar")

    # -----------------------------
    # CSS for Chat Bubbles
    # -----------------------------
    st.markdown("""
    <style>
    .chat-bubble-user {
        background-color: #dcf8c6;
        color: #000;
        padding: 10px 14px;
        border-radius: 18px;
        margin: 6px 0;
        max-width: 70%;
        align-self: flex-end;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
        position: relative;
    }
    .chat-bubble-assistant {
        background-color: #f1f0f0;
        color: #000;
        padding: 10px 14px;
        border-radius: 18px;
        margin: 6px 0;
        max-width: 70%;
        align-self: flex-start;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
        position: relative;
    }
    .timestamp {
        font-size: 11px;
        color: #555;
        margin-top: 3px;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Sidebar Controls
    # -----------------------------
    st.sidebar.subheader("⚙️ Chat Settings")
    if st.sidebar.button("🧹 Clear All History"):
        clear_all_history(username)
        st.success("✅ All history cleared!")
        st.rerun()

    # -----------------------------
    # Chat History Display
    # -----------------------------
    st.title("📘 AI TutorMate - Study Helper")
    st.subheader("📝 Conversation History")

    history = load_history(username)
    chat_container = st.container()

    with chat_container:
        for msg_id, role, content, timestamp in history:
            if role == "user":
                col1, col2 = st.columns([8,1])
                with col1:
                    st.markdown(
                        f"""
                        <div class="chat-message" style="align-items: flex-end;">
                            <div class="chat-bubble-user">
                                👤 {content}
                                <div class="timestamp">{timestamp}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col2:
                    if st.button("🗑️", key=f"del_{msg_id}"):
                        delete_message(msg_id)
                        st.rerun()

            elif role == "assistant":
                col1, col2 = st.columns([1,8])
                with col1:
                    if st.button("🗑️", key=f"del_{msg_id}"):
                        delete_message(msg_id)
                        st.rerun()
                with col2:
                    st.markdown(
                        f"""
                        <div class="chat-message" style="align-items: flex-start;">
                            <div class="chat-bubble-assistant">
                                🤖 {content}
                                <div class="timestamp">{timestamp}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # -----------------------------
    # Chat Input
    # -----------------------------
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    def send_message():
        user_msg = st.session_state.chat_input.strip()
        if not user_msg:
            return
        
        save_message(username, "user", user_msg)

        # Prepare context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are AI TutorMate, a helpful teacher. "
                    "You ONLY provide responses for educational purposes, "
                    "such as math, science, coding, engineering, history, or literature. "
                    "If asked something unrelated, politely refuse."
                )
            }
        ]
        history = load_history(username)
        for _, role, content, _ in history:
            messages.append({"role": role, "content": content})

        # Call Groq API
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ API Error: {str(e)}"

        save_message(username, "assistant", answer)

        # ✅ Clear input
        st.session_state.chat_input = ""
        st.rerun()

    # Input widget
    chat_input = st.text_area(
        "✍️ Type your message...",
        key="chat_input",
        label_visibility="collapsed",
        placeholder="Type your message and press Enter...",
        height=70
    )

    # Send button
    st.button("📤 Send", use_container_width=True, on_click=send_message)

    # Enter-to-send script
    st.markdown("""
    <script>
    const textarea = window.parent.document.querySelector('textarea[data-testid="stTextArea"]');
    if (textarea) {
        textarea.addEventListener("keydown", function(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const sendButton = window.parent.document.querySelector('button[kind="secondaryFormSubmit"]');
                if (sendButton) sendButton.click();
            }
        });
    }
    </script>
    """, unsafe_allow_html=True)
