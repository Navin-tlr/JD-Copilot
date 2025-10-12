# Chat History Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐              ┌──────────────────────┐      │
│  │   RAGMode.tsx  │──────────────│  ChatHistory.tsx     │      │
│  │                │              │  (Sidebar Component)  │      │
│  │  • Messages    │              │                       │      │
│  │  • SessionId   │  triggers    │  • Session List      │      │
│  │  • UserId      │  ─────────>  │  • Time Formatting   │      │
│  │                │              │  • Delete Button      │      │
│  └────────┬───────┘              │  • New Chat Button   │      │
│           │                      └──────────────────────┘      │
│           │ POST /chat                      │                   │
│           │ GET  /sessions/{userId}         │                   │
│           │ GET  /sessions/{sid}/messages   │                   │
│           │ DELETE /sessions/{sid}          │                   │
└───────────┼─────────────────────────────────┼───────────────────┘
            │                                 │
            ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    main.py (Endpoints)                   │   │
│  │                                                           │   │
│  │  POST   /chat                  ─────┐                    │   │
│  │  GET    /sessions/{userId}          │                    │   │
│  │  GET    /sessions/{sid}/messages    ├──> ChatService    │   │
│  │  DELETE /sessions/{sid}             │                    │   │
│  └─────────────────────────────────────┘                    │   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ChatService (chat_service.py)               │   │
│  │                                                           │   │
│  │  ┌───────────────────────────────────────────────┐      │   │
│  │  │         Session Management                     │      │   │
│  │  │                                                │      │   │
│  │  │  • create_session()                           │      │   │
│  │  │  • ensure_session()                           │      │   │
│  │  │  • get_user_sessions()                        │      │   │
│  │  │  • delete_session()                           │      │   │
│  │  │  • _generate_session_name()                   │      │   │
│  │  │                                                │      │   │
│  │  │  Limits:                                      │      │   │
│  │  │  ├─ Max Sessions: 10                          │      │   │
│  │  │  └─ Max Messages/Session: 200                 │      │   │
│  │  └───────────────────────────────────────────────┘      │   │
│  │                                                           │   │
│  │  ┌───────────────────────────────────────────────┐      │   │
│  │  │      In-Memory Storage (Dictionaries)          │      │   │
│  │  │                                                │      │   │
│  │  │  sessions: Dict[str, ChatSession]             │      │   │
│  │  │  memories: Dict[str, EnhancedMemory]          │      │   │
│  │  │                                                │      │   │
│  │  │  Eviction: LRU (oldest by last_activity)      │      │   │
│  │  └───────────────────────────────────────────────┘      │   │
│  │                                                           │   │
│  │  ┌───────────────────────────────────────────────┐      │   │
│  │  │           Message Flow                         │      │   │
│  │  │                                                │      │   │
│  │  │  send_message()                               │      │   │
│  │  │    ├─> Auto-generate name (first msg)         │      │   │
│  │  │    ├─> Context resolution                     │      │   │
│  │  │    ├─> Call route_query() with context        │      │   │
│  │  │    ├─> Store in memory                        │      │   │
│  │  │    └─> Update last_activity                   │      │   │
│  │  └───────────────────────────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │     EnhancedConversationMemory (enhanced_chat_memory)    │   │
│  │                                                           │   │
│  │  • Full conversation history                             │   │
│  │  • Context resolution (pronouns, follow-ups)             │   │
│  │  • Specialization tracking                               │   │
│  │  • Entity extraction                                     │   │
│  │  • Query type detection                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: New Message

```
User types message
       │
       ▼
┌──────────────────┐
│  RAGMode.tsx     │  POST /chat { question, session_id, user_id }
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  main.py: chat_endpoint()                                │
│    ├─> Calls chat_service.ensure_session()              │
│    └─> Passes to chat_service.send_message()            │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  ChatService.send_message()                              │
│    ├─> Check if first message                            │
│    │   └─> Generate session name: "do you have..."       │
│    │                                                      │
│    ├─> Enforce message limit (trim if > 200)             │
│    │                                                      │
│    ├─> Check if contextual query                         │
│    │   └─> Resolve: "any data?" → "data about Honasa"    │
│    │                                                      │
│    ├─> Build enhanced context                            │
│    │   ├─> Full conversation history                     │
│    │   ├─> Conversation summary                          │
│    │   ├─> Recent companies/entities                     │
│    │   └─> Key findings                                  │
│    │                                                      │
│    ├─> Call route_query(question, context)               │
│    │   └─> LLM generates response with context           │
│    │                                                      │
│    ├─> Store user & assistant messages in memory         │
│    │                                                      │
│    └─> Update session.last_activity                      │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Return response │  { answer, snippets, session_id }
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAGMode.tsx     │  Display formatted Markdown response
└──────────────────┘
```

## Session Lifecycle

```
1. CREATE
   ┌────────────────────────────────────────┐
   │ User sends first message               │
   │                                        │
   │ Backend:                               │
   │  ├─> Generate UUID                     │
   │  ├─> Create ChatSession object         │
   │  ├─> Extract first 40 chars            │
   │  └─> Set name: "do you have any..."    │
   └────────────────────────────────────────┘

2. USE
   ┌────────────────────────────────────────┐
   │ User continues conversation            │
   │                                        │
   │ Each message:                          │
   │  ├─> Add to memory (max 200)          │
   │  ├─> Update last_activity              │
   │  └─> Use context from history          │
   └────────────────────────────────────────┘

3. SWITCH
   ┌────────────────────────────────────────┐
   │ User selects different session         │
   │                                        │
   │ Frontend:                              │
   │  ├─> GET /sessions/{sid}/messages      │
   │  ├─> Load messages into state          │
   │  └─> Continue with full context        │
   └────────────────────────────────────────┘

4. DELETE
   ┌────────────────────────────────────────┐
   │ User clicks delete button              │
   │                                        │
   │ Backend:                               │
   │  ├─> Remove from sessions dict         │
   │  ├─> Clear memory.messages             │
   │  └─> Remove from memories dict         │
   └────────────────────────────────────────┘

5. EVICT (Auto)
   ┌────────────────────────────────────────┐
   │ Sessions reach limit (10)              │
   │                                        │
   │ Backend:                               │
   │  ├─> Find oldest by last_activity      │
   │  ├─> Call delete_session()             │
   │  └─> Create new session                │
   └────────────────────────────────────────┘
```

## Memory Structure

```
ChatService
   │
   ├── sessions: Dict[session_id, ChatSession]
   │    │
   │    └── ChatSession
   │         ├── id: "uuid-123"
   │         ├── user_id: "student-123"
   │         ├── name: "do you have any advice for me..."
   │         ├── created_at: datetime
   │         ├── last_activity: datetime
   │         └── metadata: {}
   │
   └── memories: Dict[session_id, EnhancedConversationMemory]
        │
        └── EnhancedConversationMemory
             ├── messages: List[ChatMessage]
             │    │
             │    └── ChatMessage
             │         ├── role: "user" | "assistant"
             │         ├── content: "message text"
             │         ├── timestamp: datetime
             │         ├── query_type: "advice_query"
             │         ├── specialization: "Finance"
             │         └── entities_mentioned: ["Honasa"]
             │
             ├── current_context: Dict
             │    ├── last_specialization
             │    ├── last_companies_mentioned
             │    ├── last_entities
             │    └── last_numbers_mentioned
             │
             └── max_messages: 200
```

## Context Building

```
_build_enhanced_context()
   │
   ├── Full Conversation History
   │    └── [{ role, content, timestamp }, ...]
   │
   ├── Conversation Summary
   │    └── "Discussing Finance roles at Honasa..."
   │
   ├── Current Topic
   │    └── "Finance"
   │
   ├── Recent Companies
   │    └── ["Honasa", "Masters Union", "Mill Story"]
   │
   ├── Recent Entities
   │    └── ["Finance", "Marketing", "Sales"]
   │
   ├── Key Findings
   │    ├── "Total companies: 18"
   │    ├── "Average min salary: ₹8.5 LPA"
   │    └── "Recently discussed: Honasa, Target"
   │
   └── Reasoning Chain
        ├── "Step 1: User asked about Honasa → Found 3 roles"
        └── "Step 2: User requested data → Provided details"
```

## Session Naming Examples

```
Input Message                            → Generated Name
────────────────────────────────────────────────────────────
"do you have any advice for me, for honasa"
                                         → "do you have any advice for me..."

"how many companies came for finance?"
                                         → "how many companies came for finance?"

"tell me about masters union"
                                         → "tell me about masters union"

"hi"
                                         → "Chat Oct 12"  (too short fallback)

"What are the top 5 companies that recruited for Finance roles and what are their salary ranges?"
                                         → "What are the top 5 companies that..."
```

## API Response Formats

### GET /sessions/{user_id}
```json
{
  "sessions": [
    {
      "id": "abc-123",
      "name": "do you have any advice for me...",
      "created_at": "2025-10-12T10:30:00",
      "last_activity": "2025-10-12T10:35:00",
      "message_count": 8
    }
  ]
}
```

### GET /sessions/{session_id}/messages
```json
{
  "messages": [
    {
      "id": "msg-1",
      "content": "do you have any advice for me, for honasa",
      "sender": "user",
      "timestamp": "2025-10-12T10:30:00"
    },
    {
      "id": "msg-2",
      "content": "### Zeroing In on Honasa's Opportunity...",
      "sender": "assistant",
      "timestamp": "2025-10-12T10:30:15"
    }
  ]
}
```

## UI States

```
1. Empty State (No Sessions)
   ┌──────────────────────────┐
   │     Chat History         │
   │  ┌────────────────────┐  │
   │  │  [New Chat]        │  │
   │  └────────────────────┘  │
   │                          │
   │    📱 No chat history    │
   │                          │
   │  0 of 10 chats stored    │
   └──────────────────────────┘

2. Active Sessions
   ┌──────────────────────────┐
   │     Chat History         │
   │  ┌────────────────────┐  │
   │  │  [New Chat]        │  │
   │  └────────────────────┘  │
   │                          │
   │  ┌────────────────────┐  │
   │  │ do you have any... │  │
   │  │ 🕐 2m ago · 8 msgs │  │  ← Current session
   │  └────────────────────┘  │  (highlighted)
   │                          │
   │  ┌────────────────────┐  │
   │  │ how many compa...  │  │
   │  │ 🕐 5m ago · 4 msgs │  │
   │  └────────────────────┘  │
   │                          │
   │  3 of 10 chats stored    │
   └──────────────────────────┘

3. Hover State
   ┌──────────────────────────┐
   │  ┌────────────────────┐  │
   │  │ do you have any... │🗑│ ← Delete appears
   │  │ 🕐 2m ago · 8 msgs │  │
   │  └────────────────────┘  │
   └──────────────────────────┘
```

## Performance Optimizations

- **Lazy Loading**: Messages fetched only when session selected
- **CSS Animations**: Hardware-accelerated transforms for slide-in
- **Memo**: Session list items memoized to prevent re-renders
- **Debounce**: Time formatting cached per session
- **Eviction**: Automatic cleanup prevents memory bloat
- **Trim**: Old messages removed to stay under limit

## Security

- **User Isolation**: Sessions filtered by user_id
- **UUID IDs**: Non-sequential, hard to guess
- **No PII**: Session names are message previews only
- **Confirmation**: Delete requires user confirmation
- **CORS**: Backend validates origins
