import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from encryption import encrypt_data, load_key

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from encryption import encrypt_data, load_key

# Load dataset
df = pd.read_csv("data/secure_lottery_prediction.csv")

# Remove unnecessary columns
df = df[['drawdate', 'ball1', 'ball2', 'ball3', 'ball4', 'ball5']]
df['drawdate'] = pd.to_datetime(df['drawdate'], errors='coerce', dayfirst=True)

# Generate future dates correctly using pd.Timedelta
future_dates = np.array([(df['drawdate'].max() + pd.Timedelta(days=i)) for i in range(1, 6)]).reshape(-1, 1)

# Prepare data
X = df[['drawdate']]
y = df[['ball1', 'ball2', 'ball3', 'ball4', 'ball5']]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, y)

# Predict next 5 draws
future_dates = np.array([(df['drawdate'].max() + pd.Timedelta(days=i)).toordinal() for i in range(1, 6)]).reshape(-1, 1)


predicted_numbers = rf_model.predict(future_dates)

# Encrypt predictions
key = load_key()
encrypted_results = []
for i, date in enumerate(future_dates.flatten()):
    encrypted_date = encrypt_data(str(date), key)
    encrypted_balls = [encrypt_data(str(num), key) for num in predicted_numbers[i]]
    encrypted_results.append([encrypted_date] + encrypted_balls)

# Save encrypted predictions
pd.DataFrame(encrypted_results, columns=['Encrypted Draw Date', 'Ball1', 'Ball2', 'Ball3', 'Ball4', 'Ball5'])\
    .to_csv("data/encrypted_lottery_predictions.csv", index=False)

print("Predictions encrypted and saved successfully!")
