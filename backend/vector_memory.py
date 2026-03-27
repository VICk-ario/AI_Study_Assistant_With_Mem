import chromadb
from chromadb.utils import embedding_functions
import datetime
import json
from security_utils import encrypt_text, decrypt_text

#initialize the persistent ChromaDB client
#This creates a folder called 'chroma_storage ' in your directory to save memories forever
client = chromadb.PersistentClient(path="./chroma_storage")

#get or create a "collection"(This is like a table in a traditional database) to store our memories
collection = client.get_or_create_collection(name="episodic_memories")
# We need to manually call the embedding function so we can embed PLAIN text 
# but store ENCRYPTED text.
default_ef = embedding_functions.DefaultEmbeddingFunction()

def save_episode(username, subject, user_input, tutor_response):
    """Embeds plain text but stores encrypted text in ChromaDB."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    plain_text = f"[{timestamp}] Subject: {subject}\nStudent: {user_input}\nTutor: {tutor_response}"
    
    # 1. Generate the embedding from the READABLE text
    # This ensures the 'coordinates' in the database are correct.
    embedding = default_ef([plain_text])[0]
    
    # 2. Scramble the text for storage
    encrypted_doc = encrypt_text(plain_text)
    
    memory_id = f"{username}_{datetime.datetime.now().timestamp()}"

    collection.add(
        documents=[encrypted_doc], # Scrambled text goes to disk
        embeddings=[embedding],    # Clean math for searching
        metadatas=[{"username": username, "subject": subject.lower()}],
        ids=[memory_id]
    )
    print(f"--- [Security] Encrypted episode saved for {username} ---")
    
def recall_past_episodes(query, username, subject=None, n_results=2):
    """Retrieves and decrypts past memories."""
    if collection.count() == 0:
        return []

    where_filter = {"username": username}
    if subject and subject.lower() != "general":
        where_filter = {"$and": [{"username": {"$eq": username}}, {"subject": {"$eq": subject.lower()}}]}

    # Chroma will automatically embed your 'query' text using the same model
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter
    )
    
    encrypted_docs = results['documents'][0]
    
    # 3. Decrypt the results so the AI can read them
    decrypted_docs = []
    for doc in encrypted_docs:
        try:
            decrypted_docs.append(decrypt_text(doc))
        except Exception:
            # Fallback for old unencrypted data
            decrypted_docs.append(doc)
            
    return decrypted_docs

def clear_episodic_memory(username, subject=None):
    """Deletes episodic memories for a user. Optionally filters by subject."""
    if subject:
        # Delete only memories for a specific subject
        collection.delete(
            where={
                "$and": [
                    {"username": {"$eq": username}},
                    {"subject": {"$eq": subject.lower()}}
                ]
            }
        )
        print(f"[Vector DB] All {subject} memories cleared for {username}.")
    else:
        # Delete EVERYTHING for this user
        collection.delete(where={"username": username})
        print(f"[Vector DB] All memories wiped for {username}.")
        
def get_recent_topics(username):
    """Retrieves a unique list of subjects the user has studied."""
    # We query the most recent 10 entries for this user
    results = collection.get(
        where={"username": username},
        limit=10,
        include=["metadatas"]
    )
    
    if not results['metadatas']:
        return []

    # Extract unique subjects from metadata
    subjects = {m['subject'] for m in results['metadatas'] if 'subject' in m}
    return list(subjects)


def export_user_data(username):
    """Gathers all SQL and Vector data and saves it to a JSON file."""
    # We import this here to avoid circular imports if database.py 
    # already imports vector_memory.py
    from database import get_all_user_facts
    
    # 1. Get SQL Facts (Semantic Memory)
    facts = get_all_user_facts(username)
    
    # 2. Get all Chroma memories (Episodic Memory)
    # This assumes 'collection' is defined globally in this file
    memories = collection.get(where={"username": username})
    
    data_dump = {
        "user": username,
        "exported_at": str(datetime.datetime.now()),
        "explicit_facts": {k: v for k, v in facts},
        "conversational_history": memories['documents']
    }
    
    file_name = f"{username}_data_export.json"
    
    # Specify utf-8 encoding to prevent crashes on special characters
    with open(file_name, "w", encoding='utf-8') as f:
        json.dump(data_dump, f, indent=4, ensure_ascii=False)
    
    print(f"--- [Privacy] Data successfully exported to {file_name} ---")
    return file_name

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Testing Vector Database...")
    
    # 1. Save a fake past memory
    save_episode(
        session_id="Victor_Feb26", 
        user_input="What is the opportunity cost of buying a $20 video game?", 
        tutor_response="It is the next best thing you could have done with that $20, like saving it or buying lunch."
    )
    
    # 2. Try to recall it using a totally different, but semantically similar, sentence
    print("\nSearching for related memories...")
    memories = recall_past_episodes("Do you remember when we talked about giving up money to buy a game?")
    
    print("\n--- Retrieved Memories ---")
    for memory in memories:
        print(memory)
    
    