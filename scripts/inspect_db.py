import sqlite3

conn = sqlite3.connect('data/influencers.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables in SQLite:", [r[0] for r in cursor.fetchall()])
try:
    cursor.execute("SELECT id, username, email, provider, role, created_at FROM users;")
    rows = cursor.fetchall()
    print(f"Users in SQLite ({len(rows)}):", rows)
except Exception as e:
    print("Users table error:", e)
conn.close()
