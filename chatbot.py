import os
import asyncio
from database import get_user_context, save_user_fact
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from dotenv import load_dotenv
import json
from vector_memory import save_episode, recall_past_episodes

load_dotenv()

async def extract_and_save_facts(username, user_input):
    """
    Analyses the user's input to see if they shared any permanent traits.
    Saves them to the database if found.
    """
    extraction_prompt = [
        {
            "role": "system", 
            "content": (
                "You are an information extraction bot. Monitor the user's message for "
                "permanent facts about their learning style, goals, or weaknesses. "
                "Ignore temporary things like 'I am tired.' "
                "Output ONLY a JSON object with a 'facts' key containing a list. "
                "Example: {'facts': [{'key': 'style', 'value': 'visual'}]}"
                "If no facts are found, output an empty list: []"
            )
        },
        {"role": "user", "content": user_input}
    ]

    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free", # Use a fast/free model
            messages=extraction_prompt,
            response_format={ "type": "json_object" } # Ensures we get clean JSON
        )
        
        # Parse the JSON response
        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        
        # Handle if data is a list directly or a dict with a 'facts' key
        facts = data.get("facts", []) if isinstance(data, dict) else data

        for fact in facts:
            key = fact.get("key")
            value = fact.get("value")
            if key and value:
                # Use your existing DB function
                save_user_fact(username, key, value)
                print(f"--- [Memory Log] Saved: {key} = {value} ---")

    except Exception as e:
        # We fail silently here so the user's chat isn't interrupted
        pass

BASE_INSTRUCTIONS = (
    "You are a Socratic Study Tutor. Your goal is to help students learn "
    "by asking guiding questions. NEVER give the full answer immediately. "
    "Break problems down. If the student is correct, praise them and "
    "ask a follow-up to deepen understanding."
)

username =  input("What is your name? ")
long_term_memory = get_user_context(username)


# 3. Create the ACTUAL system message for the session
# This combines instructions + what we remember about this specific person
PERSONALIZED_SYSTEM_MESSAGE = {
    "role": "system",
    "content": f"{BASE_INSTRUCTIONS}\n\n[USER MEMORY/CONTEXT]\n{long_term_memory}"
}
 #max number of messages to keep in history (excluding system prompt)
MAX_HISTORY_MESSAGES = 8
WINDOW_SIZE = 5


#The Async API caller
client = AsyncOpenAI(
    base_url= "https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
    )

async def get_tutor_response(messages: list[dict]) -> str | None:
    try:
        response = await client.chat.completions.create(
            # OpenRouter treats the first model as primary, others as fallbacks
            model="openrouter/free",
            extra_body={
                "models": [
                    "google/gemini-2.0-flash-exp:free",
                    "meta-llama/llama-3.1-70b-instruct:free",
                    "mistralai/mistral-7b-instruct:free"
                ],
                "route": "fallback" 
            },
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        print("\n[Error] Rate limit reached. Please wait a moment before continuing.\n")
    except APITimeoutError:
        print("\n[Error] The request timed out. Check your connection and try again.\n")
    except APIError as e:
        print(f"\n[Error] An API error occurred: {e}\n")
    return None

def trim_history(history: list[dict]) -> list[dict]:
    """
    Keep the session history within MAX_HISTORY_MESSAGES turns (user + assistant).
    The system prompt at index 0 is always preserved.
    """
    # session_history[0] is the system prompt, everything after is conversation
    conversation = history[1:]  # Exclude system prompt
    if len(conversation) > MAX_HISTORY_MESSAGES:
        # Keep only the most recent MAX_HISTORY_MESSAGES conversation turns
        conversation = conversation[-MAX_HISTORY_MESSAGES:]
    # Reattach system prompt to the trimmed history
    return [history[0]] + conversation


async def summarize_history(history):
    # We don't want to summarize the System Prompt, just the dialogue
    dialogue_only = [m for m in history if m["role"] != "system"]
    
    summary_request = [
        {
            "role": "system", 
            "content": "You are a memory manager. Summarize the following tutor-student exchange. "
                       "Focus on: 1. The concept being discussed. 2. What the student is struggling with. "
                       "3. The last hint given. Be extremely concise (max 3 sentences)."
        },
        {"role": "user", "content": str(dialogue_only)}
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-5-mini", # The fast/cheap utility model of 2026
            messages=summary_request,
            temperature=0.3 # Keep it factual and stable
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[System Tool Error] Summarization failed: {e}")
        return "Multiple topics discussed."
#the memory and loop: Keeping the session alive
async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "[Warning] OPENAI_API_KEY is not set. "
            "Add it to your environment or a .env file.\n"
            )
    #initialize session state with system prompt
    session_history = [PERSONALIZED_SYSTEM_MESSAGE]
    
    print(f"---Socratic Tutor Initialized for {username}---")
    print("Type 'exit' to end the session.\n")
    
    loop = asyncio.get_event_loop()
    
    while True:
        user_input = await loop.run_in_executor(None, input, "You: ")
        
        if user_input.strip().lower() == "exit":
            print("Ending session. Goodbye!")
            break
        
        if not user_input.strip():
            print("Please enter a question or statement to continue the session.\n")
            continue
        # 1. APPEND USER MESSAGE
        session_history.append({"role": "user", "content": user_input})
        
        # 2. RETRIEVE EPISODIC MEMORY (Optional Injection)
        past_memories = recall_past_episodes(user_input, n_results=2)
        
        # We create a temporary copy of history to send to the API
        # This keeps the 'past memories' from cluttering future turns
        temp_history = list(session_history) 
        
        if past_memories:
            memory_context = "\n[RELEVANT PAST LESSONS]\n" + "\n---\n".join(past_memories)
            # Insert memory context right after the first system prompt
            temp_history.insert(1, {"role": "system", "content": memory_context})

        # 3. SUMMARIZATION CHECK
        if len(session_history) > MAX_HISTORY_MESSAGES + 1:
            print("--- System: Consolidating memory ---")
            summary = await summarize_history(session_history[1:-1]) 
            session_history = [
                session_history[0],
                {"role": "assistant", "content": f"Summary: {summary}"},
                session_history[-1]
            ]
            # If we summarized, our temp_history is now outdated, so we refresh it
            temp_history = [session_history[0], {"role": "system", "content": memory_context if past_memories else ""}] + session_history[1:]
            
        print("Tutor is thinking...\n")
        # We send temp_history (with memories) but keep session_history clean
        tutor_response = await get_tutor_response(temp_history)
        
        if tutor_response:
            print(f"Tutor: {tutor_response}\n")
            session_history.append({"role": "assistant", "content": tutor_response})
            
            # Save the new episode
            save_episode(f"{username}_session", user_input, tutor_response)

            # Background Secretary
            asyncio.create_task(extract_and_save_facts(username, user_input))
 
 
if __name__ == "__main__":
    asyncio.run(main())