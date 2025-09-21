import streamlit as st
import sqlite3
import hashlib

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


# -----------------------------
# Main App
# -----------------------------
def main():
    st.set_page_config(page_title="AI TutorMate", page_icon="🤖", layout="centered")
    st.title("🤖 AI TutorMate")

    init_db()

    # Session state to keep track of login
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

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Chat input (works like real chat)
        user_input = st.chat_input("Ask me anything about your studies:")

        if user_input:
            st.session_state.chat_history.append(("You", user_input))
            # Dummy AI response (replace later with Groq/OpenAI)
            ai_response = f"📘 I think '{user_input}' is a great question. Here's a simplified explanation..."
            st.session_state.chat_history.append(("AI", ai_response))

        # Display chat history
        for sender, msg in st.session_state.chat_history:
            if sender == "You":
                with st.chat_message("user"):
                    st.markdown(msg)
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg)


if __name__ == '__main__':
    main()
