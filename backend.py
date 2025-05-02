import sqlite3
import os

DB_PATH = "data/master_accounts.db"
MERGED_TRANSACTIONS_FILE = "data/merged_transactions.txt"

TRANSACTION_CODES = {
    "01": "withdrawal",
    "02": "transfer",
    "03": "paybill",
    "04": "deposit",
    "05": "create",
    "06": "delete",
    "07": "disable",
    "08": "changeplan",
    "00": "end_of_session"
}

FEE_PLAN = {
    "SP": 0.05,
    "NP": 0.10
}

def process_transaction_line(line, conn):
    code = line[0:2]
    name = line[3:23].strip()
    acc_no = line[24:29].strip()
    amount_str = line[30:38].strip()
    misc = line[39:41].strip()

    c = conn.cursor()

    # Handle end of session
    if code == "00":
        return

    # Convert amount
    try:
        amount = float(amount_str)
    except:
        print(f"❌ ERROR: Invalid amount in line: {line}")
        return

    # Fetch account
    c.execute("SELECT * FROM accounts WHERE account_number=?", (acc_no,))
    account = c.fetchone()

    if code == "04":  # deposit
        if not account:
            print(f"❌ ERROR: Deposit failed - account {acc_no} not found.")
            return
        new_balance = account[3] + amount
        fee = FEE_PLAN[account[4]]
        new_balance -= fee
        if new_balance < 0:
            print(f"❌ ERROR: Negative balance after fee on deposit to {acc_no}")
            return
        c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance, acc_no))

    elif code == "01":  # withdrawal
        if not account:
            print(f"❌ ERROR: Withdrawal failed - account {acc_no} not found.")
            return
        fee = FEE_PLAN[account[4]]
        new_balance = account[3] - amount - fee
        if new_balance < 0:
            print(f"❌ ERROR: Withdrawal causes negative balance on {acc_no}")
            return
        c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance, acc_no))

    elif code == "05":  # create
        if account:
            print(f"❌ ERROR: Account {acc_no} already exists.")
            return
        plan = "SP" if misc == "SP" else "NP"
        c.execute("INSERT INTO accounts (account_number, holder_name, status, balance, plan) VALUES (?, ?, 'A', ?, ?)", (acc_no, name, amount, plan))

    elif code == "06":  # delete
        if not account:
            print(f"❌ ERROR: Account {acc_no} not found for deletion.")
            return
        c.execute("DELETE FROM accounts WHERE account_number=?", (acc_no,))

    elif code == "07":  # disable
        if not account:
            print(f"❌ ERROR: Account {acc_no} not found to disable.")
            return
        c.execute("UPDATE accounts SET status='D' WHERE account_number=?", (acc_no,))

    elif code == "08":  # changeplan
        if not account:
            print(f"❌ ERROR: Account {acc_no} not found for plan change.")
            return
        new_plan = "NP" if account[4] == "SP" else "SP"
        c.execute("UPDATE accounts SET plan=? WHERE account_number=?", (new_plan, acc_no))

    elif code == "03":  # paybill
        if not account:
            print(f"❌ ERROR: Paybill failed - account {acc_no} not found.")
            return
        fee = FEE_PLAN[account[4]]
        new_balance = account[3] - amount - fee
        if new_balance < 0:
            print(f"❌ ERROR: Paybill causes negative balance on {acc_no}")
            return
        c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance, acc_no))

    elif code == "02":  # transfer
        # misc is second account number
        acc_to = misc
        c.execute("SELECT * FROM accounts WHERE account_number=?", (acc_to,))
        acc2 = c.fetchone()

        if not account or not acc2:
            print(f"❌ ERROR: Transfer failed - invalid account(s): {acc_no} or {acc_to}")
            return
        fee = FEE_PLAN[account[4]]
        new_balance1 = account[3] - amount - fee
        new_balance2 = acc2[3] + amount
        if new_balance1 < 0 or new_balance2 < 0:
            print(f"❌ ERROR: Transfer causes negative balance on {acc_no} or {acc_to}")
            return
        c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance1, acc_no))
        c.execute("UPDATE accounts SET balance=?, transaction_count = transaction_count + 1 WHERE account_number=?", (new_balance2, acc_to))

    else:
        print(f"❌ ERROR: Unknown transaction code: {code}")

def run_backend():
    if not os.path.exists(MERGED_TRANSACTIONS_FILE):
        print("❌ ERROR: Merged transaction file not found.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        with open(MERGED_TRANSACTIONS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                process_transaction_line(line, conn)

        conn.commit()
        print("✅ Transactions processed. Master account DB updated.")

if __name__ == "__main__":
    run_backend()
