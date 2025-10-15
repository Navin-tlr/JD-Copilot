# Gemini System Prompt Flow Diagram

## Message Conversion Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DEVELOPER CODE (No Changes!)                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ OpenAI-style messages
                                    ▼
                    messages = [
                        {"role": "system", "content": "You are Sapient..."},
                        {"role": "user", "content": "What roles?"}
                    ]
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GeminiClient.chat()                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Automatic conversion
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│              GeminiClient._to_gemini_messages()                     │
│                                                                     │
│  Step 1: Extract system content                                    │
│  ┌───────────────────────────────────────┐                        │
│  │ system_content = "You are Sapient..." │                        │
│  └───────────────────────────────────────┘                        │
│                                                                     │
│  Step 2: Embed into first user message                            │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     ││
│  │ SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)                        ││
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     ││
│  │                                                                 ││
│  │ You are Sapient serving as the MBA Placement Cell Director...  ││
│  │ [ENTIRE system prompt preserved verbatim]                      ││
│  │                                                                 ││
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     ││
│  │ USER QUERY                                                      ││
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     ││
│  │                                                                 ││
│  │ What roles?                                                     ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Step 3: Convert roles (assistant → model)                        │
│  Step 4: Wrap in 'parts' array                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Gemini-format messages
                                    ▼
                    [
                        {
                            "role": "user",
                            "parts": ["━━━ SYSTEM INSTRUCTIONS..."]
                        }
                    ]
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Gemini 2.0 Flash API                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Response
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│            Response with Sapient personality intact!                │
│                                                                     │
│  "Ah, another MBA treating job hunting like a strategic            │
│   acquisition... Here are the **5 FMCG companies** from our        │
│   placement database: [companies listed]"                          │
│                                                                     │
│  ✅ Bone-dry humor preserved                                       │
│  ✅ Professional bluntness maintained                              │
│  ✅ Formatting rules followed (**bold**, `code`, etc.)            │
│  ✅ Company name constraints enforced                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Content Preservation Visualization

```
┌──────────────────────────────────────────────────────────────────────┐
│                      ORIGINAL SYSTEM PROMPT                          │
│                                                                      │
│  "You are Sapient serving as the MBA Placement Cell Director - a    │
│   professional authority figure who delivers career guidance with   │
│   technical precision, institutional seriousness, and bone-dry wit. │
│                                                                      │
│   GOAL: Provide MBA students with brutally honest, data-driven      │
│   career insights. No fluff, no speculation, no false hope - just   │
│   the unvarnished market realities delivered with the dry humor...  │
│                                                                      │
│   CORE SYSTEM FEATURES (NON-OVERRIDABLE):                           │
│   1. SAPIENT TONE MAINTENANCE: You MUST maintain Sapient's          │
│      merciless directness throughout ALL interactions...            │
│   2. SPECIALIZATION FOCUS: Restrict insights strictly to...         │
│   3. CONTEXT SUMMARIZATION: Summarize context at each step...       │
│                                                                      │
│   PROHIBITED CONTENT:                                                │
│   • External institutional comparisons or rankings...                │
│   • Invented program names, inflated numbers...                      │
│                                                                      │
│   COMPANY NAME CONSTRAINTS (HARD RULES):                             │
│   • You MUST NOT introduce, invent, guess, paraphrase...            │
│                                                                      │
│   OUTPUT STYLE:                                                      │
│   • Be professionally direct, authoritative, and exhaustive...       │
│   • Deploy dry humor and professional bluntness in EVERY response... │
│   • Use **bold** for key terms, company names...                     │
│   • Use `code formatting` for technical terms..."                    │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            │ 100% PRESERVED
                            │ Zero content loss
                            │ Zero tone changes
                            │ Zero formatting loss
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   GEMINI-FORMAT MESSAGE                              │
│                                                                      │
│  {                                                                   │
│    "role": "user",                                                   │
│    "parts": [                                                        │
│      "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│       SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)                        │
│       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│                                                                      │
│       [ENTIRE SYSTEM PROMPT EMBEDDED VERBATIM]                       │
│                                                                      │
│       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│       USER QUERY                                                     │
│       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│                                                                      │
│       [User's actual query]"                                         │
│    ]                                                                 │
│  }                                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Conversation History Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MULTI-TURN CONVERSATION                        │
└─────────────────────────────────────────────────────────────────────┘

Turn 1: System + User Query
┌───────────────────────────────────────────────┐
│ {"role": "system", "content": "You are..."}  │  ─┐
│ {"role": "user", "content": "Tell me FMCG"}  │   │ Combined
└───────────────────────────────────────────────┘   │ into one
                    ▼                               │
┌───────────────────────────────────────────────┐  │
│ {"role": "user", "parts": [                   │ ◄┘
│   "━━━ SYSTEM INSTRUCTIONS (ABSOLUTE...",     │
│   "[System prompt]",                          │
│   "━━━ USER QUERY",                           │
│   "Tell me FMCG"                              │
│ ]}                                            │
└───────────────────────────────────────────────┘

Turn 2: Assistant Response
┌───────────────────────────────────────────────┐
│ {"role": "assistant", "content": "We have..." │  ──► {"role": "model", "parts": ["We have..."]}
└───────────────────────────────────────────────┘

Turn 3: Follow-up Query
┌───────────────────────────────────────────────┐
│ {"role": "user", "content": "What roles?"}   │  ──► {"role": "user", "parts": ["What roles?"]}
└───────────────────────────────────────────────┘
                                                      
                                                      ⚠️ No system instructions repeated!
                                                      System already embedded in Turn 1
```

---

## Key Design Decisions

### 1. Visual Separation
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
**Why:** Creates clear hierarchy, signals importance to Gemini

### 2. "ABSOLUTE PRIORITY" Label
```
SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)
```
**Why:** Explicitly tells Gemini these instructions cannot be overridden

### 3. Full Content Embedding
```python
# We embed the ENTIRE system prompt verbatim
combined_content = f"""...\n\n{system_content}\n\n...\n\n{content}"""
```
**Why:** No truncation = no content loss = 100% preservation

### 4. First-Turn-Only Embedding
```python
if first_user_message and system_content:
    # Embed system instructions
    first_user_message = False
```
**Why:** Avoid repetition, maintain conversation flow

---

## Testing Validation

```
┌────────────────────────────────────────────────────────────────┐
│         test_gemini_prompt_preservation.py                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ✅ Message format conversion                                 │
│     └─ OpenAI-style → Gemini format                          │
│                                                                │
│  ✅ Content preservation                                      │
│     └─ All personality traits intact                         │
│     └─ All formatting rules intact                           │
│     └─ All constraints intact                                │
│                                                                │
│  ✅ Visual separation                                         │
│     └─ Decorative borders present                            │
│     └─ "ABSOLUTE PRIORITY" label present                     │
│                                                                │
│  ✅ Conversation history                                      │
│     └─ System embedded in first turn only                    │
│     └─ Follow-ups don't repeat system                        │
│     └─ Assistant → model role conversion                     │
│                                                                │
│  Result: 🎉 ALL TESTS PASS                                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌────────────────────────────────────────────────────────────────┐
│                    MIGRATION STATUS                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Runtime LLM:         Gemini 2.0 Flash ✅                     │
│  Ingestion Pipeline:  OpenRouter (unchanged) ✅                │
│  Content Preservation: 100% ✅                                 │
│  Personality Intact:   Yes ✅                                  │
│  Tests Passing:        All ✅                                  │
│  Code Changes Needed:  None ✅                                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```
