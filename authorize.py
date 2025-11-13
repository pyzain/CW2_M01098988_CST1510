import bcrypt
import os

def hash_password(plain_text_password):
    """Hash a plaintext password using bcrypt."""
    if not plain_text_password:
        raise ValueError("Password cannot be empty.")
    password_bytes = plain_text_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')  # store as string

def verify_password(plain_text_password, hashed_password):
    """Verify if the entered password matches the stored hash."""
    password_bytes = plain_text_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def register_user(username, password):
    """Register a new user and store username + hashed password in users.txt."""
    if not username or not password:
        print("⚠️ Username and password cannot be empty.")
        return

    # Prevent duplicate usernames
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            for line in f:
                user, _ = line.strip().split(',', 1)
                if user == username:
                    print("⚠️ Username already exists. Please choose another one.")
                    return

    hashed_password = hash_password(password)

    # Append new user to file
    with open("users.txt", "a") as f:
        f.write(f"{username},{hashed_password}\n")

    print(f"✅ User '{username}' registered successfully.")

def login_user(username, password):
    """Log in an existing user by verifying credentials."""
    if not os.path.exists("users.txt"):
        print("❌ No users registered yet.")
        return False

    with open("users.txt", "r") as f:
        for line in f:
            user, hashed = line.strip().split(',', 1)
            if user == username:
                if verify_password(password, hashed):
                    print("✅ Login successful!")
                    return True
                else:
                    print("❌ Incorrect password.")
                    return False

    print("❌ Username not found.")
    return False

# -------------------------------
# Interactive Menu
# -------------------------------
if __name__ == "__main__":
    print("=== Simple User System ===")
    choice = input("Do you want to (r)egister or (l)ogin? ").strip().lower()

    if choice == "r":
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        register_user(username, password)
    elif choice == "l":
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        login_user(username, password)
    else:
        print("⚠️ Invalid choice. Please run again and choose 'r' or 'l'.")