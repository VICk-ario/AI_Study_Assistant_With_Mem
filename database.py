import sqlite3

DB_NAME = 'tutor_database.db'

def init_db():
    """Initializes the database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    #Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
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
            
        )
            
        
    ''')
    
    
    conn.commit()
    conn.close()
    print("Database initialized and tables created .")
    
def save_user_fact(username, key, value):
    """Saves a user fact (like learning style, weaknesses, goals) to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get user_id from username
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        # If user doesn't exist, create them
        c.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = c.lastrowid
    else:
        user_id = user[0]
    
    # Save or update the user fact
    c.execute('''
        INSERT INTO user_facts (user_id, fact_key, fact_value) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, fact_key) DO UPDATE SET fact_value=excluded.fact_value
    ''', (user_id, key, value))
    
    conn.commit()
    conn.close()
    
def get_user_context(username):
    """Retrieves all facts about a user and formats them for the system prompt."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = '''SELECT fact_key, fact_value FROM user_facts 
               JOIN users ON user_facts.user_id = users.id
               WHERE users.username = ?'''
    
    # Get user_id from username
    c.execute(query, (username,))
    facts = c.fetchall()
    conn.close()
    
    if not facts:
        return "New student with no recorded preferences."
    
    # Format facts into a string for the LLM
    context_str = "Known information about this student:\n" + "\n".join([f"{key}: {value}" for key, value in facts])
    
    return context_str

if __name__ == "__main__":
    init_db()