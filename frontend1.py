import sqlite3
from datetime import datetime
import os

DB_PATH = "data/master_accounts.db"
TRANSACTION_LOG_PATH = "data/transactions.txt"

MAX_WITHDRAW_STANDARD = 500
MAX_TRANSFER_STANDARD = 1000
MAX_PAYBILL_STANDARD = 2000

session = {
    "logged_in": False,
    "user_type": None,  # 'admin' or 'standard'
    "user_name": None,
    "session_transactions": []
}

def pad_left(val, width, pad_char='0'):
    return str(val).rjust(width, pad_char)

def pad_right(val, width, pad_char=' '):
    return str(val).ljust(width, pad_char)

def format_transaction(code, name, acc_no, amount, misc=""):
    name = pad_right(name, 20)
    acc_no = pad_left(acc_no, 5)
    amount = f"{amount:08.2f}"
    misc = pad_right(misc, 2)
    return f"{code}_{name}_{acc_no}_{amount}_{misc}"

def log_transaction(line):
    session["session_transactions"].append(line)

def login():
    if session["logged_in"]:
        print("❌ Already logged in.")
        return

    user_type = input("Login type (admin/standard): ").strip().lower()
    if user_type not in ("admin", "standard"):
        print("❌ Invalid login type.")
        return

    user_name = ""
    if user_type == "standard":
        user_name = input("Enter account holder's name: ").strip()

    session["logged_in"] = True
    session["user_type"] = user_type
    session["user_name"] = user_name
    print(f"✅ Logged in as {user_type.upper()}")

def logout():
    if not session["logged_in"]:
        print("❌ Not logged in.")
        return

    with open(TRANSACTION_LOG_PATH, "w") as f:
        for line in session["session_transactions"]:
            f.write(line + "\n")
        f.write("00_END_OF_SESSION_____00000_00000000__\n")

    print("📁 Session transaction file written to:", TRANSACTION_LOG_PATH)
    session.update({
        "logged_in": False,
        "user_type": None,
        "user_name": None,
        "session_transactions": []
    })
    print("👋 Logged out successfully.")

def deposit():
    if not session["logged_in"]:
        print("❌ Please login first.")
        return

    acc_name = session["user_name"]
    if session["user_type"] == "admin":
        acc_name = input("Enter account holder's name: ").strip()

    acc_no = input("Enter account number: ").strip()
    try:
        amount = float(input("Enter amount to deposit: "))
    except:
        print("❌ Invalid amount.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE account_number=? AND holder_name=?", (acc_no, acc_name))
    account = c.fetchone()

    if not account:
        print("❌ Account not found.")
        conn.close()
        return

    new_balance = account[3] + amount
    c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance, acc_no))
    conn.commit()
    conn.close()

    tx_line = format_transaction("04", acc_name, acc_no, amount)
    log_transaction(tx_line)
    print(f"💰 Deposited ${amount:.2f} to {acc_no}")

def withdrawal():
    if not session["logged_in"]:
        print("❌ Please login first.")
        return

    acc_name = session["user_name"]
    if session["user_type"] == "admin":
        acc_name = input("Enter account holder's name: ").strip()

    acc_no = input("Enter account number: ").strip()
    try:
        amount = float(input("Enter amount to withdraw: "))
    except:
        print("❌ Invalid amount.")
        return

    if session["user_type"] == "standard" and amount > MAX_WITHDRAW_STANDARD:
        print(f"❌ Standard users can only withdraw up to ${MAX_WITHDRAW_STANDARD}.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE account_number=? AND holder_name=?", (acc_no, acc_name))
    account = c.fetchone()

    if not account:
        print("❌ Account not found.")
        conn.close()
        return

    if account[3] - amount < 0:
        print("❌ Insufficient funds.")
        conn.close()
        return

    new_balance = account[3] - amount
    c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance, acc_no))
    conn.commit()
    conn.close()

    tx_line = format_transaction("01", acc_name, acc_no, amount)
    log_transaction(tx_line)
    print(f"🏧 Withdrew ${amount:.2f} from {acc_no}")

def main():
    print("🏦 Welcome to the Banking System")
    while True:
        cmd = input("\nEnter command (login, deposit, withdrawal, logout, exit): ").strip().lower()

        if cmd == "login":
            login()
        elif cmd == "logout":
            logout()
        elif cmd == "deposit":
            deposit()
        elif cmd == "withdrawal":
            withdrawal()
        elif cmd == "exit":
            if session["logged_in"]:
                logout()
            print("🛑 Exiting...")
            break
        else:
            print("❌ Unknown command.")

if __name__ == "__main__":
    main()
