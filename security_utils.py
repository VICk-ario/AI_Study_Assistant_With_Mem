import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Load the key from .env
SECRET_KEY = os.getenv("ENCRYPTION_KEY")
if not SECRET_KEY:
    raise ValueError("No ENCRYPTION_KEY found in .env file!")

cipher_suite = Fernet(SECRET_KEY.encode())

def encrypt_text(plain_text: str) -> str:
    """Converts readable text into a scrambled string."""
    if not plain_text: return ""
    encrypted_bytes = cipher_suite.encrypt(plain_text.encode())
    return encrypted_bytes.decode()

def decrypt_text(encrypted_text: str) -> str:
    """Converts scrambled string back into readable text."""
    if not encrypted_text: return ""
    decrypted_bytes = cipher_suite.decrypt(encrypted_text.encode())
    return decrypted_bytes.decode()

def get_privacy_policy():
    """Returns a structured privacy statement for the Socratic Tutor."""
    return """
--- 🛡️ PRIVACY & DATA PROTECTION POLICY ---

1. DATA COLLECTION (What I Remember):
   • Explicit Facts: Personal preferences and learning goals (stored in SQL).
   • Episodic Memory: Past academic conversations (stored in ChromaDB).
   
2. SECURITY (How I Protect You):
   • All data is encrypted at rest using AES-256 (Fernet) encryption.
   • Your encryption key is stored locally in your environment file (.env).
   
3. THIRD PARTIES (Where Data Travels):
   • I use LLM providers (via OpenRouter) to process your questions. 
   • While stored data is encrypted, text is sent to the AI in transit to generate responses.

4. YOUR CONTROL (Your Rights):
   • Access: Type 'dashboard' to see everything I know about you.
   • Deletion: Type 'forget [subject]' to wipe specific memories.
   • Portability: Type 'export' to download your entire data vault as a JSON file.
--------------------------------------------
    """