import sqlite3
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('ENCRYPTION_KEY')
if not key: print("No Key Found!"); exit()

cipher = Fernet(key)
conn = sqlite3.connect('journal.db')
c = conn.cursor()

print("🔄 Encrypting database...")

c.execute("SELECT id, content FROM entries")
rows = c.fetchall()

for row in rows:
    entry_id = row[0]
    content = row[1]
    
    # Check if already encrypted (Fernet tokens start with gAAAA...)
    if not content.startswith('gAAAA'):
        encrypted = cipher.encrypt(content.encode()).decode()
        c.execute("UPDATE entries SET content = ? WHERE id = ?", (encrypted, entry_id))
        print(f"Encrypted entry {entry_id}")

conn.commit()
conn.close()
print("✅ Database migration complete!")