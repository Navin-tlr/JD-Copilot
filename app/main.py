from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, List
import re
import sqlite3
import os
import json
from datetime import datetime

import certifi
import ssl
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer
from .agent import route_query, LAST_ROUTE_TYPE, get_last_timings, _is_no_data_result, run_adaptive_workflow  # Import router and guardrail utils + adaptive workflow
from .chat_memory import ChatMemory
from .chat_history_store import chat_history_store
from .enhanced_chat_memory import enhanced_memory_manager
from .sql_tool import run_sql_query
from .chat_api import include_chat_router
from .chat_service import chat_service
from .workflow_api import include_workflow_router
from .api.industry_hierarchy import router as industry_hierarchy_router
from .orchestrator import get_orchestrator, OrchestratorResponse

# Ensure local .env is loaded early so os.getenv and Settings both see values
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Non-fatal: Settings will still read env_file; this just helps os.getenv users
    pass

# Force Python to use certifi's CA bundle
# This is a critical fix for environments where the default SSL certificates are outdated
# or where system-level configs interfere with Python's SSL verification.
try:
    cert_path = certifi.where()
    os.environ["SSL_CERT_FILE"] = cert_path
    os.environ["REQUESTS_CA_BUNDLE"] = cert_path
    print(f"✅ SSL Context Forced: Using certifi bundle at {cert_path}")
except Exception as e:
    print(f"⚠️  Could not force SSL context: {e}")

app = FastAPI(title="JD-Copilot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat memory
chat_memory = ChatMemory()

# Include chat router
include_chat_router(app)

# Include workflow router for durable workflow features
include_workflow_router(app)

# Include industry hierarchy router for > trigger UI
app.include_router(industry_hierarchy_router)

# ==========================================
# NEW ORCHESTRATOR ENDPOINT
# ==========================================

class OrchestratorRequest(BaseModel):
    """Request for new orchestrator endpoint."""
    query: str
    session_id: str = "default"
    user_id: Optional[str] = "anonymous"
    user_context: Optional[Dict[str, Any]] = None

class OrchestratorResponseModel(BaseModel):
    """Response from orchestrator endpoint."""
    answer: str
    intent: str
    route: str
    entities: Dict[str, List[str]]
    confidence: float
    sources: List[Dict[str, Any]]
    used_memory: bool
    session_id: str

@app.post("/orchestrator/query", response_model=OrchestratorResponseModel)
async def orchestrator_query_endpoint(request: OrchestratorRequest):
    """
    NEW Orchestrator Endpoint - Clean multi-agent architecture.
    
    Flow:
    1. Intent Router classifies and routes
    2. Memory Agent provides context (if needed)
    3. SQL/Vector/Hybrid retrieval
    4. Synthesizer generates final answer
    5. Memory stores turn
    
    No fallbacks, no legacy RAG, pure A2A protocol.
    """
    try:
        print(f"\n{'='*80}")
        print(f"🎬 ORCHESTRATOR ENDPOINT: New query received")
        print(f"   User: {request.user_id}")
        print(f"   Session: {request.session_id}")
        print(f"   Query: {request.query}")
        print(f"{'='*80}\n")
        
        # Get orchestrator instance
        orchestrator = get_orchestrator()
        
        # Process query through complete agent pipeline
        response = await orchestrator.process_query(
            user_query=request.query,
            session_id=request.session_id,
            user_context=request.user_context
        )
        
        print(f"\n{'='*80}")
        print(f"✅ ORCHESTRATOR ENDPOINT: Query completed")
        print(f"   Intent: {response.intent}")
        print(f"   Route: {response.route}")
        print(f"   Memory Used: {response.used_memory}")
        print(f"   Answer Length: {len(response.answer)} chars")
        print(f"{'='*80}\n")
        
        return OrchestratorResponseModel(
            answer=response.answer,
            intent=response.intent,
            route=response.route,
            entities=response.entities,
            confidence=response.confidence,
            sources=response.sources,
            used_memory=response.used_memory,
            session_id=response.session_id
        )
        
    except Exception as e:
        print(f"❌ ORCHESTRATOR ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Orchestrator failed: {str(e)}"
        )

# ==========================================
# END NEW ORCHESTRATOR ENDPOINT
# ==========================================

# Simple LLM router system (no more complex agents)
# The route_query function handles all query processing

def get_jd_agent():
    """This function is no longer needed as we use the simple router."""
    return None


def _sync_history_snapshot(user_id: str, session_id: str) -> None:
    """Persist the current conversation transcript for the session."""
    try:
        messages = chat_memory.get_messages(session_id)
        chat_history_store.sync_session(user_id, session_id, messages)
    except Exception as exc:
        print(f"⚠️ Failed to sync chat history for session {session_id}: {exc}")

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"
    user_id: Optional[str] = "anonymous"
    user_context: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    answer: str
    snippets: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    error: Optional[bool] = False  # frontend error handling
    needs_vector_approval: bool = False  # suggest unstructured follow-up
    vector_reason: Optional[str] = None
    vector_used: bool = False
    performance: Optional[Dict[str, float]] = None  # timing breakdown
    deep_dive_mandatory: bool = False  # reserved if we ever force deep dive
    deep_dive_offered: bool = False    # backend offered deep dive (consent path)
    deep_dive_consent_needed: bool = False  # user must reply yes / deep-dive

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []

class StructuredRequest(BaseModel):
    question: str

class StructuredResponse(BaseModel):
    answer: str

@app.post("/chat/vector", response_model=ChatResponse)
async def vector_chat_endpoint(request: QueryRequest):
    """Force vector (unstructured) retrieval path after human approval."""
    try:
        user_id = (request.user_id or "anonymous").strip() or "anonymous"
        session_id = request.session_id
        chat_history_store.ensure_session(user_id, session_id)

        question = request.question.strip()
        chat_memory.add_message(session_id, "user", question)
        _sync_history_snapshot(user_id, session_id)
        snippets = retrieve_snippets(question, top_k=75, filters={})
        if snippets:
            answer = synthesize_answer(question, snippets, {}) or "No additional context found."
        else:
            answer = "No document context available for deeper search."\

        chat_memory.add_message(session_id, "assistant", answer)
        _sync_history_snapshot(user_id, session_id)
        return ChatResponse(
            answer=answer,
            snippets=snippets or [],
            citations=[],
            needs_vector_approval=False,
            vector_reason=None,
            vector_used=True
        )
    except Exception as e:
        return ChatResponse(answer=f"Vector retrieval failed: {e}", error=True, snippets=[], citations=[], vector_used=True)

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: ChatRequest = Body(...)):
    """
    This endpoint receives a user query and uses the AI agent to generate a response.
    """
    user_id = (request.user_id or "anonymous").strip() or "anonymous"
    session_id = await chat_service.ensure_session(request.session_id, user_id)
    print(f"Received query for session '{session_id}': {request.query}")
    chat_history_store.ensure_session(user_id, session_id)
    
    try:
        # Add user message to chat memory
        chat_memory.add_message(session_id, "user", request.query)
        _sync_history_snapshot(user_id, session_id)
        
        # Use the simple router to process the query
        snippets: List[Dict[str, Any]] = []

        print("🚀 Using conversational chat service for query processing")
        try:
            ai_message = None
            async for generated in chat_service.send_message(session_id, request.query, user_id):
                ai_message = generated

            if not ai_message:
                raise RuntimeError("Chat service returned no response")

            answer = ai_message.content
            session_id = ai_message.session_id  # Update in case chat service reassigned
            print(f"🔍 Final answer: {answer}")
        except Exception as router_error:
            print(f"❌ Chat service error: {router_error}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error while processing your query: {str(router_error)}",
                snippets=[],
                citations=[],
                error=True
            )

        # Attempt to retrieve supporting snippets for the frontend view
        try:
            temp_snippets = retrieve_snippets(request.query, top_k=50, filters={})
            if temp_snippets:
                snippets = temp_snippets
        except Exception as e:
            print(f"Warning: Could not retrieve snippets: {e}")
        
        print(f"✅ Query processed successfully. Answer length: {len(answer)} chars")
        
    # Heuristic: if answer suggests no data or is very short, request vector approval
        lower_ans = answer.lower().strip() if answer else ""
        needs_vector = False
        reason = None
        # Always allow deep dive if the last route was STRUCTURED (human-in-loop optional)
        if LAST_ROUTE_TYPE == "STRUCTURED":
            needs_vector = True
            reason = "Structured answer generated. Deep-Dive review required for full context."
            deep_dive_mandatory = True
        else:
            deep_dive_mandatory = False
            if (
                lower_ans in {"i couldn't find relevant information.", "0 companies came", "no companies came", "i couldn't process your query. please try again."} or
                (len(answer) < 40 and ("no companies" in lower_ans or "couldn't" in lower_ans))
            ):
                needs_vector = True
                reason = "Structured data may be incomplete; deeper document search recommended."

        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=[],
            needs_vector_approval=needs_vector,
            vector_reason=reason,
            vector_used=False,
            performance=get_last_timings(),
            deep_dive_mandatory=deep_dive_mandatory
        )
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a structured error response
        # This ensures the React app always gets valid JSON
        return ChatResponse(
            answer=f"Processing error: {str(e)}. Debug input and retry.",
            snippets=[],
            citations=[],
            error=True  # Add error flag for frontend handling
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: QueryRequest):
    """
    NEW ORCHESTRATOR-POWERED CHAT ENDPOINT
    
    Uses clean multi-agent architecture:
    1. Intent Router → classifies query
    2. Memory Agent → provides context
    3. SQL/Vector/Hybrid → retrieval
    4. Synthesizer → generates answer
    
    Replaces old adaptive LangGraph workflow with A2A protocol.
    """
    question = request.question.strip()
    user_id = (request.user_id or "anonymous").strip() or "anonymous"
    session_id = request.session_id

    try:
        session_id = await chat_service.ensure_session(session_id, user_id)
        chat_history_store.ensure_session(user_id, session_id)
        
        print(f"\n{'='*80}")
        print(f"🎬 NEW ORCHESTRATOR: Processing query")
        print(f"   User: {user_id}")
        print(f"   Session: {session_id}")
        print(f"   Query: {question}")
        print(f"{'='*80}\n")
        
        # Use the new orchestrator instead of old adaptive workflow
        orchestrator = get_orchestrator()
        result: OrchestratorResponse = await orchestrator.process_query(
            user_query=question,
            session_id=session_id,
            user_context=request.user_context or {}
        )
        
        print(f"\n🎯 Orchestrator Result:")
        print(f"   Intent: {result.intent}")
        print(f"   Route: {result.route}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Answer length: {len(result.answer)} chars\n")
        
        # Store conversation turn in chat memory
        chat_memory.add_message(session_id, "user", question)
        chat_memory.add_message(session_id, "assistant", result.answer)
        
        # Sync history to persistent storage
        _sync_history_snapshot(user_id, session_id)
        
        # Convert orchestrator response to ChatResponse format
        snippets = []
        for source in result.sources:
            snippets.append({
                "content": source.get("content", ""),
                "metadata": source.get("metadata", {})
            })
        
        return ChatResponse(
            answer=result.answer,
            snippets=snippets[:5],  # Limit to 5 for UI
            citations=[],
            needs_vector_approval=False,
            vector_reason=None,
            vector_used=result.route in ["VECTOR", "HYBRID"],
            performance={"total_ms": 0},  # Orchestrator doesn't track detailed timing yet
            deep_dive_mandatory=False,
            deep_dive_offered=False,
            deep_dive_consent_needed=False
        )
        
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            _sync_history_snapshot(user_id, session_id)
        except Exception:
            pass
        
        return ChatResponse(
            answer=f"I encountered an error processing your query: {str(e)}",
            snippets=[],
            citations=[],
            error=True
        )

# OLD ADAPTIVE WORKFLOW CODE REMOVED - keeping as comment for reference
# The old adaptive LangGraph workflow has been replaced with the new orchestrator
# If you need to rollback, check git history for the original implementation

def _old_adaptive_workflow_placeholder():
    """
    This function is a placeholder marking where the old adaptive workflow code was removed.
    
    The old workflow included:
    - Deep-dive consent handling
    - Simple query bypass
    - LangGraph triage → planning → tool_input → retrieve → reflect/synthesize
    - Complex timeout handling
    - Manual context management
    
    All of this has been replaced by the clean orchestrator architecture in app/orchestrator.py
    """
    pass

# Restore placeholder for deep-dive consent check (may be needed for legacy features)
def _restore_deep_dive_if_needed():
    """Placeholder for potential deep-dive feature restoration"""
    if False:  # Disabled - using orchestrator
        is_deep_dive_consent = _is_deep_dive_consent(question)
@app.post("/chat/enhanced", response_model=ChatResponse)
async def enhanced_chat_endpoint(request: QueryRequest):
    """
    Enhanced chat endpoint with durable workflow features.
    """
    try:
        question = request.question.strip()
        user_id = (request.user_id or "anonymous").strip() or "anonymous"
        session_id = await chat_service.ensure_session(request.session_id, user_id)
        chat_history_store.ensure_session(user_id, session_id)
        
        print(f"🤖 Enhanced processing query: {question}")
        
        # Get enhanced conversation memory
        enhanced_session = enhanced_memory_manager.get_session(session_id, user_id)
        
        # Add user message with enhanced tracking
        await enhanced_session.add_message(
            role="user",
            content=question,
            metadata={"endpoint": "enhanced", "timestamp": datetime.now().isoformat()}
        )
        try:
            user_messages_snapshot = [msg.to_dict() for msg in enhanced_session.messages]
            chat_history_store.sync_session(user_id, session_id, user_messages_snapshot)
        except Exception as exc:
            print(f"⚠️ Failed to sync enhanced chat history after user message for session {session_id}: {exc}")
        
        snippets: List[Dict[str, Any]] = []

        # Use the conversational chat service to process the query with full context
        print("🚀 Using conversational chat service for enhanced query processing")
        try:
            ai_message = None
            async for generated in chat_service.send_message(session_id, question, user_id):
                ai_message = generated

            if not ai_message:
                raise RuntimeError("Chat service returned no response")

            answer = ai_message.content
            session_id = ai_message.session_id
            print(f"🔍 Final answer: {answer}")
        except Exception as router_error:
            print(f"❌ Chat service error: {router_error}")
            return ChatResponse(
                answer=f"Query processing failed: {str(router_error)}. Check input syntax or system status.",
                snippets=[],
                citations=[],
                error=True
            )
        
        # Extract snippets from the answer if available
        try:
            temp_snippets = retrieve_snippets(question, top_k=50, filters={})
            if temp_snippets:
                snippets = temp_snippets
        except Exception as e:
            print(f"Warning: Could not retrieve snippets: {e}")
        
        # Add assistant response with enhanced tracking
        await enhanced_session.add_message(
            role="assistant",
            content=answer,
            metadata={
                "endpoint": "enhanced",
                "snippets_count": len(snippets),
                "citations_count": 0,
                "timestamp": datetime.now().isoformat()
            }
        )
        try:
            enhanced_messages = [msg.to_dict() for msg in enhanced_session.messages]
            chat_history_store.sync_session(user_id, session_id, enhanced_messages)
        except Exception as exc:
            print(f"⚠️ Failed to sync enhanced chat history for session {session_id}: {exc}")
        
        print(f"✅ Enhanced query processed successfully. Answer length: {len(answer)} chars")
        
        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=[]
        )
        
    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred in enhanced chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred while processing your query.")

@app.post("/structured", response_model=StructuredResponse)
async def structured_endpoint(request: StructuredRequest = Body(...)):
    try:
        result = run_sql_query(request.question)
        return StructuredResponse(answer=str(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structured query error: {e}")

@app.post("/chat/clear")
async def clear_chat_history(session_id: str = "default", user_id: str = "anonymous"):
    """Clear chat history for a session."""
    try:
        normalized_user = (user_id or "anonymous").strip() or "anonymous"
        chat_memory.clear_session(session_id)
        chat_history_store.delete_session(normalized_user, session_id)
        return {"message": f"Chat history cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")

@app.get("/chat/history")
async def get_chat_history(session_id: str = "default", user_id: str = "anonymous"):
    """Get chat history for a session."""
    try:
        normalized_user = (user_id or "anonymous").strip() or "anonymous"
        messages = chat_history_store.get_transcript(normalized_user, session_id)
        if not messages:
            messages = chat_memory.get_messages(session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "user_id": normalized_user, "messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")


@app.get("/chat/history/sessions")
async def list_chat_sessions(user_id: str = Query("anonymous")):
    """List chat sessions for a user ordered by recency."""
    try:
        normalized_user = (user_id or "anonymous").strip() or "anonymous"
        records = chat_history_store.list_sessions(normalized_user)
        sessions = [
            {
                "session_id": record.session_id,
                "title": record.title,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "message_count": record.message_count,
                "last_message_preview": record.last_message_preview,
                "summary": record.summary,
            }
            for record in records
        ]
        return {"user_id": normalized_user, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chat sessions: {str(e)}")


@app.get("/chat/history/{session_id}/transcript")
async def get_chat_transcript(session_id: str, user_id: str = Query("anonymous")):
    """Get the persisted transcript for a specific session."""
    normalized_user = (user_id or "anonymous").strip() or "anonymous"
    try:
        messages = chat_history_store.get_transcript(normalized_user, session_id)
        if not messages:
            messages = chat_memory.get_messages(session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "user_id": normalized_user, "messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat transcript: {str(e)}")

# Chat Service Session Management Endpoints
@app.get("/sessions/{user_id}")
async def get_user_chat_sessions(user_id: str):
    """Get all chat sessions for a user"""
    try:
        sessions = await chat_service.get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        success = await chat_service.delete_session(session_id)
        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        print(f"❌ Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/messages")
async def get_chat_session_messages(session_id: str):
    """Get all messages for a specific session"""
    try:
        messages = await chat_service.get_session_messages(session_id)
        return {"messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "sender": msg.sender,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]}
    except Exception as e:
        print(f"❌ Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoints for backward compatibility
@app.get("/companies")
async def get_companies():
    """Get all companies from the database."""
    try:
        db = PlacementDatabase()
        companies = db.get_companies()
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")


@app.get("/api/companies")
async def get_api_companies(limit: int = Query(100)):
    """Get limited list of companies for autocomplete/popup (id, name only)."""
    print(f"🔍 API /companies called with limit: {limit}")
    try:
        db = PlacementDatabase()
        all_companies = db.get_companies()
        limited_companies = all_companies[:limit]
        response_data = [{"id": c["id"], "name": c["company_name"]} for c in limited_companies]
        print(f"✅ /api/companies returning {len(response_data)} companies")
        return response_data
    except Exception as e:
        print(f"❌ Error in /api/companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")

@app.get("/role-types")
async def get_role_types():
    """Get all distinct role types from the database for role selector."""
    try:
        db = PlacementDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT role_types
                FROM roles
                WHERE role_types IS NOT NULL AND role_types != ''
            """)
            
            # Parse JSON role_types and collect unique types
            role_types_set = set()
            for (role_types_json,) in cursor.fetchall():
                try:
                    if role_types_json:
                        role_types_list = json.loads(role_types_json)
                        if isinstance(role_types_list, list):
                            for role_type in role_types_list:
                                if isinstance(role_type, str) and role_type.strip():
                                    role_types_set.add(role_type.strip())
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            # Sort and return
            sorted_role_types = sorted(list(role_types_set))
            return {"role_types": sorted_role_types}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving role types: {str(e)}")

@app.get("/companies/{specialization}")
async def get_companies_by_specialization(specialization: str, year: Optional[str] = None):
    """Get companies by specialization and optionally by year."""
    try:
        db = PlacementDatabase()
        companies = db.get_companies_by_specialization(specialization, year)
        return {
            "specialization": specialization,
            "year": year,
            "companies": companies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


def _execute_deep_dive_search(question: str) -> str:
    """Execute deep-dive search using unstructured database."""
    try:
        print("🎯 Executing deep-dive mode search")
        # Force unstructured search by retrieving and synthesizing from vector DB
        # Increase retrieval for comprehensive analysis across all PDFs
        snippets = retrieve_snippets(question, top_k=150, filters={})
        if snippets:
            answer = synthesize_answer(question, snippets, {})
            if answer:
                return f"🎯 **DEEP-DIVE ANALYSIS COMPLETE**\n\n{answer}\n\n*Analysis based on comprehensive search through job descriptions and company profiles.*"
        
        return "I couldn't find relevant information in the detailed job descriptions for your query. Please try a different question or check the spelling."
    except Exception as e:
        return f"Deep-dive analysis encountered an error: {str(e)}. Please try again."

@app.get("/stats")
async def get_placement_stats(year: Optional[str] = None):
    """Get placement statistics."""
    try:
        db = PlacementDatabase()
        stats = db.get_placement_stats(year)
        return {"year": year, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

def _is_deep_dive_consent(user_input: str) -> bool:
    """Check if user is giving consent for deep-dive mode."""
    consent_keywords = [
        "yes", "deep-dive", "deep dive", "proceed", "activate",
        "go ahead", "search", "unstructured", "detailed", "comprehensive"
    ]
    input_lower = user_input.lower().strip()
    return any(keyword in input_lower for keyword in consent_keywords) and len(input_lower) < 50

def _is_simple_query(question: str) -> bool:
    """Check if query is simple enough to bypass complex workflow."""
    q = question.lower().strip()

    # Simple factual queries that can be handled by direct routing
    simple_patterns = [
        r'how many companies', r'which companies', r'list companies',
        r'what companies', r'companies for', r'companies in',
        r'total companies', r'count companies', r'number of companies',
        r'salary', r'salaries', r'pay', r'package', r'ctc',
        r'skills', r'top skills', r'most demanded skills',
        r'roles', r'positions', r'jobs'
    ]

    # Check for simple patterns
    for pattern in simple_patterns:
        if pattern in q:
            return True

    # Check for hashtag-based queries (simple specialization queries)
    if re.search(r'#\w+', q):
        return True

    # Check for very short queries (likely simple)
    if len(q.split()) <= 6:
        return True

    return False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

SPARK_UI_DIST = (Path(__file__).resolve().parent.parent / "spark-home-2" / "dist" / "spa").resolve()
SPARK_INDEX_FILE = SPARK_UI_DIST / "index.html"

if SPARK_INDEX_FILE.exists():
    assets_dir = SPARK_UI_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="spark-ui-assets")

    @app.get("/", include_in_schema=False)
    async def serve_root() -> FileResponse:
        return FileResponse(SPARK_INDEX_FILE)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        candidate = (SPARK_UI_DIST / full_path).resolve()
        try:
            candidate.relative_to(SPARK_UI_DIST)
        except ValueError:
            return FileResponse(SPARK_INDEX_FILE)

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(SPARK_INDEX_FILE)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


