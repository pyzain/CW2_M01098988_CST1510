# ai_core.py
"""
Simple AI Wrapper using OpenAI.
Optimized for budget using 'gpt-4o-mini'.

This handles the connection to the AI so your dashboards don't have to.
"""

import os
import streamlit as st
from openai import OpenAI


class AIAssistant:
    # We default to "gpt-4o-mini" because it is much cheaper and smarter than 3.5
    def __init__(self, role_prompt="You are a helpful AI assistant.", model="gpt-4o-mini"):
        self.role_prompt = role_prompt
        self.model = model
        self.client = None

        # 1. Try to get Key from Streamlit Secrets (secrets.toml)
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            # If not in secrets, try the environment variables (backup)
            api_key = os.getenv("OPENAI_API_KEY")

        # 2. Setup the connection
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # We don't crash here, we just print a warning to the terminal
            print("Warning: OPENAI_API_KEY not found in secrets.toml or environment.")

    def ask(self, query, data_context="", max_new_tokens=500, temperature=0.5):
        """
        Send a message to the AI and get a text response.
        """
        # Safety Check
        if not self.client:
            return "⚠️ [Error] No API Key found. Check .streamlit/secrets.toml"

        # 3. Prepare the instruction
        # We combine the system role, the data, and the user's question
        messages = [
            {"role": "system", "content": self.role_prompt},
            {"role": "user", "content": f"Context Data:\n{data_context}\n\nQuestion:\n{query}"}
        ]

        try:
            # 4. Send to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_new_tokens
            )

            # 5. Get the answer
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"⚠️ [AI Error] {str(e)}"