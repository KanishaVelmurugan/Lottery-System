import os
import pandas as pd
import numpy as np
import sqlite3
import base64
import math
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# AES Encryption Key (Keep Secret)
AES_KEY = b'Sixteen byte key'  # Must be 16, 24, or 32 bytes long

# Encrypt Data
def encrypt_data(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode()

# Decrypt Data
def decrypt_data(encrypted_data):
    try:
        encrypted_data = base64.b64decode(encrypted_data)
        iv = encrypted_data[:AES.block_size]
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data[AES.block_size:]), AES.block_size)
        return decrypted_data.decode()
    except Exception as e:
        print("Error decrypting lottery numbers.", str(e))
        return None

# CSV File Setup
csv_file = "lottery_data.csv"
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["user_id", "drawdate", "user_number", "match_status", "encrypted_lottery"])
    df.to_csv(csv_file, index=False)
else:
    df = pd.read_csv(csv_file)

# Fix Missing Column Issue
if "encrypted_lottery" not in df.columns:
    df["encrypted_lottery"] = None
    df.to_csv(csv_file, index=False)

# Generate New Lottery Numbers for Today
today_date = datetime.now().strftime("%Y-%m-%d")

today_lottery_row = df[df["drawdate"] == today_date]

if today_lottery_row.empty or today_lottery_row.iloc[-1]["encrypted_lottery"] is None or \
   (isinstance(today_lottery_row.iloc[-1]["encrypted_lottery"], float) and math.isnan(today_lottery_row.iloc[-1]["encrypted_lottery"])):
    print("⚠️ Warning: No valid encrypted lottery found. Generating new lottery numbers.")
    new_lottery_numbers = np.random.randint(1, 51, 5).tolist()
    encrypted_lottery = encrypt_data(",".join(map(str, new_lottery_numbers)))

    new_entry = {
        "user_id": None,
        "drawdate": today_date,
        "user_number": None,
        "match_status": None,
        "encrypted_lottery": encrypted_lottery
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(csv_file, index=False)
else:
    encrypted_lottery = today_lottery_row.iloc[-1]["encrypted_lottery"]

# Train Prediction Model
df["drawdate"] = pd.to_datetime(df["drawdate"], errors="coerce")
df = df.dropna(subset=["drawdate"])
df["drawdate_ordinal"] = df["drawdate"].apply(lambda x: x.toordinal())

X = df[["drawdate_ordinal"]]
y = df["encrypted_lottery"].astype(str)

print("Checking for NaN values in y...")
if y.isna().any():
    print(f"Found {y.isna().sum()} NaN values in y. Cleaning now...")
    y = y.dropna()
    X = X.loc[y.index]

print("Missing values in y after cleaning:", y.isna().sum())

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, y_encoded)

# Database Setup
conn = sqlite3.connect("lottery_results.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS lottery_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT,
                    draw_date TEXT,
                    user_lottery_number TEXT,
                    prediction_result TEXT)''')
conn.commit()

# User Interaction
user_name = input("\nEnter your name: ")
user_lottery_number = int(input("Enter a number between 1-50 as your lottery pick: "))

# Encrypt User's Lottery Number before storing
encrypted_user_lottery = encrypt_data(str(user_lottery_number))

# Retrieve and Decrypt Lottery Numbers
decrypted_lottery_numbers = decrypt_data(encrypted_lottery)
if decrypted_lottery_numbers:
    drawn_numbers_list = [int(num) for num in decrypted_lottery_numbers.split(",")]
    is_winner = user_lottery_number in drawn_numbers_list
    result_message = "Congratulations! You won!" if is_winner else "Try Again!"
else:
    result_message = "Error decrypting lottery numbers."

# Store in Database (Encrypted)
cursor.execute("INSERT INTO lottery_entries (user_name, draw_date, user_lottery_number, prediction_result) VALUES (?, ?, ?, ?)",
               (user_name, today_date, encrypted_user_lottery, result_message))
conn.commit()

# Display Results
print(f"\nLottery Draw Results for {user_name}:")
print(f"Your chosen number: {user_lottery_number}")
print(f"Result: {result_message}")

conn.close()
