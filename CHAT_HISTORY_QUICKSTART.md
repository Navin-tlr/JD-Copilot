# Quick Start: Testing Chat History

## 1. Start Backend
```bash
cd /Users/navinsivakumar/Desktop/JD-Copilot
uvicorn app.main:app --reload --port 8000
```

## 2. Start Frontend
```bash
cd /Users/navinsivakumar/Desktop/JD-Copilot/spark-home-2
npm run dev
```

## 3. Open Browser
```
http://localhost:5173/rag
```

## 4. Test Flow

### A. Create First Chat
1. Type: "do you have any advice for me, for honasa"
2. Wait for response
3. Notice session name generated automatically

### B. Add More Messages
4. Type: "any specific data you have?"
5. Verify context is preserved (should reference Honasa)

### C. Open History
6. Click purple History button (top-right corner)
7. Sidebar slides in from right
8. See your session with auto-generated name

### D. Create New Chat
9. Click "New Chat" button in sidebar
10. Type: "how many companies for finance?"
11. New session created

### E. Switch Between Sessions
12. Click History button again
13. See both sessions listed
14. Click first session (Honasa)
15. Messages restored, can continue conversation

### F. Delete Session
16. Hover over any session
17. Delete icon appears
18. Click and confirm
19. Session removed

## 5. Verify Backend

### Check Active Sessions
```bash
curl http://localhost:8000/sessions/student-123 | jq
```

### View Session Messages
```bash
curl http://localhost:8000/sessions/{SESSION_ID}/messages | jq
```

### Delete Session
```bash
curl -X DELETE http://localhost:8000/sessions/{SESSION_ID}
```

## 6. Check Logs

Backend logs should show:
```
📝 Auto-generated session name: 'do you have any advice for me...'
🔄 Resolved contextual query: 'any specific data you have?' → '...'
```

## Expected Behavior

✅ Session names auto-generated from first message
✅ Up to 10 sessions shown in history
✅ Time shows as "2m ago", "3h ago", etc.
✅ Message count accurate per session
✅ Switching sessions loads full conversation
✅ Follow-up questions use context from chat history
✅ Oldest session evicted when creating 11th
✅ Delete removes session immediately

## Troubleshooting

### History button not visible
- Check Z-index conflicts
- Verify button rendered (inspect element)

### Sessions not loading
- Check backend running on port 8000
- Verify API endpoints: `curl http://localhost:8000/sessions/student-123`

### Context not preserved
- Check session_id passed in API calls
- Verify memory not cleared between messages

### Sidebar not sliding
- Check tailwind animation compiled: `animate-slide-in-right`
- Verify tailwind.config.ts includes keyframes

## Environment Variables (Optional)

```bash
export CHAT_SESSION_MEMORY_LIMIT=10      # Max concurrent sessions
export CHAT_SESSION_MESSAGE_LIMIT=200    # Max messages per session
```

## Demo Script

```bash
# Terminal 1: Start backend
cd /Users/navinsivakumar/Desktop/JD-Copilot
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd /Users/navinsivakumar/Desktop/JD-Copilot/spark-home-2
npm run dev

# Terminal 3: Test API
curl http://localhost:8000/sessions/student-123
```

**Ready to test! 🚀**
