from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, List
import re
import sqlite3

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
import json
from datetime import datetime

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer
from .agent import route_query, LAST_ROUTE_TYPE, get_last_timings, _is_no_data_result  # Import router and guardrail utils
from .chat_memory import ChatMemory
from .enhanced_chat_memory import enhanced_memory_manager
from .sql_tool import run_sql_query
from .chat_api import include_chat_router
from .workflow_api import include_workflow_router

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

# Simple LLM router system (no more complex agents)
# The route_query function handles all query processing

def get_jd_agent():
    """This function is no longer needed as we use the simple router."""
    return None

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"

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
        question = request.question.strip()
        chat_memory.add_message(request.session_id, "user", question)
        snippets = retrieve_snippets(question, top_k=25, filters={})
        if snippets:
            answer = synthesize_answer(question, snippets, {}) or "No additional context found."
        else:
            answer = "No document context available for deeper search."\

        chat_memory.add_message(request.session_id, "assistant", answer)
        citations = []
        for snip in snippets or []:
            md = snip.get("metadata", {})
            if md.get("company") or md.get("role"):
                citations.append({
                    "company": md.get("company", ""),
                    "role": md.get("role", ""),
                    "year": md.get("year", ""),
                    "extracted_skills": md.get("extracted_skills", [])
                })
        return ChatResponse(
            answer=answer,
            snippets=snippets or [],
            citations=citations,
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
    print(f"Received query for session '{request.session_id}': {request.query}")
    
    try:
        # Add user message to chat memory
        chat_memory.add_message(request.session_id, "user", request.query)
        
        # Use the simple router to process the query
        print("🚀 Using simple LLM router for query processing")
        try:
            answer = route_query(request.query)
            print(f"🔍 Router answer: {answer}")
            
            if not answer or answer.strip() == "":
                answer = "I couldn't process your query. Please try again."
                
            print(f"🔍 Final answer: {answer}")
        except Exception as router_error:
            print(f"❌ Router error: {router_error}")
            # Return a graceful error response instead of crashing
            return ChatResponse(
                answer=f"Sorry, I encountered an error while processing your query: {str(router_error)}",
                snippets=[],
                citations=[],
                error=True
            )
            
            # Extract snippets from the answer if available
            snippets = []
            try:
                # Try to get relevant snippets for citations
                temp_snippets = retrieve_snippets(request.query, top_k=15, filters={})
                if temp_snippets:
                    snippets = temp_snippets
            except Exception as e:
                print(f"Warning: Could not retrieve snippets for citations: {e}")
            
        else:
            print("⚠️ AI agent not available, falling back to basic RAG")
            # Fallback to basic RAG if agent fails
            snippets = retrieve_snippets(request.query, top_k=15, filters={})
            if snippets:
                answer = synthesize_answer(request.query, snippets, {})
            else:
                answer = "I couldn't find any relevant information to answer your question."
        
        # Add assistant response to chat memory
        chat_memory.add_message(request.session_id, "assistant", answer)
        
        # Prepare citations
        citations = []
        if snippets:
            for snippet in snippets:
                metadata = snippet.get("metadata", {})
                if metadata.get("company") or metadata.get("role") or metadata.get("year"):
                    citations.append({
                        "company": metadata.get("company", ""),
                        "role": metadata.get("role", ""),
                        "year": metadata.get("year", ""),
                        "extracted_skills": metadata.get("extracted_skills", [])
                    })
        
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
            citations=citations,
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
        
        # Return a structured error response instead of raising an exception
        # This ensures the React app always gets valid JSON
        return ChatResponse(
            answer=f"An error occurred while processing your query: {str(e)}",
            snippets=[],
            citations=[],
            error=True  # Add error flag for frontend handling
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: QueryRequest):
    """
    Legacy chat endpoint that maintains backward compatibility.
    """
    try:
        question = request.question.strip()
        session_id = request.session_id
        
        print(f"🤖 Processing query: {question}")
        
        # Add user message to chat memory
        chat_memory.add_message(session_id, "user", question)
        
        # Check if user is consenting to deep-dive mode
        is_deep_dive_consent = _is_deep_dive_consent(question)
        
        if is_deep_dive_consent:
            print("🎯 Deep-dive mode activated by user consent")
            # Get the previous question from chat memory for context
            previous_messages = chat_memory.get_messages(session_id)
            if len(previous_messages) >= 2:  # At least one previous Q&A
                # Get the last user question before consent
                for i in range(len(previous_messages) - 2, -1, -1):
                    message = previous_messages[i]
                    role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
                    if role == "user":
                        original_question = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
                        print(f"🔍 Deep-dive analyzing original query: {original_question}")
                        # Force unstructured search
                        answer = _execute_deep_dive_search(original_question)
                        break
                else:
                    answer = "I need the original question to perform deep-dive analysis. Please ask your question again."
            else:
                answer = "I need the original question to perform deep-dive analysis. Please ask your question again."
        else:
            # Use the simple router to process the query
            print("🚀 Using simple LLM router for query processing")
            try:
                answer = route_query(question)
                print(f"🔍 Router answer: {answer}")
                
                if not answer or answer.strip() == "":
                    answer = "I couldn't process your query. Please try again."
                    
                print(f"🔍 Final answer: {answer}")
            except Exception as router_error:
                print(f"❌ Router error: {router_error}")
                # Return a graceful error response instead of crashing
                return ChatResponse(
                    answer=f"Sorry, I encountered an error while processing your query: {str(router_error)}",
                    snippets=[],
                    citations=[],
                    error=True
                )
        
        # Extract snippets from the answer if available
        snippets = []
        try:
            # Try to get relevant snippets for citations
            temp_snippets = retrieve_snippets(question, top_k=15, filters={})
            if temp_snippets:
                snippets = temp_snippets
        except Exception as e:
            print(f"Warning: Could not retrieve snippets for citations: {e}")
        
        # Prepare citations for the response object (but don't add to answer text)
        citations = []
        if snippets:
            for snippet in snippets:
                metadata = snippet.get("metadata", {})
                if metadata.get("company") or metadata.get("role") or metadata.get("year"):
                    citations.append({
                        "company": metadata.get("company", ""),
                        "role": metadata.get("role", ""),
                        "year": metadata.get("year", ""),
                        "extracted_skills": metadata.get("extracted_skills", [])
                    })
        
        # Add assistant response to chat memory
        chat_memory.add_message(session_id, "assistant", answer)
        
        print(f"✅ Query processed successfully. Answer length: {len(answer)} chars")
        
        lower_ans = answer.lower().strip() if answer else ""
        no_data = _is_no_data_result(answer)
        deep_dive_phrase = "deep-dive mode available" in lower_ans
        deep_dive_analysis = "deep-dive analysis complete" in lower_ans

        deep_dive_offered = False
        deep_dive_consent_needed = False
        needs_vector = False
        reason = None
        deep_dive_mandatory = False

        if LAST_ROUTE_TYPE == "STRUCTURED":
            # Only prompt for deep dive if structured data was insufficient
            if no_data or deep_dive_phrase:
                deep_dive_offered = True
                deep_dive_consent_needed = True and not deep_dive_analysis
                needs_vector = True  # front-end can show consent CTA
                reason = "Structured database returned no direct data. Offer deep-dive search of unstructured job descriptions." 
        # If user already consented, we mark vector_used implicitly in answer content; keep flags off

        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=citations,
            needs_vector_approval=needs_vector,
            vector_reason=reason,
            vector_used=deep_dive_analysis,  # treat analysis completion as vector usage
            performance=get_last_timings(),
            deep_dive_mandatory=deep_dive_mandatory,
            deep_dive_offered=deep_dive_offered,
            deep_dive_consent_needed=deep_dive_consent_needed
        )
        
    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred while processing your query.")


@app.post("/chat/enhanced", response_model=ChatResponse)
async def enhanced_chat_endpoint(request: QueryRequest):
    """
    Enhanced chat endpoint with durable workflow features.
    """
    try:
        question = request.question.strip()
        session_id = request.session_id
        user_id = "anonymous"  # Could be extracted from request headers or auth
        
        print(f"🤖 Enhanced processing query: {question}")
        
        # Get enhanced conversation memory
        enhanced_session = enhanced_memory_manager.get_session(session_id, user_id)
        
        # Add user message with enhanced tracking
        await enhanced_session.add_message(
            role="user",
            content=question,
            metadata={"endpoint": "enhanced", "timestamp": datetime.now().isoformat()}
        )
        
        # Use the simple router to process the query
        print("🚀 Using simple LLM router for enhanced query processing")
        try:
            answer = route_query(question)
            print(f"🔍 Router answer: {answer}")
            
            if not answer or answer.strip() == "":
                answer = "I couldn't process your query. Please try again."
                
            print(f"🔍 Final answer: {answer}")
        except Exception as router_error:
            print(f"❌ Router error: {router_error}")
            # Return a graceful error response instead of crashing
            return ChatResponse(
                answer=f"Sorry, I encountered an error while processing your query: {str(router_error)}",
                snippets=[],
                citations=[],
                error=True
            )
        
        # Extract snippets from the answer if available
        snippets = []
        try:
            # Try to get relevant snippets for citations
            temp_snippets = retrieve_snippets(question, top_k=15, filters={})
            if temp_snippets:
                snippets = temp_snippets
        except Exception as e:
            print(f"Warning: Could not retrieve snippets for citations: {e}")
        
        # Prepare citations for the response object (but don't add to answer text)
        citations = []
        if snippets:
            for snippet in snippets:
                metadata = snippet.get("metadata", {})
                if metadata.get("company") or metadata.get("role") or metadata.get("year"):
                    citations.append({
                        "company": metadata.get("company", ""),
                        "role": metadata.get("role", ""),
                        "year": metadata.get("year", ""),
                        "extracted_skills": metadata.get("extracted_skills", [])
                    })
        
        # Add assistant response with enhanced tracking
        await enhanced_session.add_message(
            role="assistant",
            content=answer,
            metadata={
                "endpoint": "enhanced",
                "snippets_count": len(snippets),
                "citations_count": len(citations),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"✅ Enhanced query processed successfully. Answer length: {len(answer)} chars")
        
        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=citations
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
async def clear_chat_history(session_id: str = "default"):
    """Clear chat history for a session."""
    try:
        chat_memory.clear_session(session_id)
        return {"message": f"Chat history cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")

@app.get("/chat/history")
async def get_chat_history(session_id: str = "default"):
    """Get chat history for a session."""
    try:
        messages = chat_memory.get_messages(session_id)
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

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

def _is_deep_dive_consent(user_input: str) -> bool:
    """Check if user is giving consent for deep-dive mode."""
    consent_keywords = [
        "yes", "deep-dive", "deep dive", "proceed", "activate", 
        "go ahead", "search", "unstructured", "detailed", "comprehensive"
    ]
    input_lower = user_input.lower().strip()
    return any(keyword in input_lower for keyword in consent_keywords) and len(input_lower) < 50

def _execute_deep_dive_search(question: str) -> str:
    """Execute deep-dive search using unstructured database."""
    try:
        print("🎯 Executing deep-dive mode search")
        # Force unstructured search by retrieving and synthesizing from vector DB
        snippets = retrieve_snippets(question, top_k=30, filters={})
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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


