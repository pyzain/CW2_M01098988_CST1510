# services/ai_assistant.py
import requests
import streamlit as st

class AIAssistant:
    def __init__(self, system_prompt: str = "You are an AI assistant."):
        self.api_key = st.secrets["OPENROUTER_API_KEY"]
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.system_prompt = system_prompt

    def ask(self, user_message: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post(self.base_url, json=payload, headers=headers)

        if response.status_code != 200:
            return f"API Error: {response.text}"

        try:
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "Unexpected API response."
