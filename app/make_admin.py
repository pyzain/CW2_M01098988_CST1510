from app.data.db import connect_database

conn = connect_database()
cur = conn.cursor()
cur.execute(
    "UPDATE users SET role = 'admin' WHERE username = ?",
    ("try1",)
)
conn.commit()
conn.close()

print("Done. User promoted to admin.")
