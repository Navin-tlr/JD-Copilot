from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
import json
from typing import Dict, List
from .chat_service import chat_service, ChatMessage, ChatSession
from .agents.orchestrator import agent_orchestrator

router = APIRouter(prefix="/chat", tags=["chat"])

# Simple connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except:
                self.disconnect(session_id)

manager = ConnectionManager()

@router.post("/sessions")
async def create_session(data: dict = Body(...)):
    """Create a new chat session"""
    try:
        user_id = data.get("user_id", "anonymous")
        session_id = await chat_service.create_session(user_id)
        return {"session_id": session_id, "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get all sessions for a user"""
    try:
        sessions = await chat_service.get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a session"""
    try:
        messages = await chat_service.get_session_messages(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        success = await chat_service.delete_session(session_id)
        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_message(data: dict = Body(...)):
    """Send a message via REST API"""
    try:
        session_id = data.get("session_id")
        content = data.get("content")
        user_id = data.get("user_id", "anonymous")
        
        if not session_id or not content:
            raise HTTPException(status_code=400, detail="session_id and content are required")
        
        async def generate_response():
            async for ai_message in chat_service.send_message(session_id, content, user_id):
                message_data = {
                    'type': 'ai_message_chunk',
                    'content': ai_message.content,
                    'message_id': ai_message.id,
                    'timestamp': ai_message.timestamp.isoformat()
                }
                yield f"data: {json.dumps(message_data)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent")
async def send_message_agent(data: dict = Body(...)):
    """
    Send a message via Agent Pipeline (NEW).
    This uses the multi-agent system with intent classification, planning, etc.
    """
    try:
        session_id = data.get("session_id", "default-session")
        content = data.get("content")
        user_id = data.get("user_id", "student-123")
        
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        # Process through agent pipeline
        result = await agent_orchestrator.process_query(
            query=content,
            session_id=session_id,
            user_id=user_id
        )
        
        return {
            "response": result['response'],
            "metadata": result.get('metadata', {}),
            "session_id": session_id
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def include_chat_router(app):
    app.include_router(router)
