# AI Study Buddy with Persistent Memory

An intelligent study companion that remembers everything about you—your learning history, preferences, past questions, and goals—to deliver truly personalized tutoring across sessions. Moves beyond one-off chatbots to build a long-term relationship with each learner.

---

##  Why This Project?

Every student learns differently. Generic chatbots start fresh every conversation, forcing you to repeat your context, goals, and learning style. This AI Study Buddy solves that by implementing **long-term and short-term memory**, creating a seamless, adaptive learning experience that feels like a real tutor who knows you.

---

##  Key Features

- **Session Memory** – Remembers everything said during a single study session.
- **User Profile Memory** – Stores your name, preferred subjects, learning style (visual, step-by-step, etc.), and explicit facts you share.
- **Episodic Memory** – Recalls past conversations, mistakes, and questions from weeks ago using semantic search.
- **Smart Retrieval** – Injects only the most relevant memories into each response, respecting context limits.
- **Privacy Dashboard** – View, edit, or delete everything the assistant remembers about you.
- **Goal Tracking** – Remembers your deadlines (exams, projects) and adjusts study plans accordingly.
- *(Optional)* Spaced repetition, progress visualization, multi-modal support (PDF/image uploads).

---

##  Technology Stack (Conceptual)

- **LLM Integration** – OpenAI, Anthropic Claude, or open-source models (Llama, Mistral) via API or local hosting.
- **Embeddings** – Sentence-transformers, OpenAI embeddings, or similar for semantic search.
- **Vector Database** – Pinecone, Weaviate, Qdrant, or Chroma for storing and retrieving episodic memories.
- **Relational Database** – PostgreSQL, SQLite, or MongoDB for user profiles, preferences, and explicit facts.
- **Backend Framework** – FastAPI, Node.js/Express, or Django.
- **Frontend** – React, Vue, or simple HTML/JavaScript for prototyping.
- **Authentication** – JWT, Auth0, or Firebase Auth.

---

##  How It Works (High-Level)

1. **User signs in** – Profile data (learning style, goals) is loaded from the relational database.
2. **Conversation starts** – The system retrieves relevant past memories from the vector database using embeddings of the current query.
3. **Prompt assembly** – The LLM receives: system prompt (tutor persona), user profile, recent session history, and a few relevant past memories.
4. **Response generation** – The assistant replies with context-aware personalization.
5. **Memory update** – New information is extracted, summarized, and stored (explicit facts → relational DB; conversations → vector DB).
6. **Privacy layer** – Users can inspect and manage all stored data via a dedicated dashboard.

---

##  Getting Started (Placeholder)

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-study-buddy.git
cd ai-study-buddy

# Install dependencies (example for Python)
pip install -r requirements.txt

# Set up environment variables (API keys, database URLs)
cp .env.example .env

# Run database migrations
python manage.py migrate

# Start the development server
python app.py
```

*Note: Actual setup will depend on your chosen stack.*

---

## 🗺️ Development Roadmap

### Phase 1: Basic Chatbot
- Single‑session tutor with no persistent memory.
- Simple frontend and LLM integration.

### Phase 2: Short‑Term Memory
- Maintain conversation history within a session.
- Manage token limits via sliding window or summarization.

### Phase 3: Long‑Term Profile Memory
- User authentication and database storage.
- Store explicit facts (name, learning style, goals) and inject them into every session.

### Phase 4: Episodic Memory
- Generate embeddings for past conversations.
- Store and retrieve relevant memories using a vector database.
- Augment prompts with retrieved memories.

### Phase 5: Intelligent Memory Management
- Summarize long conversations into compact memory entries.
- Implement forgetting mechanisms (user‑controlled deletion).
- Optimize retrieval (relevance scoring, recency weighting).

### Phase 6: Privacy & User Control
- Build a “Memory Bank” UI to view/edit/delete stored data.
- Encrypt sensitive information.
- Comply with data protection best practices.

### Phase 7: Advanced Enhancements (Optional)
- Spaced repetition scheduling.
- Progress dashboards.
- Integration with calendars, Notion, or learning platforms.
- Multi‑modal input (PDF/image understanding).

---

##  Privacy First

- **Transparency** – Users can see exactly what the assistant remembers.
- **Control** – Edit or delete any memory at any time.
- **Security** – Data encrypted at rest and in transit; API keys stored securely.

---

##  Contributing

Contributions are welcome! Please open an issue or submit a pull request with your ideas.

---


##  Acknowledgements

Inspired by the need for truly personalized AI companions and the exciting advances in long‑term memory for large language models.

---

*Built with curiosity and a passion for smarter learning.*