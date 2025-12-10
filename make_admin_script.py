import sqlite3
from pathlib import Path

# Connect to the database defined in your database/db.py
# It is located at: project_root/database/platform.db
DB_PATH = Path("database/platform.db")


def set_admin(username):
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}. Run the app once first to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        print(f"❌ User '{username}' not found. Please register via the app first!")
    else:
        # Update role to admin
        cursor.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
        conn.commit()
        print(f"✅ Success! User '{username}' is now an Admin.")

    conn.close()


if __name__ == "__main__":
    target = input("Enter the username you want to make Admin: ")
    set_admin(target)