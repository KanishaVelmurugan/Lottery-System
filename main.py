from models.train_model import rf_model
from encryption.encryption import load_key, decrypt_data
import pandas as pd

# Load encrypted data
df = pd.read_csv("data/encrypted_lottery_predictions.csv")
key = load_key()

# Decrypt results
decrypted_results = []
for _, row in df.iterrows():
    decrypted_date = decrypt_data(row['Encrypted Draw Date'], key)
    decrypted_balls = [decrypt_data(row[col], key) for col in df.columns[1:]]
    decrypted_results.append([decrypted_date] + decrypted_balls)

# Display decrypted results
print("Decrypted Predictions:")
for result in decrypted_results:
    print("Draw Date:", result[0], "| Winning Numbers:", result[1:])
