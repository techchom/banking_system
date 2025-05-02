import sqlite3

DB_PATH = "data/master_accounts.db"

# Define account holder names and their new 4-digit PINs
account_pins = {
    "Admin_User": "0000",
    "John_Doe": "1111",
    "Jane_Smith": "2222",
    "Alice_Wonder": "3333",  # example
}

def update_pins():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for name, pin in account_pins.items():
        if not pin.isdigit() or len(pin) != 4:
            print(f"❌ Invalid PIN for {name}: must be 4 digits.")
            continue

        c.execute("UPDATE accounts SET password=? WHERE holder_name=?", (pin, name))
        if c.rowcount:
            print(f"✅ Updated PIN for {name}")
        else:
            print(f"⚠️ Account not found: {name}")

    conn.commit()
    conn.close()
    print("🔐 All updates done.")

if __name__ == "__main__":
    update_pins()
