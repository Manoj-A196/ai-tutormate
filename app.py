import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq
import datetime

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    role TEXT,
    content TEXT,
    timestamp TEXT
)
""")
conn.commit()

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or "your_groq_api_key_here"
client = Groq(api_key=api_key)

st.set_page_config(page_title="AI TutorMate", page_icon="📘", layout="wide")

# -----------------------------
# Authentication
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

def login(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone() is not None

def register(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except:
        return False

def clear_history(username):
    cursor.execute("DELETE FROM conversations WHERE username=?", (username,))
    conn.commit()

def delete_message(msg_id, username):
    cursor.execute("DELETE FROM conversations WHERE id=? AND username=?", (msg_id, username))
    conn.commit()

def get_history(username):
    cursor.execute("SELECT id, role, content, timestamp FROM conversations WHERE username=? ORDER BY id", (username,))
    return cursor.fetchall()

def save_message(username, role, content):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO conversations (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
                   (username, role, content, timestamp))
    conn.commit()

# -----------------------------
# Login / Register UI
# -----------------------------
if not st.session_state.logged_in:
    choice = st.sidebar.radio("Menu", ["Login", "Register"])

    if choice == "Login":
        st.subheader("🔑 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome back, {username}!")
            else:
                st.error("❌ Invalid username or password")

    elif choice == "Register":
        st.subheader("📝 Register")
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register(username, password):
                st.success("✅ Registration successful! Please login.")
            else:
                st.error("⚠️ Username already exists")

# -----------------------------
# Chat Interface
# -----------------------------
else:
    st.title("📘 AI TutorMate - Study Helper")

    # Sidebar controls
    st.sidebar.subheader(f"📝 {st.session_state.username}'s Options")

    if st.sidebar.button("🧹 Clear All History"):
        clear_history(st.session_state.username)
        st.sidebar.success("✅ All history cleared!")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None

    # Load conversation
    history = get_history(st.session_state.username)

    # -----------------------------
    # Scrollable Chat Container + Auto-scroll
    # -----------------------------
    st.subheader("💬 Chat")

    chat_container = """
    <div id="chat-box" style='height:500px; overflow-y:scroll; border:1px solid #ddd; 
    padding:10px; border-radius:10px; background-color:#fafafa;'>
    """
    for msg_id, role, content, timestamp in history:
        if role == "user":
            chat_container += f"""
            <div style='text-align:right; background-color:#DCF8C6; padding:10px;
            border-radius:10px; margin:5px 0; max-width:70%; float:right; clear:both; position:relative;'>
            <b>👤 You</b> <br> {content} <br>
            <small style='color:gray;'>{timestamp}</small><br>
            <a href="?delete={msg_id}" style="color:red; font-size:12px;">🗑 Delete</a>
            </div>
            """
        else:
            chat_container += f"""
            <div style='text-align:left; background-color:#F1F0F0; padding:10px;
            border-radius:10px; margin:5px 0; max-width:70%; float:left; clear:both; position:relative;'>
            <b>🤖 TutorMate</b> <br> {content} <br>
            <small style='color:gray;'>{timestamp}</small><br>
            <a href="?delete={msg_id}" style="color:red; font-size:12px;">🗑 Delete</a>
            </div>
            """
    chat_container += "<div id='scroll-to-bottom'></div></div>"

    # Auto-scroll JS
    chat_container += """
    <script>
    var chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
    </script>
    """

    st.markdown(chat_container, unsafe_allow_html=True)

    # -----------------------------
    # Handle delete action
    # -----------------------------
    query_params = st.experimental_get_query_params()
    if "delete" in query_params:
        msg_id = query_params["delete"][0]
        delete_message(msg_id, st.session_state.username)
        st.experimental_set_query_params()  # clear params
        st.rerun()

    # -----------------------------
    # Custom CSS for chat input
    # -----------------------------
    st.markdown(
        """
        <style>
        .chat-container {
            position: fixed;
            bottom: 20px;
            left: 20%;
            right: 20%;
            display: flex;
            align-items: center;
            background: white;
            border-radius: 25px;
            padding: 5px 10px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #ddd;
            z-index: 1000;
        }
        .chat-input {
            flex-grow: 1;
            border: none;
            outline: none;
            padding: 10px;
            font-size: 16px;
            border-radius: 20px;
        }
        .send-btn {
            background: #25D366;
            border: none;
            color: white;
            padding: 10px 14px;
            margin-left: 5px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
        }
        .send-btn:hover {
            background: #20b858;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------
    # Input + Send Button
    # -----------------------------
    with st.form("chat_form", clear_on_submit=True):
        st.markdown(
            """
            <div class="chat-container">
                <textarea name="msg" class="chat-input" placeholder="✍️ Type your message..."></textarea>
                <button class="send-btn" type="submit">📤</button>
            </div>
            """,
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button("hidden_submit", type="primary", label_visibility="hidden")

    if submitted:
        user_input = st.experimental_get_query_params().get("msg", [""])[0]

        if user_input.strip():
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

            st.rerun()
