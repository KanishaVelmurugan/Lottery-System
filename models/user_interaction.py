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

# Decrypt Data (Admin Use Only)
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

# Database Setup
conn = sqlite3.connect("lottery_results.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS lottery_draws (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draw_date TEXT UNIQUE,
                    ball1 TEXT,
                    ball2 TEXT,
                    ball3 TEXT,
                    ball4 TEXT,
                    ball5 TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS lottery_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT,
                    draw_date TEXT,
                    user_lottery_number TEXT,
                    prediction_result TEXT)''')
conn.commit()

# Generate New Lottery Numbers for Today
today_date = datetime.now().strftime("%Y-%m-%d")
cursor.execute("SELECT ball1, ball2, ball3, ball4, ball5 FROM lottery_draws WHERE draw_date = ?", (today_date,))
draw_result = cursor.fetchone()

if not draw_result:
    #print("⚠️ Warning: No valid encrypted lottery found. Generating new lottery numbers.")
    new_lottery_numbers = np.random.randint(1, 51, 5).tolist()
    encrypted_lottery_numbers = [encrypt_data(str(num)) for num in new_lottery_numbers]
    
    cursor.execute("INSERT INTO lottery_draws (draw_date, ball1, ball2, ball3, ball4, ball5) VALUES (?, ?, ?, ?, ?, ?)",
                   (today_date, *encrypted_lottery_numbers))
    conn.commit()
else:
    encrypted_lottery_numbers = list(draw_result)

# User Interaction
user_name = input("\nEnter your name: ")
user_lottery_number = int(input("Enter a number between 1-50 as your lottery pick: "))

# Encrypt User's Lottery Number before storing
encrypted_user_lottery = encrypt_data(str(user_lottery_number))

# Retrieve and Decrypt Lottery Numbers
decrypted_lottery_numbers = [decrypt_data(num) for num in encrypted_lottery_numbers if num]
if decrypted_lottery_numbers:
    drawn_numbers_list = [int(num) for num in decrypted_lottery_numbers]
    is_winner = user_lottery_number in drawn_numbers_list
    result_message = "Congratulations! You won!" if is_winner else "Try Again!"
else:
    result_message = "Error decrypting lottery numbers."

# Store in Database (Encrypted)
cursor.execute("INSERT INTO lottery_entries (user_name, draw_date, user_lottery_number, prediction_result) VALUES (?, ?, ?, ?)",
               (user_name, today_date, encrypted_user_lottery, result_message))
conn.commit()

# Display Results (Users only see their outcome)
print(f"\nLottery Draw Results for {user_name}:")
print(f"Your chosen number: {user_lottery_number}")
print(f"Result: {result_message}")

# Admin View to See Decrypted Lottery Numbers
'''admin_view = input("\nAre you the admin? (yes/no): ")
if admin_view.lower() == "yes":
    print("\nDecrypted Lottery Numbers for Today:")
    print(decrypted_lottery_numbers)'''

conn.close()
