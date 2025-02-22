from cryptography.fernet import Fernet

# Generate & save encryption key
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Load existing key
def load_key():
    return open("secret.key", "rb").read()

# Encrypt data
def encrypt_data(data, key):
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(data.encode()).decode()

# Decrypt data
def decrypt_data(encrypted_data, key):
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# Generate key if not exists
try:
    load_key()
except:
    generate_key()
