# Quick Reference: Adaptive Workflow Migration

## What Changed

The main `/chat` endpoint now uses the **adaptive LangGraph workflow** instead of the legacy `chat_service.send_message()`.

## Before vs After

### BEFORE (Buggy)
```python
# Legacy code - REMOVED
print("🚀 Using conversational chat service for query processing")
ai_message = None
async for generated in chat_service.send_message(session_id, question, user_id):
    ai_message = generated
answer = ai_message.content
```

**Problem:** This called `EnhancedConversationMemory.resolve_context()` which added incorrect context like "for Operations roles" when user asked about HR.

### AFTER (Fixed)
```python
# New adaptive workflow - IMPLEMENTED
print("🚀 Using ADAPTIVE LANGGRAPH WORKFLOW")
print("🎯 Invoking adaptive LangGraph workflow...")

# Get conversation history
session_messages = chat_history_store.get_session_messages(user_id, session_id)
history_strings = [msg.message for msg in session_messages if msg.message_type == "human"]

# Invoke LangGraph workflow
workflow_result = run_adaptive_workflow(
    original_query=question,
    conversation_history=history_strings,
    session_id=session_id
)

# Extract response
answer = workflow_result.get("final_response", "Error message")

# Save to history
chat_history_store.add_message(user_id, session_id, answer, "ai")
```

**Solution:** The triage agent in the workflow handles intent classification WITHOUT adding fake context.

## Testing

### 1. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Run Test Script
```bash
python test_adaptive_workflow_migration.py
```

### 3. Manual Test
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "how many companies came for #hr", "user_id": "test", "session_id": null}'
```

## Expected Logs

### ✅ Success (New Workflow)
```
🤖 Processing query: how many companies came for #hr
🚀 Using ADAPTIVE LANGGRAPH WORKFLOW
🎯 Invoking adaptive LangGraph workflow...
======================================================================
🚀 Agent Pipeline Started
🎯 Stage 0: Classifying intent...
✅ Adaptive workflow completed successfully
```

### ❌ Failure (Old Workflow - Should NOT appear)
```
🚀 Using conversational chat service for query processing
🔄 Resolved contextual query: 'how many companies came for #hr' → 'how many companies came for #hr for Operations roles'
```

## Files Modified

1. **`app/main.py`** (Line 19, 231-310)
   - Added `run_adaptive_workflow` import
   - Replaced `chat_service.send_message()` with workflow invocation

## Rollback (Emergency Only)

If issues occur, you can temporarily revert:

```python
# Comment out lines 280-310 in app/main.py (adaptive workflow section)
# Uncomment the old chat_service.send_message() code
```

**Note:** This brings back the buggy context resolver. Fix root cause instead!

## Architecture

The new workflow follows this path:

```
User Query
    ↓
Triage Agent (classify intent, NO context resolution)
    ↓
Planning Agent (create execution plan)
    ↓
Tool Input Agent (prepare parameters)
    ↓
Retrieval Agent (SQL or Vector)
    ↓
Reflection Agent (validate results)
    ↓
Synthesis Agent (generate response)
    ↓
Final Response
```

## Key Benefits

1. ✅ **No buggy context resolution** - Triage agent doesn't add fake context
2. ✅ **Intelligent routing** - Planning agent validates SQL schema first
3. ✅ **Adaptive fallbacks** - Reflection agent retries with adjusted params
4. ✅ **Proper history** - Both human and AI messages saved correctly
5. ✅ **Clear logging** - Full pipeline visibility for debugging

## Troubleshooting

### Issue: Server won't start
```bash
# Check for syntax errors
python -c "import app.main"
```

### Issue: Import errors
```bash
# Verify agent.py exports run_adaptive_workflow
python -c "from app.agent import run_adaptive_workflow; print('OK')"
```

### Issue: Still seeing old logs
1. Restart the server (hard restart, not just reload)
2. Clear any cached .pyc files: `find . -name "*.pyc" -delete`
3. Check that you're hitting the correct endpoint

## Related Files

- `ADAPTIVE_WORKFLOW_MIGRATION.md` - Full documentation
- `test_adaptive_workflow_migration.py` - Test script
- `app/main.py` - Modified endpoint
- `app/agent.py` - LangGraph workflow definition

---

**Quick Test Command:**
```bash
python test_adaptive_workflow_migration.py && echo "✅ Migration successful!"
```
