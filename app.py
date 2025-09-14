import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or "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"

# Initialize Groq client
client = Groq(api_key=api_key)

st.title("AI TutorMate")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

user_input = st.text_input("Ask a question:")

if st.button("Send"):
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # free Groq model
            messages=st.session_state["messages"],
        )

        answer = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.write(answer)