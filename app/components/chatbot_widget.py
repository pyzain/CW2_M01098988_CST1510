# app/components/chatbot_widget.py
"""
Floating chatbot widget (pure Streamlit).
- Small fixed-position button in the bottom-right.
- Clicking the button toggles a compact chat box (collapsible).
- Uses services.ai_assistant.AIAssistant.ask() to get responses.
- Designed to be simple, safe, and easy to reuse on any page.
"""

import streamlit as st
from app.services import AIAssistant

# Unique keys for st.session_state to avoid collisions across pages
_WIDGET_TOGGLE_KEY = "chat_widget_open"
_WIDGET_HISTORY_KEY = "chat_widget_history"
_WIDGET_MESSAGES_LIMIT = 30  # keep history bounded

def _ensure_state():
    """Ensure session_state keys exist."""
    st.session_state.setdefault(_WIDGET_TOGGLE_KEY, False)
    st.session_state.setdefault(_WIDGET_HISTORY_KEY, [])

def toggle_widget():
    st.session_state[_WIDGET_TOGGLE_KEY] = not st.session_state[_WIDGET_TOGGLE_KEY]

def add_message(role: str, text: str):
    """Append a message to the widget history (trim if too long)."""
    hist = st.session_state[_WIDGET_HISTORY_KEY]
    hist.append({"role": role, "text": text})
    # trim
    if len(hist) > _WIDGET_MESSAGES_LIMIT:
        st.session_state[_WIDGET_HISTORY_KEY] = hist[-_WIDGET_MESSAGES_LIMIT:]

def render(minimized_button_text: str = "💬 Help"):
    """
    Render the floating widget. Call this at the end of any dashboard page.
    """
    _ensure_state()

    # --- CSS: fixed button + box styles (simple) ---
    st.markdown(
        """
        <style>
        .chat-button {
            position: fixed;
            right: 20px;
            bottom: 20px;
            z-index: 9999;
        }
        .chat-box {
            position: fixed;
            right: 20px;
            bottom: 80px;
            width: 340px;
            max-width: 90%;
            z-index: 9999;
            background: white;
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.12);
            padding: 8px;
        }
        .chat-header {
            font-weight: 600;
            margin-bottom: 6px;
        }
        .chat-message-user {
            background:#e6f2ff;
            padding:6px;
            border-radius:6px;
            margin:6px 0;
        }
        .chat-message-assistant {
            background:#f1f1f1;
            padding:6px;
            border-radius:6px;
            margin:6px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- floating button ---
    button_col1, button_col2 = st.columns([1, 20])
    with button_col2:
        # Use HTML button to place it exactly, but Streamlit button also ok.
        # We'll render a small clickable markdown that triggers the toggle via st.button
        if st.button(minimized_button_text, key="chat_toggle_button"):
            toggle_widget()

    # --- chat box (render only if open) ---
    if st.session_state[_WIDGET_TOGGLE_KEY]:
        # container for chat box
        with st.container():
            st.markdown('<div class="chat-box">', unsafe_allow_html=True)
            st.markdown('<div class="chat-header">Assistant — Quick help</div>', unsafe_allow_html=True)

            # show history
            for msg in st.session_state[_WIDGET_HISTORY_KEY]:
                cls = "chat-message-user" if msg["role"] == "user" else "chat-message-assistant"
                st.markdown(f'<div class="{cls}">{msg["text"]}</div>', unsafe_allow_html=True)

            # input area (simple)
            user_input = st.text_input("Type a quick question...", key="chat_widget_input")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Send", key="chat_widget_send"):
                    if user_input and user_input.strip():
                        add_message("user", user_input.strip())
                        # Ask AI (safely)
                        try:
                            ai = AIAssistant(system_prompt="Act as a short assistant for the platform.")
                            answer = ai.ask(user_input.strip())
                        except Exception as e:
                            answer = f"[AI error: {e}]"
                        add_message("assistant", str(answer))
                        # clear input (workaround: set to empty string)
                        st.session_state["chat_widget_input"] = ""
            st.markdown('</div>', unsafe_allow_html=True)
