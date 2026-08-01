import os
import sqlite3
import pickle
import hashlib
import random

# CWE-89: SQL Injection
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()

# CWE-78: Command Injection
def ping_host(host):
    os.system("ping " + host)

# CWE-798: Hardcoded credentials
password = "admin123"
api_key = "sk-hardcoded-secret-key"

# CWE-22: Path Traversal
def read_file(filename):
    with open("/var/www/" + filename) as f:
        return f.read()

# CWE-502: Insecure Deserialization
def load_session(data):
    return pickle.loads(data)

# CWE-327: Weak Hashing
def hash_password(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# CWE-338: Insecure Random
def generate_token():
    return str(random.randint(100000, 999999))
