import os
import asyncio
import json
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from dotenv import load_dotenv

# Import your local modules
from database import get_user_context, save_user_fact, get_all_user_facts
from vector_memory import save_episode, recall_past_episodes, clear_episodic_memory, get_recent_topics
from security_utils import get_privacy_policy, export_user_data

load_dotenv()

# --- GLOBALS & CLIENT ---
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

BASE_INSTRUCTIONS = (
    "You are a Socratic Study Tutor. Your goal is to help students learn "
    "by asking guiding questions. NEVER give the full answer immediately. "
    "Break problems down. If the student is correct, praise them and "
    "ask a follow-up to deepen understanding."
)

# --- ASYNC UTILITIES ---

async def extract_keywords_and_subject(user_input: str) -> dict:
    prompt = [
        {"role": "system", "content": "Analyze the input. Return JSON: {'subject': 'math/history/etc', 'keywords': []}"},
        {"role": "user", "content": user_input}
    ]
    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=prompt,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"subject": "general", "keywords": []}

async def extract_and_save_facts(username, user_input):
    extraction_prompt = [
        {"role": "system", "content": "Extract permanent student facts (learning style, goals) as JSON: {'facts': [{'key': '...', 'value': '...'}]}"},
        {"role": "user", "content": user_input}
    ]
    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=extraction_prompt,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        facts = data.get("facts", [])
        for fact in facts:
            save_user_fact(username, fact['key'], fact['value'])
    except:
        pass

# --- THE MAIN BRAIN (WEB COMPATIBLE) ---

async def get_tutor_response_web(user_input: str, username: str) -> str:
    """
    This is the function app.py calls. It handles the full RAG pipeline 
    and returns a single string response.
    """
    # 1. Get Long Term Memory (SQL)
    long_term_memory = get_user_context(username)
    
    # 2. Build personalized system message
    system_message = {"role": "system", "content": f"{BASE_INSTRUCTIONS}\n\n[USER CONTEXT]\n{long_term_memory}"}

    # 3. Analyze Input
    analysis = await extract_keywords_and_subject(user_input)
    current_subject = analysis.get("subject", "general")
    keywords = ", ".join(analysis.get("keywords", []))

    # 4. Recall Past Episodes (Vector)
    hybrid_query = f"Keywords: {keywords}. Context: {user_input}"
    past_memories = recall_past_episodes(hybrid_query, username, current_subject)
    
    # 5. Build the context injection
    messages = [system_message]
    if past_memories:
        memory_context = f"\n[PAST LESSONS ON {current_subject.upper()}]\n" + "\n---\n".join(past_memories)
        messages.append({"role": "system", "content": memory_context})
    
    messages.append({"role": "user", "content": user_input})

    # 6. Generate Response
    try:
        response = await client.chat.completions.create(
            model="openrouter/free",
            extra_body={"models": ["google/gemini-2.0-flash-exp:free"], "route": "fallback"},
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        tutor_reply = response.choices[0].message.content.strip()

        # 7. Persistence (Save in background)
        save_episode(username, current_subject, user_input, tutor_reply)
        asyncio.create_task(extract_and_save_facts(username, user_input))

        return tutor_reply

    except Exception as e:
        return f"I'm sorry, I'm having trouble thinking right now. (Error: {str(e)})"

# --- MANAGEMENT LOGIC ---

async def handle_management_command(user_input, username):
    cmd_lower = user_input.lower()
    
    # Check for keywords instead of exact phrases
    is_memory_req = "memory" in cmd_lower and ("show" in cmd_lower or "dashboard" in cmd_lower)
    
    if is_memory_req:
        facts = get_all_user_facts(username)
        topics = get_recent_topics(username)
        
        dashboard = f"### 🧠 Memory Dashboard: {username}\n\n"
        dashboard += "**Known Facts:**\n"
        dashboard += "\n".join([f"- {f[0].title()}: {f[1]}" for f in facts]) if facts else "- None yet."
        dashboard += "\n\n**Recent Topics:**\n"
        dashboard += f"- {', '.join([t.title() for t in topics])}" if topics else "- No history."
        return dashboard
    
    if any(phrase in cmd_lower for phrase in ["privacy", "policy"]):
        return get_privacy_policy()

    if "export" in cmd_lower:
        file_path = export_user_data(username)
        return f"✅ Data vault prepared: `{file_path}`"

    return None

# --- TERMINAL ONLY LOGIC ---

async def terminal_main():
    """Only runs if you execute 'python chatbot.py' directly."""
    print("--- Socratic Tutor (Terminal Mode) ---")
    user_nm = input("What is your name? ")
    
    while True:
        u_input = input("\nYou: ")
        if u_input.lower() == "exit": break
        
        # Check management
        m_resp = await handle_management_command(u_input, user_nm)
        if m_resp:
            print(f"\nTutor: {m_resp}")
            continue
            
        # Get normal response
        resp = await get_tutor_response_web(u_input, user_nm)
        print(f"\nTutor: {resp}")

if __name__ == "__main__":
    asyncio.run(terminal_main())