import os
import pandas as pd
import numpy as np
import sqlite3
import base64
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 🔒 AES Encryption Key (Keep Secret)
AES_KEY = b'Sixteen byte key'  # Must be 16, 24, or 32 bytes long

# 🔹 Encrypt Data
def encrypt_data(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode()

# 🔹 Decrypt Data
def decrypt_data(enc_data):
    enc_bytes = base64.b64decode(enc_data)
    iv = enc_bytes[:AES.block_size]
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc_bytes[AES.block_size:]), AES.block_size).decode()

# 🔹 CSV File Setup
csv_file = "lottery_data.csv"

# Ensure the correct structure with encrypted_lottery column
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["user_id", "drawdate", "user_number", "match_status", "encrypted_lottery"])
    df.to_csv(csv_file, index=False)
else:
    df = pd.read_csv(csv_file)

# 🔹 Fix Missing Column Issue
if "encrypted_lottery" not in df.columns:
    df["encrypted_lottery"] = None  # Add missing column
    df.to_csv(csv_file, index=False)

# 🔹 Generate New Lottery Numbers for Today
today_date = datetime.now().strftime("%Y-%m-%d")
if today_date not in df["drawdate"].values:
    new_lottery_numbers = np.random.randint(1, 51, 5).tolist()
    encrypted_lottery = encrypt_data(",".join(map(str, new_lottery_numbers)))
    
    new_entry = {
        "user_id": None,
        "drawdate": today_date,
        "user_number": None,
        "match_status": None,
        "encrypted_lottery": encrypted_lottery
    }
    df = df.append(new_entry, ignore_index=True)
    df.to_csv(csv_file, index=False)

# 🔹 Train Prediction Model
df["drawdate"] = pd.to_datetime(df["drawdate"], errors="coerce")
df = df.dropna(subset=["drawdate"])  # Remove invalid dates
df["drawdate_ordinal"] = df["drawdate"].apply(lambda x: x.toordinal())

X = df[["drawdate_ordinal"]]
y = df[["encrypted_lottery"]]  # Keeping encrypted values

rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, y)

# 🔹 Database Setup
conn = sqlite3.connect("lottery_results.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS lottery_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT,
                    draw_date TEXT,
                    user_lottery_number INTEGER,
                    prediction_result TEXT)''')
conn.commit()

# 🔹 User Interaction
user_name = input("\nEnter your name: ")
user_lottery_number = int(input("Enter a number between 1-50 as your lottery pick: "))

# 🔹 Get Today's Encrypted Lottery Numbers & Decrypt
today_lottery_row = df[df["drawdate"] == today_date].iloc[-1]
encrypted_lottery = today_lottery_row["encrypted_lottery"]
actual_lottery_numbers = list(map(int, decrypt_data(encrypted_lottery).split(",")))

# 🔹 Check if User Wins
is_winner = user_lottery_number in actual_lottery_numbers
result_message = "Winner!" if is_winner else "Try Again!"

# 🔹 Encrypt User's Lottery Number before storing
encrypted_user_lottery = encrypt_data(str(user_lottery_number))

# 🔹 Store in Database (Encrypted)
cursor.execute("INSERT INTO lottery_entries (user_name, draw_date, user_lottery_number, prediction_result) VALUES (?, ?, ?, ?)",
               (user_name, today_date, encrypted_user_lottery, result_message))
conn.commit()


# 🔹 Display Results (WITHOUT showing decrypted numbers)
print(f"\nLottery Draw Results for {user_name}:")
print(f"Your chosen number: [Encrypted]")
print(f"Result: {result_message}")

conn.close()
