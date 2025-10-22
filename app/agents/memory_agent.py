"""
Memory Agent
============
Short-term conversational memory for context continuity.

Responsibilities:
- Store last 5-6 conversation turns per session
- Provide context for ambiguous queries
- Support query rewriting and entity disambiguation
- Auto-expire after 2 hours TTL
- Never used as sole evidence, only for context

Architecture:
- In-memory storage (can be extended to Redis)
- Session-scoped with rolling window
- Compact summaries after 3 turns
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    timestamp: float
    user_query: str
    intent: str
    entities: Dict[str, Any]
    route: str
    response_summary: str  # Brief summary of response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "user_query": self.user_query,
            "intent": self.intent,
            "entities": self.entities,
            "route": self.route,
            "response_summary": self.response_summary
        }
    
    def is_expired(self, ttl_hours: int = 2) -> bool:
        """Check if turn is expired based on TTL."""
        return time.time() - self.timestamp > (ttl_hours * 3600)


@dataclass
class SessionMemory:
    """Memory for a single session."""
    session_id: str
    turns: List[ConversationTurn]
    created_at: float
    last_accessed: float
    
    def add_turn(self, turn: ConversationTurn):
        """Add a new turn and maintain rolling window."""
        self.turns.append(turn)
        self.last_accessed = time.time()
        
        # Keep only last 6 turns
        if len(self.turns) > 6:
            self.turns = self.turns[-6:]
    
    def get_context(self, max_turns: int = 5) -> List[Dict[str, Any]]:
        """Get recent context for query rewriting."""
        # Remove expired turns
        self.turns = [t for t in self.turns if not t.is_expired()]
        
        # Return last N turns
        recent_turns = self.turns[-max_turns:]
        return [t.to_dict() for t in recent_turns]
    
    def get_last_entities(self) -> Dict[str, Any]:
        """Get entities from the most recent turn."""
        if not self.turns:
            return {}
        return self.turns[-1].entities
    
    def is_expired(self, ttl_hours: int = 2) -> bool:
        """Check if entire session is expired."""
        return time.time() - self.last_accessed > (ttl_hours * 3600)


class MemoryAgent:
    """
    Short-term conversational memory agent.
    
    Stores last 5-6 turns per session for context continuity.
    Used only for disambiguation and query rewriting, never as sole evidence.
    """
    
    def __init__(self, ttl_hours: int = 2, max_turns: int = 6):
        """
        Initialize Memory Agent.
        
        Args:
            ttl_hours: Time-to-live for sessions in hours
            max_turns: Maximum turns to store per session
        """
        self.ttl_hours = ttl_hours
        self.max_turns = max_turns
        self.sessions: Dict[str, SessionMemory] = {}
        print(f"✅ Memory Agent initialized (TTL: {ttl_hours}h, Max turns: {max_turns})")
    
    def add_turn(
        self,
        session_id: str,
        user_query: str,
        intent: str,
        entities: Dict[str, Any],
        route: str,
        response_summary: str
    ):
        """
        Add a conversation turn to memory.
        
        Args:
            session_id: Unique session identifier
            user_query: User's original query
            intent: Detected intent from router
            entities: Extracted entities from router
            route: Route taken (structured_db, vector_db, hybrid)
            response_summary: Brief summary of the response
        """
        # Clean expired sessions first
        self._clean_expired_sessions()
        
        # Create or get session
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(
                session_id=session_id,
                turns=[],
                created_at=time.time(),
                last_accessed=time.time()
            )
        
        # Add turn
        turn = ConversationTurn(
            timestamp=time.time(),
            user_query=user_query,
            intent=intent,
            entities=entities,
            route=route,
            response_summary=response_summary
        )
        
        self.sessions[session_id].add_turn(turn)
        print(f"💾 Memory: Added turn to session {session_id} (total: {len(self.sessions[session_id].turns)})")
    
    def get_context(self, session_id: str, max_turns: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session to retrieve context for
            max_turns: Maximum number of recent turns to return
            
        Returns:
            Dictionary with recent conversation context or None if no context
        """
        self._clean_expired_sessions()
        
        if session_id not in self.sessions:
            print(f"ℹ️  Memory: No context found for session {session_id}")
            return None
        
        session = self.sessions[session_id]
        context_turns = session.get_context(max_turns)
        
        if not context_turns:
            print(f"ℹ️  Memory: No valid turns for session {session_id}")
            return None
        
        context = {
            "session_id": session_id,
            "turn_count": len(context_turns),
            "recent_turns": context_turns,
            "last_entities": session.get_last_entities()
        }
        
        print(f"🧠 Memory: Retrieved {len(context_turns)} turns for session {session_id}")
        return context
    
    def get_last_entities(self, session_id: str) -> Dict[str, Any]:
        """
        Get entities from the most recent turn.
        
        Useful for carrying forward context (e.g., company, specialization).
        """
        if session_id not in self.sessions:
            return {}
        
        return self.sessions[session_id].get_last_entities()
    
    def clear_session(self, session_id: str):
        """Clear memory for a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"🗑️  Memory: Cleared session {session_id}")
    
    def _clean_expired_sessions(self):
        """Remove expired sessions based on TTL."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.ttl_hours)
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        if expired:
            print(f"🧹 Memory: Cleaned {len(expired)} expired sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        self._clean_expired_sessions()
        
        total_turns = sum(len(s.turns) for s in self.sessions.values())
        
        return {
            "active_sessions": len(self.sessions),
            "total_turns": total_turns,
            "avg_turns_per_session": total_turns / len(self.sessions) if self.sessions else 0,
            "ttl_hours": self.ttl_hours,
            "max_turns_per_session": self.max_turns
        }


# Global instance
_memory_agent = None


def get_memory_agent() -> MemoryAgent:
    """Get or create global Memory Agent instance."""
    global _memory_agent
    if _memory_agent is None:
        _memory_agent = MemoryAgent(ttl_hours=2, max_turns=6)
    return _memory_agent
