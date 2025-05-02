# Updated banking frontend with DB-backed transaction history
import sqlite3
import os
import readline
import getpass
import csv
from datetime import datetime

DB_PATH = "data/master_accounts.db"

MAX_WITHDRAW_STANDARD = 500
MAX_TRANSFER_STANDARD = 1000
MAX_PAYBILL_STANDARD = 2000
DAILY_WITHDRAW_LIMIT = 1000
DEPOSIT_LIMIT = 9999
ALLOWED_BILL_COMPANIES = {"EC", "CQ", "FI"}

COMMANDS = [
    'history', 'changepin',
    'balance', 'login', 'logout', 'deposit', 'withdrawal', 'transfer',
    'paybill', 'create', 'delete', 'disable', 'changeplan', 'exit'
]

def completer(text, state):
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return options[state] if state < len(options) else None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

session = {
    "logged_in": False,
    "user_type": None,
    "user_name": None,
    "account_number": None
}

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updates = [
        ("Redon Hasani", "1111", "John_Doe"),
        ("Taulant Miftari", "2222", "Jane_Smith"),
        ("Teuta Berisha", "3333", "Alice_Wonder"),
    ]
    for new_name, new_pass, old_name in updates:
        c.execute("UPDATE accounts SET holder_name=?, password=? WHERE holder_name=?", (new_name, new_pass, old_name))
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

def log_transaction(account_number, t_type, amount, misc=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (account_number, type, amount, misc, timestamp) VALUES (?, ?, ?, ?, ?)",
              (account_number, t_type, amount, misc, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def view_account_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT account_number, holder_name FROM accounts ORDER BY holder_name")
    accounts = c.fetchall()
    if not accounts:
        print("❌ No accounts found."); conn.close(); return
    print("\n🔍 Select an account to view history:")
    for idx, (acc, name) in enumerate(accounts, 1):
        print(f"{idx}. {name} ({acc})")
    try:
        choice = int(input("Choose number: "))
        if choice < 1 or choice > len(accounts):
            print("❌ Invalid choice."); return
    except:
        print("❌ Invalid input."); return
    selected_acc, selected_name = accounts[choice - 1]
    c.execute("SELECT type, amount, misc, timestamp FROM transactions WHERE account_number=? ORDER BY timestamp DESC", (selected_acc,))
    rows = c.fetchall()
    conn.close()
    print(f"\n📜 Transaction history for {selected_name} ({selected_acc}):")
    for t_type, amount, misc, timestamp in rows:
        print(f"[{timestamp}] {t_type.capitalize():<12} | Amount: ${amount:.2f} | Info: {misc}")

def get_balance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM accounts WHERE account_number=?", (session["account_number"],))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def changepin():
    new_pin = getpass.getpass("Enter new 4-digit PIN: ").strip()
    if not new_pin.isdigit() or len(new_pin) != 4:
        print("❌ Invalid PIN format.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE accounts SET password=? WHERE account_number=?", (new_pin, session["account_number"]))
    conn.commit(); conn.close()
    print("✅ PIN updated successfully.")

def history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT type, amount, misc, timestamp FROM transactions WHERE account_number=? ORDER BY timestamp DESC", (session["account_number"],))
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("(No transactions found.)")
        return
    for t_type, amount, misc, timestamp in rows:
        print(f"[{timestamp}] {t_type.capitalize():<12} | Amount: ${amount:.2f} | Info: {misc}")

def balance():
    amount = get_balance()
    if amount is not None:
        print(f"💰 Balance: ${amount:.2f}")
    else:
        print("❌ Account not found.")

def deposit():
    try:
        amount = float(input("Enter amount to deposit: "))
        if amount <= 0 or amount > DEPOSIT_LIMIT:
            print("❌ Invalid amount."); return
    except:
        print("❌ Invalid input."); return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", (amount, session["account_number"]))
    conn.commit(); conn.close()
    log_transaction(session["account_number"], "deposit", amount, f"by {session['user_name']}")
    print("✅ Deposit complete.")

def withdrawal():
    try:
        amount = float(input("Enter amount to withdraw: "))
        if amount <= 0:
            print("❌ Invalid amount."); return
    except:
        print("❌ Invalid input."); return
    balance = get_balance()
    if balance is None or balance < amount:
        print("❌ Insufficient funds."); return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, session["account_number"]))
    conn.commit(); conn.close()
    log_transaction(session["account_number"], "withdrawal", amount, f"by {session['user_name']}")
    print("✅ Withdrawal complete.")

def transfer():
    to_acc = input("Enter target account number: ").strip()
    try:
        amount = float(input("Enter amount to transfer: "))
        if amount <= 0:
            print("❌ Invalid amount."); return
    except:
        print("❌ Invalid input."); return
    if session["user_type"] == "standard" and amount > MAX_TRANSFER_STANDARD:
        print(f"❌ Standard users can only transfer up to ${MAX_TRANSFER_STANDARD}."); return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM accounts WHERE account_number=?", (session["account_number"],))
    from_bal = c.fetchone()
    c.execute("SELECT holder_name FROM accounts WHERE account_number=?", (to_acc,))
    to_info = c.fetchone()
    if not from_bal or not to_info:
        print("❌ Invalid accounts."); conn.close(); return
    if from_bal[0] < amount:
        print("❌ Insufficient funds."); conn.close(); return
    c.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, session["account_number"]))
    c.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", (amount, to_acc))
    conn.commit(); conn.close()
    log_transaction(session["account_number"], "transfer", amount, f"to {to_acc} ({to_info[0]})")
    log_transaction(to_acc, "received", amount, f"from {session['user_name']} ({session['account_number']})")
    print(f"✅ Transferred ${amount:.2f} to account {to_acc}.")

def paybill():
    company = input("Enter bill company (EC, CQ, FI): ").strip().upper()
    if company not in ALLOWED_BILL_COMPANIES:
        print("❌ Invalid bill company."); return
    try:
        amount = float(input("Enter bill amount: "))
        if amount <= 0:
            print("❌ Invalid amount."); return
    except:
        print("❌ Invalid input."); return
    if session["user_type"] == "standard" and amount > MAX_PAYBILL_STANDARD:
        print(f"❌ Standard users can only pay bills up to ${MAX_PAYBILL_STANDARD}."); return
    balance = get_balance()
    if balance is None or balance < amount:
        print("❌ Insufficient funds."); return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, session["account_number"]))
    conn.commit(); conn.close()
    log_transaction(session["account_number"], "paybill", amount, f"to {company}")
    print(f"✅ Paid ${amount:.2f} to {company}.")

def show_commands():
    print("\n💡 Available commands:")
    if session["user_type"] == "admin":
        print("  - listaccounts, view, create, delete, disable, changeplan, resetpin")
    print("  - deposit, withdrawal, transfer, paybill")
    print("  - balance, changepin, history, exportcsv, logout, exit")

def list_accounts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT account_number, holder_name, balance FROM accounts ORDER BY holder_name")
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("❌ No accounts found.")
        return
    print("\n📄 Llogaritë ekzistuese:")
    for idx, (acc_num, name, balance) in enumerate(rows, 1):
        print(f"{idx}. {name} ({acc_num}) - ${balance:.2f}")

def command_loop():
    while session["logged_in"]:
        cmd = input("\nCommand: ").strip().lower()
        if cmd == "logout":
            session.update({"logged_in": False, "user_type": None, "user_name": None, "account_number": None})
            print("👋 Logged out.")
            break
        elif cmd == "listaccounts": list_accounts()
        elif cmd == "view": view_account_history()
        elif cmd == "changepin": changepin()
        elif cmd == "history": history()
        elif cmd == "balance": balance()
        elif cmd == "deposit": deposit()
        elif cmd == "withdrawal": withdrawal()
        elif cmd == "transfer": transfer()
        elif cmd == "paybill": paybill()
        else:
            print("❌ Unknown command. Type carefully!")

def login():
    if session["logged_in"]:
        print("❌ Already logged in.")
        return
    name = input("Enter account holder's name: ").strip()
    pin = getpass.getpass("Enter 4-digit PIN: ").strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT account_number FROM accounts WHERE holder_name=? AND password=?", (name, pin))
    result = c.fetchone()
    conn.close()
    if not result:
        print("❌ Invalid credentials.")
        return
    session.update({
        "logged_in": True,
        "user_type": "admin" if name.lower() == "admin_user" else "standard",
        "user_name": name,
        "account_number": result[0]
    })
    print(f"✅ Logged in as {name} ({session['user_type'].upper()})")
    print(f"👋 Mirësevini, {name}! Jeni kyçur me sukses në Banking System F.")
    show_commands()
    command_loop()

def main():
    setup_database()
    print("✨ Mirësevini në Banking System F ✨")
    print("Please enter a command:")
    while True:
        cmd = input("\nCommand: ").strip().lower()
        if cmd == "login": login()
        elif cmd == "exit": print("👋 Goodbye!"); break
        else: print("❌ Unknown command. Please log in first or type 'exit'.")

if __name__ == "__main__":
    main()
