# reset_transactions_table.py

import sqlite3

DB_PATH = "data/master_accounts.db"

def reset_transactions_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Drop old table if it exists
    c.execute("DROP TABLE IF EXISTS transactions")
    
    # Create new table with the correct schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT,
            type TEXT,
            amount REAL,
            misc TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ transactions table has been reset.")

if __name__ == "__main__":
    reset_transactions_table()
