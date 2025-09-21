import streamlit as st
import sqlite3
import datetime
from groq import Groq
from dotenv import load_dotenv
import os

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or "your_groq_api_key_here"
client = Groq(api_key=api_key)

st.set_page_config(page_title="📘 AI TutorMate", page_icon="📘", layout="wide")

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_message(username, role, content):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
              (username, role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def load_history(username):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages WHERE username=? ORDER BY id", (username,))
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

def register_user(username, password):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# Initialize DB
init_db()

# -----------------------------
# Sidebar Login/Register
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.sidebar.title("🔑 User Login")

if not st.session_state.logged_in:
    choice = st.sidebar.radio("Choose Action", ["Login", "Register"])

    if choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid username or password")

    elif choice == "Register":
        new_username = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Register"):
            if register_user(new_username, new_password):
                st.sidebar.success("✅ Registered successfully! Please login.")
            else:
                st.sidebar.error("⚠️ Username already exists.")

# -----------------------------
# Main Chat UI
# -----------------------------
if st.session_state.logged_in:
    st.sidebar.write(f"👤 Logged in as **{st.session_state.username}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Clear All History
    st.sidebar.subheader("⚙️ Chat Settings")
    if st.sidebar.button("🧹 Clear All History"):
        clear_all_history(st.session_state.username)
        st.success("✅ All history cleared!")
        st.rerun()

    # Load history
    history = load_history(st.session_state.username)

    st.title("📘 AI TutorMate - Study Helper")

    # -----------------------------
    # Chat Bubble Styles
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
    # Display Conversation
    # -----------------------------
    st.subheader("📝 Conversation History")

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
    # Auto-scroll
    # -----------------------------
    st.markdown(
        """
        <script>
        var chatContainer = window.parent.document.querySelector('.main');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        </script>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # Chat Input
    # -----------------------------
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    user_input = st.text_area(
        "✍️ Type your message...",
        key="chat_input",
        label_visibility="collapsed",
        placeholder="Type your message and press Enter...",
    )

    send_btn = st.button("📤 Send", use_container_width=True)

    # Enter-to-Send JS
    st.markdown(
        """
        <script>
        const textarea = window.parent.document.querySelector('textarea[data-testid="stTextArea-text_input"]');
        if (textarea) {
            textarea.addEventListener("keydown", function(event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    const sendButton = window.parent.document.querySelector('button[kind="secondaryFormSubmit"]');
                    if (sendButton) { sendButton.click(); }
                }
            });
        }
        </script>
        """,
        unsafe_allow_html=True
    )

    if send_btn and user_input.strip():
        # Save user message
        save_message(st.session_state.username, "user", user_input.strip())

        # Prepare context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are AI TutorMate, a helpful teacher. "
                    "You ONLY provide responses for educational purposes. "
                    "If asked something unrelated to study, politely refuse."
                )
            }
        ]
        for _, role, content, _ in history + [(0, "user", user_input.strip(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]:
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

        # Save assistant reply
        save_message(st.session_state.username, "assistant", answer)

        # Clear input
        st.session_state.chat_input = ""

        st.rerun()
