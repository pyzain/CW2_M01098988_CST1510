# app/pages/5_🤖_AI_Assistant.py
"""
Full AI Assistant page.
- Shows chat history stored in st.session_state['ai_messages'] (keeps simple)
- Allows switching between short and full context modes
- Reuses services.ai_assistant.AIAssistant.ask()
"""

import streamlit as st
from app.services.ai_assistant import AIAssistant

# Setup history in session state
st.session_state.setdefault("ai_messages", [
    {"role": "system", "content": "You are a concise AI assistant for the platform."}
])

def append_message(role, content):
    st.session_state["ai_messages"].append({"role": role, "content": content})
    # keep history reasonable
    if len(st.session_state["ai_messages"]) > 80:
        st.session_state["ai_messages"] = st.session_state["ai_messages"][-80:]

st.title("🤖 AI Assistant (Full page)")
st.write("Use the assistant for longer questions and contextual prompts.")

mode = st.radio("Context mode", ["Short (quick)", "Full (dashboard context)"], index=0, horizontal=True)

user_input = st.text_area("Your question", height=180)

if st.button("Send"):
    if not user_input.strip():
        st.warning("Please enter a question.")
    else:
        append_message("user", user_input.strip())
        try:
            ai = AIAssistant(system_prompt="You are a helpful assistant for the Multi-Domain Platform.")
            answer = ai.ask(user_input.strip())
        except Exception as e:
            answer = f"[AI error: {e}]"
        append_message("assistant", answer)

# Show history
st.markdown("### Conversation")
for m in st.session_state["ai_messages"][-20:]:
    if m["role"] == "user":
        st.markdown(f"**You:** {m['content']}")
    elif m["role"] == "assistant":
        st.markdown(f"**Assistant:** {m['content']}")
    else:
        st.markdown(f"**{m['role'].capitalize()}:** {m['content']}")
