# models/user.py
"""User entity for Multi-Domain Intelligence Platform."""

from typing import Protocol


class PasswordHasherProtocol(Protocol):
    """Protocol for a hasher object expected by User.verify_password."""
    def check_password(self, plain: str, hashed: str) -> bool:
        ...


class User:
    """Represents a user in the platform (simple OOP wrapper)."""

    def __init__(self, username: str, password_hash: str, role: str = "user", id: int = None):
        # store database ID if provided
        self.id = id
        self.__username = username
        self.__password_hash = password_hash
        self.__role = role

    def get_username(self) -> str:
        return self.__username

    def get_role(self) -> str:
        return self.__role

    def verify_password(self, plain_password: str, hasher):
        return hasher.check_password(plain_password, self.__password_hash)

    def __str__(self) -> str:
        return f"User({self.__username}, role={self.__role}, id={self.id})"

