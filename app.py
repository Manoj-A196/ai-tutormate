import streamlit as st
from g4f.client import Client
from g4f.Provider import Grok  # Force Grok provider

# Initialize client
client = Client()

st.set_page_config(page_title="AI Tutor (Education Only)", page_icon="📘")
st.title("📘 AI Tutor Mate - Study Helper")

# Store conversation
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": (
                "You are AI Tutor Mate. "
                "You only provide answers for educational purposes: "
                "subjects like mathematics, science, coding, engineering, history, and literature. "
                "If a user asks something unrelated to study or learning, politely refuse and remind them "
                "that you are only for education."
            )
        }
    ]

# User input
user_input = st.text_area("✍️ Ask your study question:")

if st.button("Generate Response"):
    if user_input:
        with st.spinner("Thinking like a tutor..."):
            st.session_state["messages"].append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state["messages"],
                provider=Grok
            )

            reply = response.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": reply})

            st.success("✅ Tutor answered!")
            st.write(reply)
    else:
        st.warning("Please enter a study-related question!")

# Show history
st.subheader("📝 Conversation History")
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**👤 You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 Tutor:** {msg['content']}")
