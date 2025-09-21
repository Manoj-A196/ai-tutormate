import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

# Load API key (first try Streamlit secrets, then .env for local use)
load_dotenv()
api_key = (
    st.secrets.get("GROQ_API_KEY", None)
    or os.getenv("GROQ_API_KEY")
)

if not api_key:
    st.error("❌ No API key found. Please set GROQ_API_KEY in Streamlit secrets or .env file.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

st.set_page_config(page_title="AI TutorMate", page_icon="📘")
st.title("📘 AI TutorMate - Study Helper")

# Store conversation
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": (
                "You are AI TutorMate, a helpful teacher. "
                "You ONLY provide responses for educational purposes, such as math, science, coding, "
                "engineering, history, or literature. "
                "If a user asks something unrelated to study or education, you must politely refuse "
                "and remind them that you only help with learning."
            )
        }
    ]

# --- Show chat history first ---
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# --- Handle new input ---
user_input = st.chat_input("✍️ Ask your study question:")

if user_input:
    # Show user bubble immediately
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state["messages"].append({"role": "user", "content": user_input})

    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # free Groq model
            messages=st.session_state["messages"],
            temperature=0.7
        )

        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"⚠️ API Error: {e}"

    # Show assistant bubble immediately
    with st.chat_message("assistant"):
        st.write(answer)

    # Save to history
    st.session_state["messages"].append({"role": "assistant", "content": answer})
