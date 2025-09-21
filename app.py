# app.py
import streamlit as st
from dotenv import load_dotenv
import os
from groq import Groq
import datetime
import io

# local DB helper
from chat_db import init_db, create_user, get_user_by_username, hash_password, verify_password, \
                    save_message, get_messages_for_user, delete_message_by_id, clear_history

# PDF helper (optional)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB = True
except Exception:
    REPORTLAB = False

# init DB
init_db()

# load API key
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY", None)
client = Groq(api_key=API_KEY) if API_KEY else None

st.set_page_config(page_title="AI TutorMate", layout="wide")

# Session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "name" not in st.session_state:
    st.session_state.name = None

# ---- Sidebar: Login / Register ----
st.sidebar.title("Account")

mode = st.sidebar.radio("Choose", ["Login", "Register"])

if mode == "Register":
    st.sidebar.subheader("Create account")
    reg_name = st.sidebar.text_input("Full name", key="reg_name")
    reg_user = st.sidebar.text_input("Username", key="reg_user")
    reg_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
    reg_pass2 = st.sidebar.text_input("Confirm password", type="password", key="reg_pass2")
    if st.sidebar.button("Register"):
        if not reg_user.strip():
            st.sidebar.error("Choose a username")
        elif reg_pass != reg_pass2:
            st.sidebar.error("Passwords do not match")
        else:
            hashed = hash_password(reg_pass)
            ok = create_user(reg_user.strip(), hashed, reg_name.strip())
            if ok:
                st.sidebar.success("Account created — now switch to Login")
            else:
                st.sidebar.error("Username already exists")

elif mode == "Login":
    st.sidebar.subheader("Login")
    in_user = st.sidebar.text_input("Username", key="login_user")
    in_pass = st.sidebar.text_input("Password", type="password", key="login_pass")
    if st.sidebar.button("Login"):
        row = get_user_by_username(in_user.strip())
        if row is None:
            st.sidebar.error("Invalid credentials")
        else:
            _id, username_db, password_hash_db, name_db = row
            if verify_password(in_pass, password_hash_db):
                st.session_state.logged_in = True
                st.session_state.username = username_db
                st.session_state.name = name_db or username_db
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials")

# If logged in -> show logout + tools
if st.session_state.logged_in:
    st.sidebar.markdown(f"**Logged in:** {st.session_state.name} (`{st.session_state.username}`)")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.experimental_rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 Clear All History"):
        clear_history(st.session_state.username)
        st.sidebar.success("History cleared")
        st.experimental_rerun()

    # Download history as TXT
    msgs_for_export = get_messages_for_user(st.session_state.username)
    if msgs_for_export:
        chat_text = "\n".join([f"[{m['timestamp']}] {'You' if m['role']=='user' else 'TutorMate'}: {m['content']}" for m in msgs_for_export])
        st.sidebar.download_button("⬇️ Download TXT", chat_text, file_name=f"{st.session_state.username}_history.txt", mime="text/plain")
        if REPORTLAB:
            # generate PDF bytes
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height-50, f"AI TutorMate - {st.session_state.username}'s History")
            c.setFont("Helvetica", 10)
            y = height - 80
            for m in msgs_for_export:
                line = f"[{m['timestamp']}] {'You' if m['role']=='user' else 'TutorMate'}: {m['content']}"
                for sub in line.split("\n"):
                    if y < 60:
                        c.showPage()
                        c.setFont("Helvetica", 10)
                        y = height - 50
                    c.drawString(50, y, sub[:120])
                    y -= 12
                y -= 6
            c.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            st.sidebar.download_button("📄 Download PDF", pdf_bytes, file_name=f"{st.session_state.username}_history.pdf", mime="application/pdf")

# ---- Main App ----
st.title("📘 AI TutorMate")

if not st.session_state.logged_in:
    st.info("Please register or login from the sidebar to use the chat.")
    st.stop()

username = st.session_state.username

# show chat history (scrollable)
messages = get_messages_for_user(username)

# basic CSS for the chat box
st.markdown("""
    <style>
    .chat-box { height: 60vh; overflow-y: auto; border:1px solid #eee; padding:12px; border-radius:8px; background:#fafafa; }
    .bubble-user { background:#dcf8c6; padding:8px 10px; border-radius:12px; max-width:70%; margin-left:30%; margin-bottom:8px; }
    .bubble-assistant { background:#f1f0f0; padding:8px 10px; border-radius:12px; max-width:70%; margin-right:30%; margin-bottom:8px; }
    .meta { font-size:11px; color:#555; margin-top:6px; text-align:right; }
    .delete-link { font-size:12px; color:#c0392b; text-decoration:none; margin-left:8px; }
    </style>
""", unsafe_allow_html=True)

chat_html = '<div id="chat-box" class="chat-box">'
for m in messages:
    content_html = st.components.v1.html  # just to reference; not used
    safe = st.utils.unsafe_html if False else m['content']  # keep as plain text
    # We will escape minimal HTML by replacing < and >
    safe_content = m['content'].replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    delete_link = f'<a class="delete-link" href="?delete={m["id"]}">🗑️ Delete</a>'
    if m['role'] == 'user':
        chat_html += f'<div class="bubble-user">👤 {safe_content}<div class="meta">{m["timestamp"]} {delete_link}</div></div>'
    else:
        chat_html += f'<div class="bubble-assistant">🤖 {safe_content}<div class="meta">{m["timestamp"]} {delete_link}</div></div>'
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# handle delete via query param
if "delete" in st.query_params:
    try:
        delete_id = int(st.query_params.get("delete")[0])
        delete_message_by_id(delete_id, username)
    except Exception:
        pass
    st.experimental_set_query_params()
    st.experimental_rerun()

# auto-scroll to bottom (JS)
st.markdown("""
    <script>
    const el = document.getElementById("chat-box");
    if (el) { el.scrollTop = el.scrollHeight; }
    </script>
""", unsafe_allow_html=True)

# input using st.chat_input (Enter to send)
user_input = st.chat_input("✍️ Type your study question and press Enter (Shift+Enter for newline)")

if user_input is not None and user_input.strip() != "":
    # save user message
    save_message(username, "user", user_input.strip())
    # call API
    system_msg = {"role":"system",
                  "content": "You are AI TutorMate. You only provide educational answers (math, science, coding, history, literature). If user asks non-educational things, politely refuse."}
    # build messages for API from DB (including system first)
    db_msgs = get_messages_for_user(username)
    messages_for_api = [system_msg] + [{"role": m["role"], "content": m["content"]} for m in db_msgs]
    # call Groq
    if client:
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages_for_api,
                temperature=0.7
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ API Error: {e}"
    else:
        answer = "⚠️ No GROQ_API_KEY configured."

    # save assistant reply
    save_message(username, "assistant", answer)
    # rerun to refresh display (so chat shows new messages)
    st.rerun()
