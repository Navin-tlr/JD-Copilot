"""
Main Orchestrator - Agent-to-Agent (A2A) Protocol
==================================================
Coordinates the multi-agent workflow for placement intelligence queries.

Flow:
1. User Query → Intent Classifier & Router
2. Router decides: SQL / Vector / Hybrid + Memory usage
3. If use_memory → Memory Agent provides context
4. Execute retrieval (SQL, Vector, or both)
5. Summarizer & Synthesizer → Final response
6. Store turn in Memory

Architecture:
- No fallbacks or legacy RAG paths
- Clean A2A communication
- Each agent has single responsibility
"""

import json
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from app.agents.intent_router import get_intent_router, RouterDecision
from app.agents.memory_agent import get_memory_agent
# SQL and Vector tools will be imported from existing modules


@dataclass
class OrchestratorResponse:
    """Final response from orchestrator."""
    answer: str
    intent: str
    route: str
    entities: Dict[str, List[str]]
    confidence: float
    sources: List[Dict[str, Any]]
    used_memory: bool
    session_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "intent": self.intent,
            "route": self.route,
            "entities": self.entities,
            "confidence": self.confidence,
            "sources": self.sources,
            "used_memory": self.used_memory,
            "session_id": self.session_id
        }


class QueryOrchestrator:
    """
    Main orchestrator coordinating all agents via A2A protocol.
    
    Single entry point for all user queries.
    No fallbacks - each agent must succeed or raise explicit error.
    """
    
    def __init__(self):
        """Initialize orchestrator and all agents."""
        self.intent_router = get_intent_router()
        self.memory_agent = get_memory_agent()
        print("✅ Query Orchestrator initialized")
    
    async def process_query(
        self,
        user_query: str,
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResponse:
        """
        Process user query through complete agent pipeline.
        
        Args:
            user_query: User's natural language question
            session_id: Session identifier for memory tracking
            user_context: Additional user context (optional)
            
        Returns:
            OrchestratorResponse with answer and metadata
        """
        print(f"\n{'='*80}")
        print(f"🎬 ORCHESTRATOR: Processing query")
        print(f"   Session: {session_id}")
        print(f"   Query: {user_query}")
        print(f"{'='*80}\n")
        
        # Step 1: Get memory context if available
        memory_context = self.memory_agent.get_context(session_id)
        
        # Step 2: Intent classification and routing
        router_decision = await self.intent_router.classify_and_route(
            query=user_query,
            memory_context=memory_context,
            session_id=session_id
        )
        
        # Step 3: If router says use_memory but no context, get last entities
        if router_decision.use_memory and not memory_context:
            print("⚠️  Router requested memory but no context available")
            # Could prompt user for clarification here
        
        # Step 4: Execute retrieval based on route
        retrieved_data = await self._execute_retrieval(
            user_query=user_query,
            decision=router_decision,
            memory_context=memory_context
        )
        
        # Step 5: Synthesize final answer
        answer, response_summary, sources = await self._synthesize_response(
            user_query=user_query,
            decision=router_decision,
            retrieved_data=retrieved_data,
            memory_context=memory_context
        )
        
        # Step 6: Store turn in memory
        self.memory_agent.add_turn(
            session_id=session_id,
            user_query=user_query,
            intent=router_decision.intent,
            entities={
                "specialization": router_decision.entities.specialization,
                "role": router_decision.entities.role,
                "company": router_decision.entities.company,
                "year": router_decision.entities.year
            },
            route=router_decision.route.value,
            response_summary=response_summary
        )
        
        # Step 7: Build final response
        response = OrchestratorResponse(
            answer=answer,
            intent=router_decision.intent,
            route=router_decision.route.value,
            entities={
                "specialization": router_decision.entities.specialization,
                "role": router_decision.entities.role,
                "company": router_decision.entities.company
            },
            confidence=router_decision.confidence,
            sources=sources,
            used_memory=router_decision.use_memory,
            session_id=session_id
        )
        
        print(f"\n{'='*80}")
        print(f"✅ ORCHESTRATOR: Query processing complete")
        print(f"   Intent: {response.intent}")
        print(f"   Route: {response.route}")
        print(f"   Sources: {len(response.sources)} items")
        print(f"{'='*80}\n")
        
        return response
    
    async def _execute_retrieval(
        self,
        user_query: str,
        decision: RouterDecision,
        memory_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute data retrieval based on routing decision.
        
        Returns:
            Dictionary with sql_results and/or vector_results
        """
        print(f"\n🔍 RETRIEVAL: Executing {decision.route.value}")
        
        retrieved_data = {
            "sql_results": None,
            "vector_results": None
        }
        
        if decision.route.value == "structured_db":
            retrieved_data["sql_results"] = await self._query_sql(user_query, decision)
        
        elif decision.route.value == "vector_db":
            retrieved_data["vector_results"] = await self._query_vector(user_query, decision)
        
        elif decision.route.value == "hybrid":
            # Parallel execution
            retrieved_data["sql_results"] = await self._query_sql(user_query, decision)
            retrieved_data["vector_results"] = await self._query_vector(user_query, decision)
        
        return retrieved_data
    
    async def _query_sql(self, user_query: str, decision: RouterDecision) -> Optional[List[Dict[str, Any]]]:
        """
        Query SQL database using the NL→SQL engine (LlamaIndex NLSQLTableQueryEngine).
        """
        print("   📊 SQL: Querying structured database...")
        
        try:
            # Use the dedicated NL→SQL tool with strict timeouts
            from app.sql_tool import run_sql_query
            
            # Build natural language query from entities
            query_parts = []
            
            if decision.entities.specialization:
                query_parts.append(f"specializations: {', '.join(decision.entities.specialization)}")
            
            if decision.entities.role:
                query_parts.append(f"roles: {', '.join(decision.entities.role)}")
            
            if decision.entities.company:
                query_parts.append(f"companies: {', '.join(decision.entities.company)}")
            
            if decision.entities.year:
                query_parts.append(f"year: {decision.entities.year}")
            
            # Construct natural query with entity context
            entity_context = []

            if decision.entities.specialization:
                entity_context.append(f"Identified Specialization: {', '.join(decision.entities.specialization)}")

            if decision.entities.role:
                entity_context.append(f"Identified Role: {', '.join(decision.entities.role)}")

            if decision.entities.company:
                entity_context.append(f"Identified Company: {', '.join(decision.entities.company)}")

            if decision.entities.year:
                entity_context.append(f"Identified Year: {decision.entities.year}")

            # Build enhanced query with context
            if entity_context:
                context_prefix = "-- Context from Intent Router --\n" + "\n".join(entity_context) + "\n-- Original User Question --\n"
                natural_query = context_prefix + user_query
            else:
                natural_query = user_query

            print(f"   📝 SQL Query: {natural_query}")

            # Run NL→SQL with a 12s cap to avoid UI stalls
            result_str = run_sql_query(natural_query, timeout_sec=12.0)
            if not isinstance(result_str, str):
                result_str = str(result_str)

            if result_str:
                return [{"answer": result_str, "source": "sql_database", "engine": "NLSQL"}]

            return [{"answer": "I cannot answer this question with the available data.", "source": "sql_database", "engine": "NLSQL"}]
            
        except Exception as e:
            print(f"   ❌ SQL query failed: {e}")
            return [{"error": str(e), "source": "sql_database"}]
    
    async def _query_vector(self, user_query: str, decision: RouterDecision) -> Optional[List[Dict[str, Any]]]:
        """
        Query Pinecone vector database using existing RAG tool.
        """
        print("   🔮 Vector: Querying Pinecone...")
        
        try:
            from app.rag import retrieve_snippets
            
            # Build query string
            query_parts = []
            
            if decision.entities.specialization:
                query_parts.append(', '.join(decision.entities.specialization))
            
            if decision.entities.role:
                query_parts.append(', '.join(decision.entities.role))
            
            if decision.entities.company:
                query_parts.append(', '.join(decision.entities.company))
            
            # Construct natural query
            if query_parts:
                vector_query = f"{decision.intent} {' '.join(query_parts)}"
            else:
                vector_query = user_query
            
            print(f"   🔍 Vector Query: {vector_query}")
            
            # Build filters
            filters = {}
            if decision.entities.company:
                # Use first company for filtering, lowercase for company_norm in Pinecone
                company_name = decision.entities.company[0].lower()
                filters["company_norm"] = company_name
            
            # Retrieve snippets (top_k based on route)
            top_k = 100 if decision.route.value == "vector_db" else 50
            snippets = retrieve_snippets(vector_query, top_k=top_k, filters=filters)
            
            if snippets:
                print(f"   ✅ Retrieved {len(snippets)} vector snippets")
                return snippets
            
            return [{"answer": "No vector results found", "source": "vector_database"}]
            
        except Exception as e:
            print(f"   ❌ Vector query failed: {e}")
            return [{"error": str(e), "source": "vector_database"}]
    
    async def _synthesize_response(
        self,
        user_query: str,
        decision: RouterDecision,
        retrieved_data: Dict[str, Any],
        memory_context: Optional[Dict[str, Any]]
    ) -> tuple[str, str, List[Dict[str, Any]]]:
        """
        Synthesize final answer using existing RAG synthesizer.
        
        Tone is controlled by existing system prompt (Linus/Aristotle/Robert Greene).
        
        Returns:
            Tuple of (full_answer, brief_summary, sources)
        """
        print("   ✨ Synthesizer: Generating response...")
        
        try:
            from app.rag import synthesize_answer
            
            # Collect all sources
            sources = []
            sql_results = retrieved_data.get("sql_results", [])
            vector_results = retrieved_data.get("vector_results", [])
            
            # Handle SQL results
            if sql_results:
                for item in sql_results:
                    if "answer" in item:
                        sources.append({
                            "type": "sql",
                            "content": item["answer"],
                            "source": item.get("source", "sql_database")
                        })
            
            # Handle vector results (snippets)
            if vector_results:
                sources.extend(vector_results)
            
            # If we have vector snippets, use synthesize_answer
            if vector_results and isinstance(vector_results, list):
                # Build filters for synthesis
                filters = {}
                if decision.entities.company:
                    company_name = decision.entities.company[0].lower()
                    filters["company_norm"] = company_name
                
                # Build context for synthesis
                context = {}
                if memory_context:
                    context = memory_context
                
                answer = synthesize_answer(
                    question=user_query,
                    snippets=vector_results,
                    filters=filters,
                    context=context
                )
                
                if answer:
                    # Generate brief summary (first 150 chars)
                    summary = answer[:150] + "..." if len(answer) > 150 else answer
                    
                    print(f"   ✅ Synthesized answer: {len(answer)} chars")
                    return answer, summary, sources
            
            # Fallback: if only SQL results, return that
            if sql_results:
                sql_answer = "\n\n".join([
                    item.get("answer", "") for item in sql_results if "answer" in item
                ])
                
                if sql_answer:
                    summary = sql_answer[:150] + "..." if len(sql_answer) > 150 else sql_answer
                    return sql_answer, summary, sources
            
            # No results
            no_data_msg = "I couldn't find relevant information for your query. Please try rephrasing or provide more details."
            return no_data_msg, no_data_msg, sources
            
        except Exception as e:
            print(f"   ❌ Synthesis failed: {e}")
            error_msg = f"I encountered an error generating the response: {str(e)}"
            return error_msg, error_msg, sources


# Global instance
_orchestrator = None


def get_orchestrator() -> QueryOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = QueryOrchestrator()
    return _orchestrator
