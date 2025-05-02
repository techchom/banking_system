import sqlite3
from tabulate import tabulate

DB_PATH = "data/master_accounts.db"

def view_accounts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
    SELECT account_number, holder_name, status, balance, plan, transaction_count
    FROM accounts
    ORDER BY account_number;
    """)

    rows = c.fetchall()
    conn.close()

    if not rows:
        print("ℹ️ No accounts found in the database.")
        return

    headers = ["Account #", "Holder Name", "Status", "Balance", "Plan", "Tx Count"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    view_accounts()
