import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or "your_groq_api_key_here"

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

# Use chat input (auto-clears after sending)
user_input = st.chat_input("✍️ Ask your study question:")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Call Groq API
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # free Groq model
        messages=st.session_state["messages"],
        temperature=0.7
    )

    answer = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": answer})

    # Show reply
    st.write(f"**🤖 TutorMate:** {answer}")

# Show chat history
st.subheader("📝 Conversation History")
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**👤 You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 TutorMate:** {msg['content']}")
