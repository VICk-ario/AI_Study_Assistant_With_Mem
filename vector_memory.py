import chromadb
from chromadb.utils import embedding_functions
import datetime

#initialize the persistent ChromaDB client
#This creates a folder called 'chroma_storage ' in your directory to save memories forever
client = chromadb.PersistentClient(path="./chroma_storage")

#get or create a "collection"(This is like a table in a traditional database) to store our memories
collection = client.get_or_create_collection(name="episodic_memories")

def save_episode(username:str,subject:str, user_input:str, tutor_response:str):
    """
    Saves a learning episode to the ChromaDB collection.
    Each episode includes the session ID , subject, user input, tutor response, and an embedding for semantic search.
    """
    #Timestamp. This is vital for "weeks ago" recall because you can tell the AI when the memory happened.
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") 
    # We combine the exchange into one readable "memory" string
    memory_text = f"[{timestamp}] Student asked: {user_input}\nTutor replied: {tutor_response}"
    #We need a unique ID for every memory. We can use the session_id + the total count
    memory_count = collection.count()
    memory_id = f"{username}_{datetime.datetime.now().timestamp()}"

    # We add metadata keys that we can filter on later
    collection.add(
        documents=[memory_text],
        metadatas=[{
            "username": username, 
            "subject": subject, 
            "date": timestamp
        }],
        ids=[memory_id]
    )
    print(f"[Vector DB] Saved Episode : {memory_id}")
    
def recall_past_episodes(current_query: str, username: str, subject: str = None, n_results: int = 2) -> list[str]:
    """Searches the database for past exchanges similar to the current query."""
    # If the database is empty, return nothing
    if collection.count() == 0:
        return []
    # Construct the filter
    # We always filter by username so students don't see each other's memories
    where_filter = {"username": username}
    
    # If a specific subject is provided, we use a 'and' logic
    if subject:
        where_filter = {
            "$and": [
                {"username": {"$eq": username}},
                {"subject": {"$eq": subject}}
            ]
        }

    # Search the vector database
    results = collection.query(
        query_texts=[current_query],
        n_results=n_results,
        where=where_filter
    )
    
    # Extract the actual text documents from the results
    retrieved_memories = results['documents'][0]
    return retrieved_memories

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
    
    