# app.py
import streamlit as st
import sqlite3
import datetime
from groq import Groq
from dotenv import load_dotenv
import os
import io

# Optional PDF support
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# -----------------------------
# Load API key (Streamlit secrets or .env)
# -----------------------------
load_dotenv()
api_key = st.secrets.get("GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
if not api_key:
    st.warning("No GROQ_API_KEY found — set it in Streamlit secrets or .env to enable the AI responses.")
else:
    client = Groq(api_key=api_key)

st.set_page_config(page_title="AI TutorMate", page_icon="📘", layout="wide")

# -----------------------------
# Helpers & DB
# -----------------------------
DB_PATH = "chat_history.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
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

def register_user(username, password):
    conn = get_conn()
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
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    r = c.fetchone()
    conn.close()
    return r is not None

def save_message(username, role, content):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
              (username, role, content, ts))
    conn.commit()
    conn.close()

def load_history(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM messages WHERE username=? ORDER BY id", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_message_by_id(msg_id, username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id=? AND username=?", (msg_id, username))
    conn.commit()
    conn.close()

def clear_all_history(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE username=?", (username,))
    conn.commit()
    conn.close()

def generate_pdf_bytes(history, username):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"AI TutorMate - {username}'s Conversation")
    c.setFont("Helvetica", 11)
    y = height - 80
    for _id, role, content, timestamp in history:
        lines = (f"[{timestamp}] {'You' if role=='user' else 'TutorMate'}: " + content).split("\n")
        for line in lines:
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 50
            c.drawString(50, y, line)
            y -= 14
        y -= 6
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def html_escape(s: str):
    if s is None:
        return ""
    return (s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>"))

# initialize db
init_db()

# -----------------------------
# UI: Login / Register (sidebar)
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.sidebar.title("🔑 Account")

if not st.session_state.logged_in:
    choice = st.sidebar.radio("Action", ["Login", "Register"])
    if choice == "Login":
        in_user = st.sidebar.text_input("Username", key="login_user")
        in_pass = st.sidebar.text_input("Password", type="password", key="login_pass")
        if st.sidebar.button("Login"):
            if authenticate_user(in_user.strip(), in_pass):
                st.session_state.logged_in = True
                st.session_state.username = in_user.strip()
                st.sidebar.success(f"Logged in as {st.session_state.username}")
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid username or password")
    else:  # Register
        reg_user = st.sidebar.text_input("New username", key="reg_user")
        reg_pass = st.sidebar.text_input("New password", type="password", key="reg_pass")
        if st.sidebar.button("Register"):
            ok = register_user(reg_user.strip(), reg_pass)
            if ok:
                st.sidebar.success("Registered! Please switch to Login.")
            else:
                st.sidebar.error("Username already exists")
else:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    # Clear all
    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 Clear All History"):
        clear_all_history(st.session_state.username)
        st.sidebar.success("All history cleared")
        st.experimental_rerun()

    # Download TXT
    history_for_export = load_history(st.session_state.username)
    if history_for_export:
        chat_text = "\n".join([f"[{t}] {'You' if r=='user' else 'TutorMate'}: {c}" for (_id, r, c, t) in history_for_export])
        st.sidebar.download_button("⬇️ Download TXT", chat_text, file_name=f"{st.session_state.username}_history.txt", mime="text/plain")

        # PDF if available
        if REPORTLAB_AVAILABLE:
            pdf_bytes = generate_pdf_bytes(history_for_export, st.session_state.username)
            if pdf_bytes:
                st.sidebar.download_button("📄 Download PDF", pdf_bytes, file_name=f"{st.session_state.username}_history.pdf", mime="application/pdf")
        else:
            st.sidebar.caption("Install reportlab for PDF export (add to requirements).")

# -----------------------------
# Main Chat UI (when logged in)
# -----------------------------
if st.session_state.logged_in:
    username = st.session_state.username
    st.title("📘 AI TutorMate - Study Helper")
    st.write(f"Hello **{username}** — ask study questions (math, science, coding, history...).")

    # Chat bubble CSS + scrollable container
    st.markdown(
        """
        <style>
        .chat-box {
            height: 60vh;
            overflow-y: auto;
            border: 1px solid #e6e6e6;
            padding: 12px;
            border-radius: 8px;
            background: #fafafa;
        }
        .bubble-user {
            background:#dcf8c6;
            padding:10px 12px;
            border-radius:12px;
            max-width:70%;
            margin-left:30%;
            margin-bottom:8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .bubble-assistant {
            background:#f1f0f0;
            padding:10px 12px;
            border-radius:12px;
            max-width:70%;
            margin-right:30%;
            margin-bottom:8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .meta {
            font-size:11px;
            color:#555;
            margin-top:6px;
            text-align:right;
        }
        .delete-link {
            font-size:12px;
            color:#c0392b;
            text-decoration:none;
            margin-left:8px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Build chat HTML with delete links (uses query param ?delete=ID)
    history = load_history(username)
    chat_html = '<div id="chat-box" class="chat-box">'
    for _id, role, content, ts in history:
        safe_content = html_escape(content)
        # include delete link that sets ?delete=<id>
        delete_link = f'<a class="delete-link" href="?delete={_id}">🗑️ Delete</a>'
        if role == "user":
            chat_html += f'<div class="bubble-user">👤 {safe_content}<div class="meta">{ts} {delete_link}</div></div>'
        else:
            chat_html += f'<div class="bubble-assistant">🤖 {safe_content}<div class="meta">{ts} {delete_link}</div></div>'
    chat_html += '</div>'

    st.markdown(chat_html, unsafe_allow_html=True)

    # Handle delete via query params (st.query_params)
    if "delete" in st.query_params:
        try:
            delete_id = int(st.query_params.get("delete", [None])[0])
            if delete_id:
                delete_message_by_id(delete_id, username)
        except Exception:
            pass
        # clear query params and reload
        st.experimental_set_query_params()
        st.experimental_rerun()

    # Auto-scroll to bottom JS (executes after chat_html)
    st.markdown(
        """
        <script>
        const el = document.getElementById("chat-box");
        if (el) { el.scrollTop = el.scrollHeight; }
        </script>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Use Streamlit's chat_input for reliable Enter=Send and Shift+Enter newline
    user_input = st.chat_input("✍️ Type your question and press Enter to send (Shift+Enter = newline)")

    if user_input is not None and user_input.strip() != "":
        # Save user's message
        save_message(username, "user", user_input.strip())

        # Build messages for Groq (system + conversation)
        system_msg = {
            "role": "system",
            "content": (
                "You are AI TutorMate, a helpful teacher. "
                "You ONLY provide responses for educational purposes, such as math, science, coding, "
                "engineering, history, or literature. If asked something unrelated to study, politely refuse."
            )
        }
        # reload history to include the just-saved user message
        history = load_history(username)
        messages_for_api = [system_msg]
        for (_id, role, content, ts) in history:
            # Groq expects 'user'/'assistant' roles — our DB already stores those
            messages_for_api.append({"role": role, "content": content})

        # call Groq if key available
        if api_key:
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages_for_api,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
            except Exception as e:
