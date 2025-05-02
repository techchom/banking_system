import sqlite3
import os

# Create data folder if it doesn't exist
os.makedirs("data", exist_ok=True)

DB_PATH = "data/master_accounts.db"

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop tables if they exist (for repeatable testing)
    c.execute("DROP TABLE IF EXISTS accounts;")
    c.execute("DROP TABLE IF EXISTS transactions;")

    # Create accounts table
    c.execute("""
    CREATE TABLE accounts (
        account_number TEXT PRIMARY KEY,
        holder_name TEXT NOT NULL,
        status TEXT CHECK(status IN ('A', 'D')) NOT NULL DEFAULT 'A',
        balance REAL NOT NULL CHECK (balance >= 0),
        plan TEXT CHECK(plan IN ('SP', 'NP')) NOT NULL DEFAULT 'SP',
        transaction_count INTEGER DEFAULT 0
    );
    """)

    # Create transactions table
    c.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        holder_name TEXT,
        account_number TEXT,
        amount REAL,
        misc TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed sample data
    sample_accounts = [
        ("00001", "John_Doe", "A", 1500.00, "SP"),
        ("00002", "Jane_Smith", "A", 3000.50, "NP"),
        ("00003", "Admin_User", "A", 99999.99, "NP"),
    ]

    c.executemany("""
    INSERT INTO accounts (account_number, holder_name, status, balance, plan)
    VALUES (?, ?, ?, ?, ?);
    """, sample_accounts)

    conn.commit()
    conn.close()
    print("✅ Database setup complete. Accounts seeded.")

if __name__ == "__main__":
    setup_database()
