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
from .agent import create_final_agent, create_production_agent
from .chat_memory import ChatMemory
from .sql_tool import run_sql_query

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

# Initialize the AI agent when the application starts
# This ensures it's ready to handle requests without delay
jd_agent = None

def get_jd_agent():
    """Get or create the JD agent."""
    global jd_agent
    if jd_agent is None:
        try:
            jd_agent = create_production_agent()
        except Exception as e:
            print(f"Warning: Could not initialize JD agent: {e}")
            jd_agent = None
    return jd_agent

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
async def query_endpoint(request: ChatRequest = Body(...), agent = Depends(get_jd_agent)):
    """
    This endpoint receives a user query and uses the AI agent to generate a response.
    """
    print(f"Received query for session '{request.session_id}': {request.query}")
    
    try:
        # Add user message to chat memory
        chat_memory.add_message(request.session_id, "user", request.query)
        
        if agent:
            print("🚀 Using AI agent for intelligent query processing")
            # The main logic is now a single call to the agent executor
            response = agent.invoke({
                "input": request.query,
                # If you implement memory, you'll pass chat_history here
            })
            
            answer = response.get("output", "I couldn't process your query. Please try again.")
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
        
        return QueryResponse(answer=answer, sources=[])  # You can enhance this to return sources later

    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred while processing your query.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: QueryRequest, agent = Depends(get_jd_agent)):
    """
    Legacy chat endpoint that maintains backward compatibility.
    """
    try:
        question = request.question.strip()
        session_id = request.session_id
        
        print(f"🤖 Processing query: {question}")
        
        # Add user message to chat memory
        chat_memory.add_message(session_id, "user", question)
        
        # Use the AI agent to process the query
        if agent:
            print("🚀 Using AI agent for intelligent query processing")
            try:
                response = agent.invoke({
                    "input": question,
                })
                answer = response.get("output", "I couldn't process your query. Please try again.")
            except Exception as agent_error:
                print(f"❌ Agent execution error: {agent_error}")
                # Return a graceful error response instead of crashing
                return ChatResponse(
                    answer=f"Sorry, I encountered an error while processing your query: {str(agent_error)}",
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
            
        else:
            print("⚠️ AI agent not available, falling back to basic RAG")
            # Fallback to basic RAG if agent fails
            snippets = retrieve_snippets(question, top_k=8, filters={})
            if snippets:
                answer = synthesize_answer(question, snippets, {})
            else:
                answer = "I couldn't find any relevant information to answer your question."
        
        # Add assistant response to chat memory
        chat_memory.add_message(session_id, "assistant", answer)
        
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
        # This ensures the Flutter app always gets valid JSON
        return ChatResponse(
            answer=f"An error occurred while processing your query: {str(e)}",
            snippets=[],
            citations=[],
            error=True  # Add error flag for frontend handling
        )

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


