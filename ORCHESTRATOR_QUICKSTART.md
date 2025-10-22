# 🚀 Orchestrator Quick Start

## 5-Minute Setup

### 1. Environment Setup

```bash
# Navigate to project
cd /Users/navinsivakumar/Desktop/JD-Copilot

# Ensure .env file has required keys
cat .env | grep -E "GEMINI_API_KEY|PINECONE_API_KEY|DATABASE_PATH"

# If missing, add:
echo "GEMINI_API_KEY=your_key" >> .env
echo "PINECONE_API_KEY=your_key" >> .env
echo "PINECONE_INDEX_NAME=jd-embeddings" >> .env
echo "DATABASE_PATH=data/placement_data.db" >> .env
```

### 2. Start Server

```bash
# Start with auto-reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# You should see:
# ✅ Query Orchestrator initialized
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. Test Endpoint

```bash
# Simple test
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many companies came for marketing?",
    "session_id": "test_session",
    "user_id": "test_user"
  }'
```

## Common Queries

### Count Queries (SQL Route)
```bash
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many companies came for finance?",
    "session_id": "session1"
  }'
```

### Company Analysis (Vector Route)
```bash
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Google marketing roles",
    "session_id": "session2"
  }'
```

### Skills Analysis (Hybrid Route)
```bash
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What skills are needed for HR roles?",
    "session_id": "session3"
  }'
```

### Follow-up Query (Memory)
```bash
# First query
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List companies for marketing",
    "session_id": "session4"
  }'

# Follow-up (same session_id)
curl -X POST "http://127.0.0.1:8000/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about their salary ranges?",
    "session_id": "session4"
  }'
```

## Python Test

```python
# test_quick.py
import asyncio
import requests

async def quick_test():
    url = "http://127.0.0.1:8000/orchestrator/query"
    
    payload = {
        "query": "How many companies came for marketing?",
        "session_id": "test_session",
        "user_id": "test_user"
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    print(f"Intent: {result['intent']}")
    print(f"Route: {result['route']}")
    print(f"Answer: {result['answer']}")

asyncio.run(quick_test())
```

## Understanding Routes

| Route | When Used | Example Query |
|-------|-----------|---------------|
| `structured_db` | Counts, lists, statistics | "How many companies for marketing?" |
| `vector_db` | Company analysis, JD details | "Tell me about Google's SDE role" |
| `hybrid` | Skills, requirements, complex | "What skills are needed for finance?" |

## Checking Logs

```bash
# Server logs show complete flow
# Look for:
# 🎬 ORCHESTRATOR: Processing query
# 🔍 Intent Router: Analyzing query
# 📊 SQL: Querying structured database
# 🔮 Vector: Querying Pinecone
# ✨ Synthesizer: Generating response
# ✅ ORCHESTRATOR: Query processing complete
```

## Troubleshooting

### Server won't start
```bash
# Check Python environment
python --version  # Should be 3.9+

# Check dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8000  # Kill any existing process
```

### API returns 500 error
```bash
# Check server logs for detailed error
# Common issues:
# 1. Missing API keys in .env
# 2. Database file not found
# 3. Pinecone index doesn't exist
```

### Intent Router not working
```bash
# Test Intent Router directly
python -c "
from app.agents.intent_router import get_intent_router
router = get_intent_router()
decision = router.classify_and_route('How many companies?', {}, 'test')
print(decision)
"
```

### Memory not working
```bash
# Ensure same session_id for follow-up queries
# Check memory TTL (default 2 hours)
# Verify session exists:
from app.agents.memory_agent import get_memory_agent
memory = get_memory_agent()
context = memory.get_context('your_session_id')
print(context)
```

## Next Steps

1. **Read Full Documentation**: `ORCHESTRATOR_README.md`
2. **Run Test Suite**: `python test_orchestrator.py`
3. **Explore Intent Router**: `app/agents/intent_router.py`
4. **Check Memory Agent**: `app/agents/memory_agent.py`
5. **Review Orchestrator**: `app/orchestrator.py`

## Quick Reference

### API Endpoint
```
POST /orchestrator/query
```

### Request Body
```json
{
  "query": "string (required)",
  "session_id": "string (default: 'default')",
  "user_id": "string (default: 'anonymous')",
  "user_context": "object (optional)"
}
```

### Response Fields
```json
{
  "answer": "string - final synthesized answer",
  "intent": "string - classified intent",
  "route": "string - structured_db/vector_db/hybrid",
  "entities": "object - extracted entities",
  "confidence": "float - 0.0 to 1.0",
  "sources": "array - data sources used",
  "used_memory": "boolean - memory context used",
  "session_id": "string - session identifier"
}
```

---

**Need Help?** Check server logs or run `python test_orchestrator.py` for diagnostics.
