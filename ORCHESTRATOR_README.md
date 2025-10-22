# 🎭 New Orchestrator System - Complete Guide

## Overview

This document describes the **new multi-agent orchestration system** built with clean A2A (Agent-to-Agent) protocol, replacing legacy RAG workflows with a purpose-built architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUERY                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              INTENT ROUTER                                   │
│  • LLM-based classification (no hardcoded rules)            │
│  • Extracts entities (specialization, role, company, year) │
│  • Routes: SQL / Vector / Hybrid                            │
│  • Memory usage detection                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MEMORY AGENT (if needed)                       │
│  • 6-turn rolling window                                    │
│  • 2-hour TTL per session                                   │
│  • Provides context for follow-up queries                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────┐        ┌──────────────────┐
│  SQL TOOL    │        │  VECTOR TOOL     │
│              │        │  (Pinecone)      │
│  Structured  │        │  Unstructured    │
│  Database    │        │  JD Snippets     │
└──────┬───────┘        └──────┬───────────┘
       │                       │
       └───────────┬───────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│           SYNTHESIZER & SUMMARIZER                          │
│  • Combines SQL + Vector results                            │
│  • Gemini-powered synthesis                                 │
│  • Tone: Linus + Aristotle + Robert Greene                  │
│  • Generates: Full answer + Brief summary + Sources         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MEMORY STORAGE                                 │
│  • Stores turn in session memory                            │
│  • Tracks entities for follow-up queries                   │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
              FINAL RESPONSE
```

## Components

### 1. Intent Router (`app/agents/intent_router.py`)

**Responsibilities:**
- Classify user intent using Gemini LLM
- Extract entities: specialization, role, company, year
- Determine routing: `structured_db`, `vector_db`, or `hybrid`
- Detect if memory context is needed
- No fallback logic (LLM-only classification)

**Key Features:**
- Entities support multiple values (arrays)
- "Analytics" disambiguation: "Analytics" alone → "General" specialization
- No hardcoded rules, only examples for LLM
- Confidence scoring (0.0 - 1.0)

**Specializations:**
- Business Analytics
- Finance
- HR
- Lean Operations & Systems
- Marketing
- General

### 2. Memory Agent (`app/agents/memory_agent.py`)

**Responsibilities:**
- Store conversation history per session
- Provide context for follow-up queries
- Auto-cleanup expired sessions

**Key Features:**
- 6-turn rolling window (5-6 chats as requested)
- 2-hour TTL per session
- Stores: query, intent, entities, route, response summary
- Thread-safe with locks
- Can extract last entities for context resolution

### 3. SQL Tool (`app/sql_tool.py`)

**Responsibilities:**
- Query structured SQLite database
- Canonical query matching
- LlamaIndex NLSQLTableQueryEngine fallback

**Key Features:**
- Deterministic canonical queries for common patterns
- Natural language to SQL conversion
- Returns formatted results

### 4. Vector Tool (`app/rag.py`)

**Responsibilities:**
- Query Pinecone vector database
- Retrieve relevant JD snippets
- Company-specific filtering

**Key Features:**
- HNSW semantic search
- Company normalization filters
- Relevance scoring and noise filtering
- Supports 384-dimension embeddings (Gemini text-embedding-004)

### 5. Synthesizer (`app/rag.py` - `synthesize_answer()`)

**Responsibilities:**
- Combine SQL and vector results
- Generate final answer with citations
- Apply conversational tone

**Key Features:**
- Gemini-powered synthesis
- Tone: Linus (direct) + Aristotle (structured) + Robert Greene (strategic)
- Markdown formatting for readability
- Context-aware (uses memory when available)

### 6. Orchestrator (`app/orchestrator.py`)

**Responsibilities:**
- Main coordinator for A2A protocol
- Executes complete agent pipeline
- No fallbacks or legacy paths

**Flow:**
1. Get memory context (if session exists)
2. Intent classification and routing
3. Execute retrieval (SQL/Vector/Hybrid)
4. Synthesize final answer
5. Store turn in memory
6. Return structured response

## API Endpoints

### New Orchestrator Endpoint

**POST** `/orchestrator/query`

**Request:**
```json
{
  "query": "How many companies came for marketing?",
  "session_id": "user_session_123",
  "user_id": "student_123",
  "user_context": {
    "specialization": "Marketing",
    "batch_year": "2024"
  }
}
```

**Response:**
```json
{
  "answer": "There are 15 companies offering marketing roles.",
  "intent": "count companies by specialization",
  "route": "structured_db",
  "entities": {
    "specialization": ["marketing"],
    "role": [],
    "company": []
  },
  "confidence": 0.95,
  "sources": [
    {
      "type": "sql",
      "content": "There are 15 companies offering marketing roles.",
      "source": "sql_database"
    }
  ],
  "used_memory": false,
  "session_id": "user_session_123"
}
```

## Running the System

### Start the Server

```bash
# Make sure you're in the project root
cd /Users/navinsivakumar/Desktop/JD-Copilot

# Run with uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Test the Orchestrator

```bash
# Run test suite
python test_orchestrator.py
```

### Make API Calls

```bash
# Using curl
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many companies came for marketing?",
    "session_id": "test_session",
    "user_id": "test_user"
  }'
```

## Environment Variables

Required variables in `.env`:

```bash
# Gemini API Key (for LLM)
GEMINI_API_KEY=your_gemini_api_key

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=jd-embeddings

# Database Path
DATABASE_PATH=data/placement_data.db

# Embedding Model
EMBED_MODEL=gemini/text-embedding-004
```

## Testing Scenarios

### 1. Simple SQL Query
```json
{
  "query": "How many companies came for marketing?",
  "session_id": "test_1"
}
```
**Expected:** Structured DB route, count result

### 2. Company-Specific JD Analysis
```json
{
  "query": "Tell me about Honasa Consumer's management trainee program",
  "session_id": "test_2"
}
```
**Expected:** Vector DB route, detailed JD analysis

### 3. Hybrid Query
```json
{
  "query": "What skills are required for finance roles?",
  "session_id": "test_3"
}
```
**Expected:** Hybrid route, SQL + Vector results

### 4. Follow-up Query (Memory)
```json
// First query
{
  "query": "List companies for marketing",
  "session_id": "test_4"
}

// Follow-up query
{
  "query": "What about their salary ranges?",
  "session_id": "test_4"
}
```
**Expected:** Memory agent provides context, "their" refers to marketing companies

## Key Design Decisions

### 1. No Fallbacks
- Intent Router must succeed or fail explicitly
- No legacy RAG paths
- Clean error handling with specific messages

### 2. LLM-Only Intent Classification
- No hardcoded rules (except specialization database validation)
- Examples-only approach in system prompt
- Gemini handles natural language understanding

### 3. Entity Arrays
- Entities support multiple values: `["company1", "company2"]`
- Router can extract: "Google and Microsoft" → `["Google", "Microsoft"]`

### 4. Memory as Optional Context
- Memory Agent provides context when needed
- Router decides if memory is relevant
- 6-turn rolling window prevents context overload

### 5. Existing Tools Reused
- SQL tool (`app/sql_tool.py`) unchanged
- Vector tool (`app/rag.py`) unchanged
- Synthesizer (`synthesize_answer()`) unchanged
- Clean integration via orchestrator

## Comparison with Legacy System

| Feature | Legacy System | New Orchestrator |
|---------|---------------|------------------|
| Intent Classification | Hardcoded rules + LLM fallback | LLM-only, no fallback |
| Memory | Complex chat history | Simple 6-turn window |
| Routing | Multiple fallback paths | Single A2A protocol |
| Entity Extraction | Single values | Multiple values (arrays) |
| Synthesis | Multiple prompts/personas | Unified Strategic Intelligence Analyst |
| Error Handling | Silent fallbacks | Explicit errors |
| Testing | Difficult to isolate | Clean unit testing |

## Troubleshooting

### Common Issues

**1. Gemini API Key Missing**
```bash
# Error: GEMINI_API_KEY not set
# Solution: Add to .env file
GEMINI_API_KEY=your_key_here
```

**2. Pinecone Connection Failed**
```bash
# Error: Pinecone index not found
# Solution: Check PINECONE_INDEX_NAME matches your index
PINECONE_INDEX_NAME=jd-embeddings
```

**3. Database Not Found**
```bash
# Error: DATABASE_PATH not found
# Solution: Ensure data/placement_data.db exists
python -m ingest.pipeline --pdf_dir data/jds
```

**4. Intent Router Confidence Low**
- Check if query is ambiguous
- Add more examples to Intent Router system prompt
- Verify entities are correctly extracted

**5. Memory Not Working**
- Ensure same `session_id` is used for follow-up queries
- Check if session expired (2-hour TTL)
- Verify `use_memory` flag in RouterDecision

## Future Enhancements

### Planned Features
1. **Redis-backed Memory** - Scale memory across multiple instances
2. **Streaming Responses** - Real-time answer generation
3. **Multi-turn Planning** - Complex query decomposition
4. **Feedback Loop** - User feedback improves routing
5. **A/B Testing** - Compare orchestrator vs legacy system
6. **Metrics Dashboard** - Route distribution, latency, confidence scores

### Extension Points
- Add new agents (e.g., Citation Agent, Fact-Checker Agent)
- Custom routing strategies per user profile
- Dynamic prompt tuning based on user feedback
- Integration with external APIs (LinkedIn, company websites)

## Contributing

When adding new features:

1. **Maintain A2A Protocol** - All agents must follow clean communication
2. **No Fallbacks** - Fail explicitly, don't silently degrade
3. **Test Coverage** - Add tests for new agents/routes
4. **Documentation** - Update this README with new flows
5. **Entity Validation** - Ensure entities match database schema

## Support

For issues or questions:
- Check logs: `uvicorn` console output shows detailed flow
- Run test suite: `python test_orchestrator.py`
- Review agent prompts: `app/agents/intent_router.py` (line ~80-500)
- Inspect memory state: Memory Agent has `get_session_summary()` method

---

**Last Updated:** 2025-01-XX  
**Maintainer:** JD-Copilot Team  
**Status:** Production Ready ✅
