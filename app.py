import streamlit as st
import sqlite3
from groq import Groq
from dotenv import load_dotenv
import os

# --- Load API key ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# --- DB Setup ---
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# --- Session State ---
if "username" not in st.session_state:
    st.session_state.username = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Login / Register Page ---
if st.session_state.username is None:
    choice = st.radio("Choose", ["Login", "Register"])

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            if c.fetchone():
                st.session_state.username = username
                st.success("Login successful ✅")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials ❌")

    else:
        st.subheader("Register")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users(username,password) VALUES(?,?)", (new_user, new_pass))
                conn.commit()
                st.success("Registered! Please login now.")
            except:
                st.error("User already exists ❌")

# --- Chat Interface ---
else:
    st.title(f"💬 AI TutorMate - Welcome {st.session_state.username}!")

    # Load old history from DB (only once)
    if not st.session_state.messages:
        rows = c.execute("SELECT role, content FROM chat_history WHERE username=? ORDER BY id ASC",
                         (st.session_state.username,)).fetchall()
        for r in rows:
            st.session_state.messages.append({"role": r[0], "content": r[1]})

    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Save user msg in DB
        c.execute("INSERT INTO chat_history(username, role, content) VALUES(?,?,?)",
                  (st.session_state.username, "user", prompt))
        conn.commit()

        # Get response from Groq
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=st.session_state.messages
        )
        answer = response.choices[0].message.content

        # Show assistant message
        with st.chat_message("assistant"):
            st.markdown(answer)

        # Save assistant msg in memory + DB
        st.session_state.messages.append({"role": "assistant", "content": answer})
        c.execute("INSERT INTO chat_history(username, role, content) VALUES(?,?,?)",
                  (st.session_state.username, "assistant", answer))
        conn.commit()
