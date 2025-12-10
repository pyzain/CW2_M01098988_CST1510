# app/models/user.py
"""Simple User model used by the app."""

class User:
    def __init__(self, user_id: int, username: str, role: str = "user"):
        self.id = user_id
        self.__username = username
        self.__role = role

    def get_username(self) -> str:
        return self.__username

    def get_role(self) -> str:
        return self.__role

    def __repr__(self):
        return f"User({self.__username}, role={self.__role})"
