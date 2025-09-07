from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, List
import re

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
from .agent import route_query  # Import the simple router instead of agent functions
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
    error: Optional[bool] = False  # Add error flag for frontend error handling

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []

class StructuredRequest(BaseModel):
    question: str

class StructuredResponse(BaseModel):
    answer: str

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
                temp_snippets = retrieve_snippets(request.query, top_k=3, filters={})
                if temp_snippets:
                    snippets = temp_snippets
            except Exception as e:
                print(f"Warning: Could not retrieve snippets for citations: {e}")
            
        else:
            print("⚠️ AI agent not available, falling back to basic RAG")
            # Fallback to basic RAG if agent fails
            snippets = retrieve_snippets(request.query, top_k=8, filters={})
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
        
        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=citations
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
            temp_snippets = retrieve_snippets(question, top_k=3, filters={})
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
        
        return ChatResponse(
            answer=answer,
            snippets=snippets,
            citations=citations
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
            temp_snippets = retrieve_snippets(question, top_k=3, filters={})
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


