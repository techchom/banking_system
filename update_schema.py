import sqlite3

conn = sqlite3.connect("data/master_accounts.db")
c = conn.cursor()

# Add 'password' column if it doesn't exist
try:
    c.execute("ALTER TABLE accounts ADD COLUMN password TEXT DEFAULT '1234'")
    print("✅ Password column added.")
except sqlite3.OperationalError:
    print("ℹ️ Password column already exists.")

# Optional: Set password for admin
c.execute("UPDATE accounts SET password='adminpass' WHERE holder_name='Admin_User'")
conn.commit()
conn.close()
