"""
Advanced Query Router for Multi-Hop Queries
Handles complex queries requiring sequential reasoning across structured and unstructured data.
"""

import re
from typing import Dict, List, Any, Optional
import sqlite3

from .config import get_settings
from .rag import retrieve_snippets, synthesize_answer
from .final_sql_tool import run_llama_index_sql_query


class QueryRouter:
    """Advanced router for multi-hop queries with sequential reasoning."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def route_query(self, question: str) -> str:
        """
        Handle multi-hop queries using pure LlamaIndex without hardcoded logic.
        """
        print(f"🔍 Multi-hop query processing with pure LlamaIndex: '{question}'")

        try:
            # Use LlamaIndex directly for multi-hop queries
            result = run_llama_index_sql_query(question)
            if result and not result.startswith("Structured query engine not available"):
                return self._format_multi_hop_response(result, question)
            else:
                # Fallback to RAG for complex queries
                return self._rag_fallback_multi_hop(question)

        except Exception as e:
            print(f"❌ Multi-hop query error: {e}")
            return self._safe_fallback_response(question)
    
    def _format_multi_hop_response(self, raw_result: str, original_question: str) -> str:
        """Format LlamaIndex results for multi-hop queries."""
        if not raw_result or raw_result.startswith("Error"):
            return self._rag_fallback_multi_hop(original_question)

        # Add context and formatting for multi-hop responses
        formatted_response = f"MULTI-HOP ANALYSIS RESULTS\n\n"
        formatted_response += f"Query: {original_question}\n\n"
        formatted_response += f"Analysis Results:\n{raw_result}\n\n"

        # Add safety disclaimer
        formatted_response += "Note: This analysis is based on our placement database. "
        formatted_response += "For personalized career advice, please consult with placement counselors."

        return formatted_response

    def _rag_fallback_multi_hop(self, question: str) -> str:
        """Fallback to RAG for complex multi-hop queries when LlamaIndex fails."""
        try:
            snippets = retrieve_snippets(question, top_k=5, filters={})
            if snippets:
                rag_result = synthesize_answer(question, snippets, {})
                if rag_result:
                    return f"Based on available placement information:\n\n{rag_result}\n\n" \
                           "Note: This is general guidance based on our database. " \
                           "Please consult placement counselors for personalized advice."
        except Exception as e:
            print(f"❌ RAG fallback failed: {e}")

        return "I need to process this complex query through multiple data sources. " \
               "Please try rephrasing or ask about specific companies or roles separately."
    
    # Removed hardcoded query handlers - using pure LlamaIndex approach
    
    # Removed hardcoded company extraction - LlamaIndex handles entity recognition

    # Removed hardcoded role extraction and preparation logic - LlamaIndex handles this

    # Removed hardcoded query handlers - using pure LlamaIndex approach

    # Removed all hardcoded comparison and skill analysis logic - LlamaIndex handles this

    # Removed all hardcoded company analysis and advice generation - LlamaIndex handles this
    
    def _safe_fallback_response(self, question: str) -> str:
        """Safe fallback when multi-hop processing fails."""
        print(f"⚠️ Multi-hop fallback for: {question}")
        
        # Try hybrid approach as fallback
        try:
            result = run_llama_index_sql_query(question)
            if result and not result.startswith("Structured query engine not available"):
                return f"Based on our analysis:\n\n{result}"
        except Exception:
            pass
        
        # Final fallback
        return "I need to process this complex query through multiple data sources. " \
               "Please try rephrasing or ask about specific companies or roles separately."


# Global instance for easy access
query_router = QueryRouter()
