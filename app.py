import streamlit as st
import sqlite3
import hashlib
import os
from groq import Groq
from dotenv import load_dotenv

# -----------------------------
# Load API key
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ API key not found. Please set GROQ_API_KEY in .env file.")
client = Groq(api_key=api_key)

# -----------------------------
# Database functions
# -----------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            username TEXT,
            role TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    data = c.fetchone()
    conn.close()
    return data

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_message(username, role, message):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO chats (username, role, message) VALUES (?, ?, ?)", (username, role, message))
    conn.commit()
    conn.close()

def load_chat_history(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role, message FROM chats WHERE username=?", (username,))
    history = c.fetchall()
    conn.close()
    return history

# -----------------------------
# Main App
# -----------------------------
def main():
    st.set_page_config(page_title="AI TutorMate", page_icon="🤖", layout="centered")
    st.title("🤖 AI TutorMate")

    init_db()

    # Session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    menu = ["Login", "Register"]
    choice = st.sidebar.radio("Account", menu)

    if not st.session_state.logged_in:
        if choice == "Login":
            st.subheader("Login Section")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                hashed_pwd = hash_password(password)
                result = login_user(username, hashed_pwd)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome {username} 🎉")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        elif choice == "Register":
            st.subheader("Create New Account")

            new_user = st.text_input("Username")
            new_password = st.text_input("Password", type="password")

            if st.button("Register"):
                if new_user and new_password:
                    try:
                        add_user(new_user, hash_password(new_password))
                        st.success("Account created successfully!")
                        st.info("Go to Login Menu to login")
                    except:
                        st.error("User already exists!")
                else:
                    st.warning("Please fill all fields")

    else:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        # -----------------------------
        # Chat Section
        # -----------------------------
        st.subheader("💬 AI Tutor Chat")

        # Load previous chat history
        history = load_chat_history(st.session_state.username)

        for role, msg in history:
            if role == "user":
                with st.chat_message("user"):
                    st.markdown(msg)
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg)

        # Chat input
        user_input = st.chat_input("Ask me anything about your studies:")

        if user_input:
            # Save user message
            save_message(st.session_state.username, "user", user_input)
            with st.chat_message("user"):
                st.markdown(user_input)

            # AI Response
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": user_input}],
                )
                ai_response = response.choices[0].message.content
            except Exception as e:
                ai_response = f"⚠️ Error: {e}"

            # Save AI reply
            save_message(st.session_state.username, "assistant", ai_response)
            with st.chat_message("assistant"):
                st.markdown(ai_response)


if __name__ == '__main__':
    main()
