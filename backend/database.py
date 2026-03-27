import json
import sqlite3
from security_utils import encrypt_text, decrypt_text

DB_NAME = 'tutor_database.db'

def init_db():
    """Initializes the database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    #Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            firebase_uid TEXT UNIQUE
        ) 
        ''')
    
    #2. User Facts table (Learning style, weaknesses, goals)
    c.execute('''
            CREATE TABLE IF NOT EXISTS user_facts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fact_key TEXT ,
            fact_value TEXT ,
            FOREIGN KEY (user_id) REFERENCES users(id)
            UNIQUE(user_id, fact_key) -- THIS IS CRITICAL
            
        )
            
        
    ''')
    
    
    conn.commit()
    conn.close()
    print("Database initialized and tables created .")
    
def get_or_create_user(firebase_uid, email):
    """Links Firebase Identity to our Local SQL Database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT id FROM users WHERE firebase_uid = ?", (firebase_uid,))
    user = c.fetchone()
    
    if not user:
        # Create new local user mapped to Firebase UID
        c.execute("INSERT INTO users (firebase_uid, email, username) VALUES (?, ?, ?)", (firebase_uid, email, email))
        conn.commit()
        user_id = c.lastrowid
    else:
        user_id = user[0]
        
    conn.close()
    return user_id
    
def save_user_fact(username, key, value):
    """Encrypts and saves a user fact to the database."""
    encrypted_value = encrypt_text(value) # Scramble the data first
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Ensure user exists and get ID
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = c.fetchone()[0]
    
    # 2. Save or update the encrypted fact
    c.execute('''
        INSERT INTO user_facts (user_id, fact_key, fact_value) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, fact_key) DO UPDATE SET fact_value=excluded.fact_value
    ''', (user_id, key, encrypted_value)) # Use encrypted_value here!
    
    conn.commit()
    conn.close()
    print(f"--- [Security] Encrypted fact saved for {username} ---")
    
def get_user_context(username):
    """Retrieves, decrypts, and formats user facts for the system prompt."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = '''SELECT fact_key, fact_value FROM user_facts 
               JOIN users ON user_facts.user_id = users.id
               WHERE users.username = ?'''
    
    c.execute(query, (username,))
    facts = c.fetchall()
    conn.close()
    
    if not facts:
        return "New student with no recorded preferences."
    
    # 3. Decrypt the facts for the AI to read
    decrypted_lines = []
    for key, encrypted_val in facts:
        try:
            plain_val = decrypt_text(encrypted_val)
            decrypted_lines.append(f"{key}: {plain_val}")
        except Exception:
            # Fallback in case there's old, unencrypted data in the DB
            decrypted_lines.append(f"{key}: {encrypted_val}")

    context_str = "Known information about this student:\n" + "\n".join(decrypted_lines)
    return context_str

def delete_user_fact(username, key):
    """Deletes a specific fact about a user from the SQL database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Assuming your table has a 'username' or you've linked it via user_id
    c.execute('''
        DELETE FROM user_facts 
        WHERE user_id = (SELECT id FROM users WHERE username = ?) 
        AND fact_key = ?
    ''', (username, key))
    conn.commit()
    conn.close()
    print(f"[SQL DB] Fact '{key}' deleted for {username}.")

def get_all_user_facts(username):
    """Retrieves all key-value pairs for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT fact_key, fact_value FROM user_facts 
        WHERE user_id = (SELECT id FROM users WHERE username = ?)
    ''', (username,))
    facts = c.fetchall()
    conn.close()
    return facts # Returns a list of tuples: [('learning_style', 'visual'), ...]

if __name__ == "__main__":
    init_db()